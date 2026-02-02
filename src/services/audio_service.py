"""
Audio Transcription Service
实时音频转写服务，提供 Partial 和 Accurate 两种字幕输出
"""
import os
import sys
import time
import queue
import threading
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Deque, Callable
from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from src.config import (
    VAD_DIR, MODEL_DIR_FINAL, MODEL_DIR_PARTIAL,
    SR, CHANNELS, BLOCK_MS, BLOCK_SAMPLES,
    AUDIO_Q_MAX, UTT_Q_MAX,
    VAD_THRESHOLD, MIN_SPEECH_MS, MIN_SILENCE_MS, MAX_UTT_S,
    PADDING_MS, PADDING_SAMPLES, END_TAIL_MS,
    LANGUAGE, BEAM_SIZE, TEMPERATURE, PATIENCE, COMPUTE_TYPE_FINAL,
    PARTIAL_UPDATE_MS, PARTIAL_MIN_SEC, PARTIAL_TAIL_SEC,
    PARTIAL_BEAM_SIZE, PARTIAL_PATIENCE, STABLE_HYPS,
    COMMITTED_PROMPT_WORDS, PREV_SENT_TAIL_CHARS,
    COMPUTE_TYPE_PARTIAL, MIN_CHARS_TO_PRINT,
    MAX_NO_SPEECH_PROB, MIN_AVG_LOGPROB, DEFAULT_PROF_WORDS,
    OUT_TXT, DEVICE
)


# ====== 数据结构 ======
@dataclass
class State:
    """VAD 状态"""
    in_speech: bool = False
    speech_ms: int = 0
    silence_ms: int = 0
    utt_ms: int = 0


@dataclass
class UTTEvent:
    """语音事件"""
    kind: str  # "START" | "CHUNK" | "END"
    audio: Optional[np.ndarray] = None  # float32 1D
    t: float = 0.0


@dataclass
class CaptionOutput:
    """字幕输出"""
    type: str  # "partial" | "accurate"
    text: str
    timestamp: str
    no_speech_prob: Optional[float] = None
    avg_logprob: Optional[float] = None


# ====== 工具函数 ======
def int16_to_float32(x: np.ndarray) -> np.ndarray:
    """将 int16 音频转为 float32"""
    return (x.astype(np.float32)) / 32768.0


def safe_put_drop_oldest(q: queue.Queue, item):
    """安全放入队列，队列满时丢弃最老的项"""
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass


def load_silero_vad_local(vad_dir: str):
    """加载本地 Silero VAD 模型"""
    vad_dir = os.path.abspath(vad_dir)
    if not os.path.isdir(vad_dir):
        raise FileNotFoundError(f"VAD_DIR not found: {vad_dir}")

    sys.path.insert(0, vad_dir)

    try:
        from silero_vad import load_silero_vad
        model = load_silero_vad()
        return model
    except Exception:
        pass

    import torch
    model, _ = torch.hub.load(repo_or_dir=vad_dir, model="silero_vad", source="local")
    return model


def words_split(s: str) -> List[str]:
    """分词"""
    return [w for w in s.strip().split() if w]


def lcp_wordlist(lists: List[List[str]]) -> List[str]:
    """计算多个词列表的最长公共前缀"""
    if not lists:
        return []
    min_len = min(len(x) for x in lists)
    out: List[str] = []
    for i in range(min_len):
        w0 = lists[0][i]
        if all(x[i] == w0 for x in lists[1:]):
            out.append(w0)
        else:
            break
    return out


def merge_with_overlap(committed: List[str], tail: List[str], max_check: int = 50) -> List[str]:
    """合并两个词列表，处理重叠"""
    if not committed:
        return tail
    if not tail:
        return committed

    max_k = min(len(committed), len(tail), max_check)
    for k in range(max_k, 0, -1):
        if committed[-k:] == tail[:k]:
            return committed + tail[k:]
    return committed + tail


def setup_logger(name: str, log_file: str) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 清除已有的 handlers
    logger.handlers.clear()

    # 文件 handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def format_subtitle_line(stable_words: List[str], unstable_words: List[str]) -> str:
    """格式化字幕行"""
    stable = " ".join(stable_words).strip()
    unstable = " ".join(unstable_words).strip()
    if stable and unstable:
        return f"{stable}  [{unstable}]"
    if stable:
        return stable
    if unstable:
        return f"[{unstable}]"
    return ""


