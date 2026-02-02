"""
LLM Processor Service
LLM 处理服务，接收转写文本并生成结构化笔记
"""
import json
import queue
import threading
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from src.agent.llm import DSV3
from src.agent.prompt import promptv2
from src.agent.func import transript_chunk, pre, extract_json_object
from src.config import LLM_CHUNK_SIZE, LLM_OUTPUT_JSON


class LLMProcessorService:
    """
    LLM 处理服务
    接收 accurate 转写文本，批量处理后生成结构化内容
    """

    def __init__(self, chunk_size: int = LLM_CHUNK_SIZE):
        """
        初始化 LLM 处理服务

        Args:
            chunk_size: 每次处理的转写文本数量
        """
        self.llm_client = DSV3()
        self.chunk_size = chunk_size

        # 缓冲区
        self.transcript_buffer: List[str] = []
        self.prev_supplement = ''  # 上一个 chunk 的 supplement

        # 结果存储
        self.structured_content: List[Dict[str, Any]] = []
        self.all_supplements: List[str] = []

        # 线程安全
        self.lock = threading.Lock()

        # 异步处理队列
        self.process_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.process_thread: Optional[threading.Thread] = None

        # 回调
        self.on_processed_callback: Optional[Callable[[Dict[str, Any]], None]] = None

        # 是否启用自动保存
        self.auto_save = True

        # 会话管理：每次开始转写时生成新的文件名
        self.session_start_time: Optional[str] = None
        self.save_path: Optional[str] = None

    def set_on_processed_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置处理完成回调"""
        self.on_processed_callback = callback

    def start_session(self):
        """
        开始新的转写会话
        生成基于时间戳的文件名
        """
        self.session_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确保 data/logs 目录存在
        logs_dir = os.path.join("data", "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # 生成文件路径: data/logs/20260118_143025_content.json
        self.save_path = os.path.join(logs_dir, f"{self.session_start_time}_content.json")

        print(f"Started new session: {self.session_start_time}")
        print(f"Content will be saved to: {self.save_path}")

    def start_async_processing(self):
        """启动异步处理线程"""
        if self.process_thread and self.process_thread.is_alive():
            print("Async processing already running!")
            return

        self.stop_event.clear()
        self.process_thread = threading.Thread(target=self._async_processor, daemon=True)
        self.process_thread.start()
        print("LLM async processing started!")

    def stop_async_processing(self):
        """停止异步处理线程"""
        self.stop_event.set()
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        print("LLM async processing stopped!")

    def add_transcript(self, text: str):
        """
        添加一条转写文本

        Args:
            text: accurate 转写文本
        """
        with self.lock:
            self.transcript_buffer.append(text)

            # 检查是否达到批次大小
            if len(self.transcript_buffer) >= self.chunk_size:
                # 提取要处理的 chunk
                chunk = self.transcript_buffer[:self.chunk_size]
                self.transcript_buffer = self.transcript_buffer[self.chunk_size:]

                # 放入处理队列
                self.process_queue.put(chunk)

    def process_batch_sync(self, chunk: List[str]) -> Dict[str, Any]:
        """
        同步处理一个批次（阻塞）

        Args:
            chunk: 转写文本列表

        Returns:
            结构化内容
        """
        # 合并 chunk
        transcript_text = ' '.join(chunk)

        # 构建提示词
        prompt_trans = pre(self.prev_supplement) + transript_chunk(transcript_text)
        full_prompt = promptv2 + prompt_trans

        # 调用 LLM
        print(f"Processing {len(chunk)} transcripts with LLM...")
        resp = self.llm_client.generate(full_prompt)

        # 提取 JSON
        resp_json = extract_json_object(resp)

        if resp_json is None:
            print("Warning: Failed to extract JSON from LLM response")
            return {
                "content": {"coursework": [], "knowledge": [], "question": []},
                "supplement": {"ongoing": [], "carryover_raw": []}
            }

        # 提取结果
        content = resp_json.get('content', {"coursework": [], "knowledge": [], "question": []})
        supplement = resp_json.get('supplement', {"ongoing": [], "carryover_raw": []})

        # 更新 prev_supplement
        self.prev_supplement = json.dumps(supplement)

        # 存储结果
        with self.lock:
            self.structured_content.append(content)
            self.all_supplements.append(self.prev_supplement)

        # 自动保存
        if self.auto_save:
            self.save_to_file()

        # 回调
        if self.on_processed_callback:
            try:
                self.on_processed_callback(content)
            except Exception as e:
                print(f"Callback error: {e}")

        print(f"Processed batch successfully! Total batches: {len(self.structured_content)}")
        return content

    def _async_processor(self):
        """异步处理器（在后台线程运行）"""
        while not self.stop_event.is_set():
            try:
                chunk = self.process_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.process_batch_sync(chunk)
            except Exception as e:
                print(f"Error processing batch: {e}")

    def get_all_content(self) -> List[Dict[str, Any]]:
        """获取所有结构化内容"""
        with self.lock:
            return self.structured_content.copy()

    def get_latest_content(self, n: int = 1) -> List[Dict[str, Any]]:
        """
        获取最新的 n 条结构化内容

        Args:
            n: 返回的条数

        Returns:
            最新的 n 条内容
        """
        with self.lock:
            return self.structured_content[-n:] if self.structured_content else []

    def save_to_file(self, filepath: Optional[str] = None):
        """
        保存结构化内容到文件

        Args:
            filepath: 保存路径，默认使用会话路径
        """
        save_path = filepath or self.save_path

        if not save_path:
            print("Warning: No save path set. Call start_session() first.")
            return

        with self.lock:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.structured_content, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(self.structured_content)} batches to {save_path}")

    def load_from_file(self, filepath: str):
        """
        从文件加载结构化内容

        Args:
            filepath: 文件路径
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        with self.lock:
            self.structured_content = data

        print(f"Loaded {len(self.structured_content)} batches from {filepath}")

    def clear(self):
        """清空所有缓冲和结果"""
        with self.lock:
            self.transcript_buffer = []
            self.structured_content = []
            self.all_supplements = []
            self.prev_supplement = ''

        print("LLM service cleared!")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                "buffer_size": len(self.transcript_buffer),
                "processed_batches": len(self.structured_content),
                "queue_size": self.process_queue.qsize(),
                "chunk_size": self.chunk_size,
                "session_start_time": self.session_start_time,
                "save_path": self.save_path
            }

    def get_content_as_text(self) -> str:
        """
        将所有结构化内容转换为纯文本字符串
        用于问答功能

        Returns:
            格式化的文本内容
        """
        with self.lock:
            if not self.structured_content:
                return ""

            text_parts = []

            for idx, batch in enumerate(self.structured_content, 1):
                text_parts.append(f"=== Batch {idx} ===\n")

                # Coursework
                if batch.get("coursework"):
                    text_parts.append("【课程安排】\n")
                    for item in batch["coursework"]:
                        text_parts.append(f"- {item}\n")
                    text_parts.append("\n")

                # Knowledge
                if batch.get("knowledge"):
                    text_parts.append("【知识点】\n")
                    for item in batch["knowledge"]:
                        text_parts.append(f"- {item}\n")
                    text_parts.append("\n")

                # Question
                if batch.get("question"):
                    text_parts.append("【问题】\n")
                    for item in batch["question"]:
                        text_parts.append(f"- {item}\n")
                    text_parts.append("\n")

            return "".join(text_parts)

    def answer_question(self, user_input: str) -> str:
        """
        基于转写内容回答用户问题

        Args:
            user_input: 用户的问题

        Returns:
            LLM 的回答
        """
        # 获取当前所有转写内容
        content = self.get_content_as_text()

        if not content:
            return "抱歉，当前还没有转写内容。请先开始转写。"

        # 构建提示词
        prompt = f"""<user_query>{user_input}</user_query>

<class_content>
{content}
</class_content>

请结合上述课堂内容回答用户的问题。如果用户问题是课堂设置（作业 考试 助教等）相关问题且课堂内容中没有相关信息，请明确告知用户；
如果是知识问题且课堂内容中没有相关信息，则不影响正常回答，给出知识解答”。"""

        # 调用 LLM
        try:
            response = self.llm_client.generate(prompt)
            return response
        except Exception as e:
            return f"回答问题时出错: {str(e)}"


