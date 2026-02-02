"""
ClassAudio Configuration Example File
配置示例文件 - 复制此文件为 config_local.py 并填写实际值
"""
import os

# ====== 路径配置 ======
# BASE_DIR 现在指向项目根目录（src/ 的父目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# VAD 模型路径
VAD_DIR = os.path.join(DATA_DIR, "vad", "silero-vad-master")

# Whisper 模型路径
# 请下载模型并放置在以下路径，或修改为你的模型路径
MODEL_DIR_FINAL = os.path.join(
    DATA_DIR,
    "models",
    "models--Systran--faster-whisper-medium.en",
    "snapshots",
    "a29b04bd15381511a9af671baec01072039215e3"
)
MODEL_DIR_PARTIAL = os.path.join(DATA_DIR, "models", "faster-whisper-small.en")

# 输出路径
LOGS_DIR = os.path.join(DATA_DIR, "logs")
OUT_TXT = os.path.join(LOGS_DIR, "captions.txt")
TRANSCRIPT_LIST_JSON = os.path.join(DATA_DIR, "transcript_list.json")

# ====== 音频配置 ======
SR = 16000  # 采样率
CHANNELS = 1  # 单声道
BLOCK_MS = 32  # 每个音频块的毫秒数
BLOCK_SAMPLES = int(SR * BLOCK_MS / 1000)

# 队列大小
AUDIO_Q_MAX = 300
UTT_Q_MAX = 4000

# ====== VAD 配置 ======
VAD_THRESHOLD = 0.5  # 语音检测阈值
MIN_SPEECH_MS = 250  # 最小语音持续时间
MIN_SILENCE_MS = 800  # 最小静音持续时间
MAX_UTT_S = 18  # 最大语音段长度（秒）

PADDING_MS = 200  # 前置填充
PADDING_SAMPLES = int(SR * PADDING_MS / 1000)
END_TAIL_MS = 200  # 尾部静音保留

# ====== Whisper 解码配置 (Final Model) ======
LANGUAGE = "en"
BEAM_SIZE = 8
TEMPERATURE = 0.0
PATIENCE = 1.2
COMPUTE_TYPE_FINAL = "float16"  # GPU: float16, CPU: int8 或 float32

# ====== Partial 字幕配置 ======
PARTIAL_UPDATE_MS = 300  # partial 更新间隔（毫秒）
PARTIAL_MIN_SEC = 0.8  # partial 最小音频长度
PARTIAL_TAIL_SEC = 10.0  # partial 解码尾部长度
PARTIAL_BEAM_SIZE = 4
PARTIAL_PATIENCE = 1.0
STABLE_HYPS = 3  # 稳定假设数量
COMMITTED_PROMPT_WORDS = 60
PREV_SENT_TAIL_CHARS = 240

COMPUTE_TYPE_PARTIAL = "float16"

# ====== 输出过滤配置 ======
MIN_CHARS_TO_PRINT = 3  # 最小字符数
MAX_NO_SPEECH_PROB = 0.6  # 最大非语音概率
MIN_AVG_LOGPROB = -1.0  # 最小平均对数概率

# ====== 专业词汇提示词 ======
# 默认提示词（当用户未设置课堂主题时使用）
# 建议：启动后通过前端设置课堂主题，由 LLM 生成专业词汇
DEFAULT_PROF_WORDS = """
This is an academic lecture. Please transcribe all technical terms accurately using their standard spelling.
""".strip()

# ====== LLM 配置 ======
# DeepSeek V3 配置 - 用于关键词生成
# 请从环境变量设置，或在 config_local.py 中覆盖
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY_HERE")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v3-2-251201")

# DuBao Flash 配置 - 用于内容整理
# 请从环境变量设置，或在 config_local.py 中覆盖
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "YOUR_DOUBAO_API_KEY_HERE")
DOUBAO_BASE_URL = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-flash-250828")

# LLM 处理配置
LLM_CHUNK_SIZE = 4  # 每次处理的转写文本数量
LLM_OUTPUT_JSON = os.path.join(LOGS_DIR, "llmcontent-latest.json")

# 确保 logs 目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

# ====== GPU 配置 ======
DEVICE = "cuda"  # 使用 CUDA 加速，CPU 设为 "cpu"

# ====== 本地配置覆盖 ======
# 如果存在 config_local.py，则导入并覆盖上述配置
try:
    from .config_local import *
except ImportError:
    pass