def transcribe_once(
    model: WhisperModel,
    audio: np.ndarray,
    *,
    language: str,
    beam_size: int,
    temperature: float,
    patience: float,
    initial_prompt: str,
    condition_on_previous_text: bool,
    vad_filter: bool,
):
    """单次转写"""
    segments, info = model.transcribe(
        audio,
        language=language,
        beam_size=beam_size,
        temperature=temperature,
        patience=patience,
        vad_filter=vad_filter,
        condition_on_previous_text=condition_on_previous_text,
        initial_prompt=initial_prompt,
    )
    text = "".join([s.text for s in segments]).strip()
    return text, info


# ====== 主服务类 ======
class AudioTranscriptionService:
    """
    音频转写服务
    提供实时的 partial 字幕和准确的 accurate 字幕
    """

    def __init__(self):
        """初始化服务"""
        self.vad_model = None
        self.partial_model = None
        self.final_model = None

        # 队列
        self.audio_q = queue.Queue(maxsize=AUDIO_Q_MAX)
        self.evt_q = queue.Queue(maxsize=UTT_Q_MAX)

        # 输出队列（外部消费）
        self.partial_output_q = queue.Queue(maxsize=100)  # partial 字幕
        self.accurate_output_q = queue.Queue(maxsize=100)  # accurate 字幕

        # 控制
        self.stop_event = threading.Event()
        self.is_running = False

        # 线程
        self.vad_thread = None
        self.transcriber_thread = None
        self.audio_stream = None

        # 回调
        self.partial_callback: Optional[Callable[[CaptionOutput], None]] = None
        self.accurate_callback: Optional[Callable[[CaptionOutput], None]] = None

        # 日志
        self.logger = setup_logger('AudioService', 'logs/audio_service.log')
        self.vad_logger = setup_logger('VAD', 'logs/vad.log')
        self.transcriber_logger = setup_logger('Transcriber', 'logs/transcriber.log')

        # 动态专业词汇提示词
        self.dynamic_prof_words: Optional[str] = None

    def initialize(self):
        """初始化模型（耗时操作，建议在启动时调用）"""
        print("Loading VAD model...")
        self.vad_model = load_silero_vad_local(VAD_DIR)
        try:
            self.vad_model.eval()
        except Exception:
            pass

        print("Loading Whisper Partial model...")
        self.partial_model = WhisperModel(
            MODEL_DIR_PARTIAL,
            device=DEVICE,
            compute_type=COMPUTE_TYPE_PARTIAL,
        )

        print("Loading Whisper Final model...")
        self.final_model = WhisperModel(
            MODEL_DIR_FINAL,
            device=DEVICE,
            compute_type=COMPUTE_TYPE_FINAL,
        )
        print("All models loaded successfully!")

    def set_partial_callback(self, callback: Callable[[CaptionOutput], None]):
        """设置 partial 字幕回调"""
        self.partial_callback = callback

    def set_accurate_callback(self, callback: Callable[[CaptionOutput], None]):
        """设置 accurate 字幕回调"""
        self.accurate_callback = callback

    def set_prof_words(self, prof_words: str):
        """设置动态生成的专业词汇提示词"""
        self.dynamic_prof_words = prof_words
        self.logger.info(f"Prof words updated (length: {len(prof_words)} chars)")

    def start_capture(self):
        """启动音频捕获和转写"""
        if self.is_running:
            self.logger.warning("Service is already running!")
            print("Service is already running!")
            return

        if self.vad_model is None or self.partial_model is None or self.final_model is None:
            raise RuntimeError("Models not initialized. Call initialize() first.")

        self.logger.info("Starting audio capture service...")

        self.stop_event.clear()
        self.is_running = True

        # 启动 VAD 线程
        self.vad_thread = threading.Thread(
            target=self._vad_segmenter,
            daemon=True
        )
        self.vad_thread.start()
        self.logger.info("VAD thread started")

        # 启动转写线程
        self.transcriber_thread = threading.Thread(
            target=self._transcriber,
            daemon=True
        )
        self.transcriber_thread.start()
        self.logger.info("Transcriber thread started")

        # 启动音频流
        def audio_callback(indata, frames, time_info, status):
            if frames <= 0:
                return
            block = indata[:, 0].copy()
            safe_put_drop_oldest(self.audio_q, block)

        self.audio_stream = sd.InputStream(
            samplerate=SR,
            channels=CHANNELS,
            dtype="int16",
            blocksize=BLOCK_SAMPLES,
            callback=audio_callback,
        )
        self.audio_stream.start()
        self.logger.info("Audio stream started")

        print("Audio capture started!")

    def stop_capture(self):
        """停止音频捕获和转写"""
        if not self.is_running:
            return

        self.logger.info("Stopping audio capture service...")
        print("Stopping audio capture...")
        self.stop_event.set()

        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            self.logger.info("Audio stream stopped")

        time.sleep(0.3)
        self.is_running = False
        self.logger.info("Audio capture service stopped")
        print("Audio capture stopped!")

    def get_partial_caption(self, block=True, timeout=None):
        """获取 partial 字幕（从队列）"""
        return self.partial_output_q.get(block=block, timeout=timeout)

    def get_accurate_caption(self, block=True, timeout=None):
        """获取 accurate 字幕（从队列）"""
        return self.accurate_output_q.get(block=block, timeout=timeout)

    def _vad_segmenter(self):
        """VAD 分段器（在后台线程运行）"""
        import torch

        block_ms = int(1000 * BLOCK_SAMPLES / SR)
        pre_cache_blocks = max(1, PADDING_SAMPLES // BLOCK_SAMPLES)
        end_tail_blocks = max(1, int(END_TAIL_MS / block_ms))

        st = State()
        pre_cache: List[np.ndarray] = []
        tail_silence_kept = 0

        while not self.stop_event.is_set():
            try:
                try:
                    block_i16 = self.audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                block_f32 = int16_to_float32(block_i16)

                pre_cache.append(block_f32)
                if len(pre_cache) > pre_cache_blocks:
                    pre_cache.pop(0)

                x = torch.from_numpy(block_f32)
                with torch.no_grad():
                    prob = self.vad_model(x, SR)
                    speech_prob = float(prob.item()) if hasattr(prob, "item") else float(prob)

                is_speech = speech_prob >= VAD_THRESHOLD

                if not st.in_speech:
                    if is_speech:
                        st.speech_ms += block_ms
                        if st.speech_ms >= MIN_SPEECH_MS:
                            st.in_speech = True
                            st.silence_ms = 0
                            st.utt_ms = 0
                            tail_silence_kept = 0

                            start_audio = np.concatenate(pre_cache, axis=0) if pre_cache else None
                            safe_put_drop_oldest(self.evt_q, UTTEvent(kind="START", audio=start_audio, t=time.monotonic()))
                            self.vad_logger.info(f"Speech START detected (speech_ms={st.speech_ms})")
                    else:
                        st.speech_ms = 0
                else:
                    st.utt_ms += block_ms

                    if is_speech:
                        st.silence_ms = 0
                        tail_silence_kept = 0
                        safe_put_drop_oldest(self.evt_q, UTTEvent(kind="CHUNK", audio=block_f32, t=time.monotonic()))
                    else:
                        st.silence_ms += block_ms
                        if tail_silence_kept < end_tail_blocks:
                            tail_silence_kept += 1
                            safe_put_drop_oldest(self.evt_q, UTTEvent(kind="CHUNK", audio=block_f32, t=time.monotonic()))

                    end_by_silence = st.silence_ms >= MIN_SILENCE_MS
                    too_long = st.utt_ms >= int(MAX_UTT_S * 1000)

                    if end_by_silence or too_long:
                        reason = "silence" if end_by_silence else "too_long"
                        self.vad_logger.info(f"Speech END detected (reason={reason}, utt_ms={st.utt_ms}, silence_ms={st.silence_ms})")
                        safe_put_drop_oldest(self.evt_q, UTTEvent(kind="END", audio=None, t=time.monotonic()))
                        st = State()
                        pre_cache = []
                        tail_silence_kept = 0

            except Exception as e:
                # 捕获所有异常，防止线程崩溃
                self.vad_logger.error(f"VAD segmenter error: {e}", exc_info=True)
                print(f"ERROR in VAD segmenter: {e}")
                import traceback
                traceback.print_exc()
                # 重置状态，继续运行
                st = State()
                pre_cache = []
                tail_silence_kept = 0
                continue

    def _transcriber(self):
        """转写器（在后台线程运行）"""
        prev_sent_tail = ""
        blocks: List[np.ndarray] = []
        committed_words: List[str] = []
        committed_len = 0
        recent_hyps: Deque[List[str]] = deque(maxlen=STABLE_HYPS)
        last_partial_t = 0.0

        def reset_sentence():
            nonlocal blocks, committed_words, committed_len, recent_hyps, last_partial_t
            blocks = []
            committed_words = []
            committed_len = 0
            recent_hyps = deque(maxlen=STABLE_HYPS)
            last_partial_t = 0.0

        def build_partial_audio_tail() -> np.ndarray:
            if not blocks:
                return np.zeros((0,), dtype=np.float32)
            tail_blocks = int(PARTIAL_TAIL_SEC * SR / BLOCK_SAMPLES)
            tail = blocks[-tail_blocks:] if tail_blocks > 0 else blocks
            return np.concatenate(tail, axis=0) if tail else np.zeros((0,), dtype=np.float32)

        def build_full_audio() -> np.ndarray:
            if not blocks:
                return np.zeros((0,), dtype=np.float32)
            return np.concatenate(blocks, axis=0)

        def build_partial_prompt(committed_words_local: List[str]) -> str:
            # 使用动态生成的 prof_words，如果没有则使用默认的
            prof_words = self.dynamic_prof_words if self.dynamic_prof_words else DEFAULT_PROF_WORDS
            committed_tail = " ".join(committed_words_local[-20:]).strip()
            if committed_tail:
                return (prof_words + "\n\nCommitted (tail):\n" + committed_tail).strip()
            return prof_words

        def should_do_partial(now_t: float) -> bool:
            nonlocal last_partial_t
            if last_partial_t == 0.0:
                return True
            return (now_t - last_partial_t) * 1000.0 >= PARTIAL_UPDATE_MS

        def do_partial_decode():
            nonlocal committed_words, committed_len, recent_hyps, last_partial_t

            full_dur_sec = (len(blocks) * BLOCK_SAMPLES) / SR
            if full_dur_sec < PARTIAL_MIN_SEC:
                return

            t_check = time.monotonic()
            if not should_do_partial(t_check):
                return

            audio_tail = build_partial_audio_tail()
            if audio_tail.size <= 0:
                return

            prompt = build_partial_prompt(committed_words)

            self.transcriber_logger.debug(f"Partial decode: audio_tail size={audio_tail.size}, dur={audio_tail.size/SR:.2f}s")

            text, _info = transcribe_once(
                self.partial_model,
                audio_tail,
                language=LANGUAGE,
                beam_size=PARTIAL_BEAM_SIZE,
                temperature=TEMPERATURE,
                patience=PARTIAL_PATIENCE,
                initial_prompt=prompt,
                condition_on_previous_text=False,
                vad_filter=True,
            )

            last_partial_t = time.monotonic()

            if not text:
                self.transcriber_logger.debug("Partial decode returned empty text")
                return

            self.transcriber_logger.debug(f"Partial text: {text[:50]}...")

            tail_words = words_split(text)
            hyp_words = merge_with_overlap(committed_words[:committed_len], tail_words)

            recent_hyps.append(hyp_words)
            if len(recent_hyps) >= 2:
                lcp = lcp_wordlist(list(recent_hyps))
            else:
                lcp = hyp_words

            new_committed_len = max(committed_len, len(lcp))
            new_committed_len = min(new_committed_len, len(hyp_words))

            committed_len = new_committed_len
            committed_words = hyp_words[:committed_len]

            unstable_words = hyp_words[committed_len:]

            line = format_subtitle_line(committed_words, unstable_words)
            if line:
                # 输出 partial 字幕
                caption = CaptionOutput(
                    type="partial",
                    text=line,
                    timestamp=time.strftime("%H:%M:%S")
                )
                safe_put_drop_oldest(self.partial_output_q, caption)

                # 调用回调
                if self.partial_callback:
                    try:
                        self.partial_callback(caption)
                    except Exception as e:
                        print(f"Partial callback error: {e}")

        def finalize_sentence():
            nonlocal prev_sent_tail

            audio_full = build_full_audio()
            dur_sec = audio_full.size / SR

            self.transcriber_logger.info(f"Finalizing: audio dur={dur_sec:.2f}s, blocks={len(blocks)}")

            if dur_sec < 0.6:
                self.transcriber_logger.info("Audio too short (<0.6s), skipping")
                reset_sentence()
                return

            # 使用动态生成的 prof_words，如果没有则使用默认的
            prompt = self.dynamic_prof_words if self.dynamic_prof_words else DEFAULT_PROF_WORDS

            self.transcriber_logger.debug("Starting final decode...")

            text, info = transcribe_once(
                self.final_model,
                audio_full,
                language=LANGUAGE,
                beam_size=BEAM_SIZE,
                temperature=TEMPERATURE,
                patience=PATIENCE,
                initial_prompt=prompt,
                condition_on_previous_text=True,
                vad_filter=True,
            )

            no_speech_prob = getattr(info, "no_speech_prob", None)
            avg_logprob = getattr(info, "avg_logprob", None)

            text = (text or "").strip()

            no_speech_str = f"{no_speech_prob:.3f}" if no_speech_prob is not None else "N/A"
            logprob_str = f"{avg_logprob:.3f}" if avg_logprob is not None else "N/A"
            self.transcriber_logger.info(f"Final text: '{text}' (no_speech={no_speech_str}, logprob={logprob_str})")

            ok = True
            if not text or len(text) < MIN_CHARS_TO_PRINT:
                ok = False
                self.transcriber_logger.debug(f"Rejected: text too short ({len(text)} chars)")
            if no_speech_prob is not None and no_speech_prob > MAX_NO_SPEECH_PROB:
                ok = False
                self.transcriber_logger.debug(f"Rejected: no_speech_prob too high ({no_speech_prob:.3f})")
            if avg_logprob is not None and avg_logprob < MIN_AVG_LOGPROB:
                ok = False
                self.transcriber_logger.debug(f"Rejected: avg_logprob too low ({avg_logprob:.3f})")

            if ok:
                self.transcriber_logger.info(f"Accepted final text: {text}")
                now = time.strftime("%H:%M:%S")

                # 输出 accurate 字幕
                caption = CaptionOutput(
                    type="accurate",
                    text=text,
                    timestamp=now,
                    no_speech_prob=no_speech_prob,
                    avg_logprob=avg_logprob
                )
                safe_put_drop_oldest(self.accurate_output_q, caption)

                # 调用回调
                if self.accurate_callback:
                    try:
                        self.accurate_callback(caption)
                    except Exception as e:
                        print(f"Accurate callback error: {e}")

                # 保存到文件
                os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
                line_out = f"[{now}] {text}"
                with open(OUT_TXT, "a", encoding="utf-8") as f:
                    f.write(line_out + "\n")
                    f.flush()

                prev_sent_tail = (prev_sent_tail + " " + text).strip()[-PREV_SENT_TAIL_CHARS:]

            reset_sentence()

        # 主循环
        reset_sentence()
        while not self.stop_event.is_set():
            try:
                try:
                    evt: UTTEvent = self.evt_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                if evt.kind == "START":
                    self.transcriber_logger.info("Received START event")
                    reset_sentence()
                    if evt.audio is not None and evt.audio.size > 0:
                        blocks.append(evt.audio.astype(np.float32, copy=False))
                        self.transcriber_logger.debug(f"START audio size: {evt.audio.size}")
                    do_partial_decode()

                elif evt.kind == "CHUNK":
                    if evt.audio is None or evt.audio.size == 0:
                        continue
                    blocks.append(evt.audio.astype(np.float32, copy=False))
                    total_samples = sum(b.size for b in blocks)
                    self.transcriber_logger.debug(f"CHUNK added, total blocks: {len(blocks)}, total samples: {total_samples}")
                    do_partial_decode()

                elif evt.kind == "END":
                    self.transcriber_logger.info("Received END event, finalizing...")
                    finalize_sentence()

            except Exception as e:
                # 捕获所有异常，防止线程崩溃
                self.transcriber_logger.error(f"Transcriber error: {e}", exc_info=True)
                print(f"ERROR in transcriber: {e}")
                import traceback
                traceback.print_exc()
                # 重置状态，继续运行
                reset_sentence()
                continue