# ====== 批量处理工具函数 ======
def batch_process_from_json(input_json: str, output_json: str, chunk_size: int = 4):
    """
    从 JSON 文件批量处理转写文本（兼容原始 llmprocess.ipynb 的逻辑）

    Args:
        input_json: 输入的 transcript_list.json 路径
        output_json: 输出的结构化内容 JSON 路径
        chunk_size: 每次处理的文本数量
    """
    # 加载数据
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} transcripts from {input_json}")

    # 创建服务
    service = LLMProcessorService(chunk_size=chunk_size)
    service.auto_save = False  # 禁用自动保存

    # 批量处理
    result_list = []
    prev_list = []

    chunk = []
    prev = ''

    for i, text in enumerate(data):
        chunk.append(text)

        if (i + 1) % chunk_size == 0 and i != 0:
            # 合并 chunk
            transcript_text = ' '.join(chunk)
            prompt_trans = pre(prev) + transript_chunk(transcript_text)

            # 调用 LLM
            llm = DSV3()
            resp = llm.generate(promptv2 + prompt_trans)

            # 提取 JSON
            resp_json = extract_json_object(resp)

            if resp_json:
                content = resp_json.get('content', {})
                prev = json.dumps(resp_json.get('supplement', {}))

                result_list.append(content)
                prev_list.append(prev)

                print(f"Processed batch {len(result_list)}: {content}")
            else:
                print(f"Warning: Failed to extract JSON at batch {i // chunk_size}")

            chunk = []

    # 保存结果
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(result_list)} batches to {output_json}")
    return result_list
