# ClassAudio 项目结构

## 目录结构

```
classaudio/
│
├── frontend/                   # 前端界面
│   ├── index.html             # 主页面
│   ├── app.js                 # 前端逻辑
│   └── styles.css             # 样式文件
│
├── src/                       # 源代码
│   ├── agent/                 # LLM 代理模块
│   │   ├── func.py           # 工具函数
│   │   ├── keywords.py       # 专业词汇生成
│   │   ├── llm.py            # LLM 接口
│   │   └── prompt.py         # 提示词模板
│   │
│   ├── api/                   # API 服务
│   │   └── server.py         # FastAPI 服务器
│   │
│   ├── services/              # 核心服务
│   │   ├── audio_service.py  # 音频转写服务
│   │   └── llm_service.py    # LLM 处理服务
│   │
│   └── config.py              # 全局配置
│
├── scripts/                   # 工具脚本
│   └── launcher.py           # 启动器
│
├── docs/                      # 文档
│   ├── 快速启动指南.md
│   ├── 连接稳定性改进.md
│   ├── 转写停止问题修复.md
│   ├── 日志系统说明.md
│   └── 课堂主题功能说明.md
│
├── data/                      # 数据目录
│   ├── models/               # Whisper 模型（忽略提交）
│   ├── vad/                  # VAD 模型（忽略提交）
│   └── logs/                 # 运行时日志（忽略提交）
│
├── logs/                      # 系统日志（忽略提交）
│   ├── audio_service.log
│   ├── vad.log
│   └── transcriber.log
│
├── keywords.ipynb             # 关键词生成测试笔记本
├── run.py                     # 快捷启动入口
├── view_logs.py              # 日志查看工具
├── clear_cache.bat           # 缓存清理工具
├── 启动ClassAudio.bat         # Windows 一键启动
├── requirements.txt          # Python 依赖
├── README.md                 # 项目说明
├── PROJECT_STRUCTURE.md      # 本文件
└── .gitignore               # Git 忽略配置

```

---

## 核心模块说明

### 1. 前端 (frontend/)

**职责：** 用户界面和交互

**主要文件：**
- `index.html` - 页面结构，包含主题设置、控制面板、字幕显示、笔记展示
- `app.js` - WebSocket 连接、API 调用、状态管理、事件处理
- `styles.css` - 渐变主题设计、响应式布局

**关键功能：**
- 课堂主题设置和专业词汇生成
- 实时 WebSocket 连接（支持自动重连、心跳保活）
- Partial 和 Accurate 字幕显示
- 结构化笔记展示
- Toast 通知系统

---

### 2. 音频转写服务 (src/services/audio_service.py)

**职责：** 音频捕获、VAD 分割、Whisper 转写

**核心组件：**
- **VAD 线程：** 实时语音活动检测，分割音频段
- **Transcriber 线程：** 处理音频段，生成 partial 和 final 字幕
- **双模型架构：**
  - Partial 解码：faster-whisper-small.en（快速响应）
  - Final 解码：faster-whisper-medium.en（高准确度）

**动态专业词汇：**
- `dynamic_prof_words` 属性存储用户设置的专业词汇
- `set_prof_words()` 方法动态更新提示词
- 应用于 partial 和 final 解码的 prompt

**输出队列：**
- `partial_output_q` - Partial 字幕队列
- `accurate_output_q` - Accurate 字幕队列

---

### 3. LLM 处理服务 (src/services/llm_service.py)

**职责：** 结构化笔记生成

**处理流程：**
1. 接收 accurate 字幕
2. 累积到 4 条后触发处理
3. 调用 LLM 分类为：课程内容、知识点、问题讨论
4. 返回结构化 JSON

**LLM 配置：**
- DeepSeek V3 用于关键词生成
- Doubao Flash 用于内容整理

---

### 4. 关键词生成 (src/agent/keywords.py)

**职责：** 根据课堂主题生成专业词汇

**实现：**
- 使用预设 prompt 模板
- 强制英文输出（即使输入中文）
- 生成至少 30 个专业术语
- 包含标准学术拼写

**使用场景：**
- 用户在前端输入课堂主题
- 后端调用 `generate_prof_words(topic)`
- 自动设置到 audio_service

---

### 5. API 服务 (src/api/server.py)

**职责：** 提供 HTTP 和 WebSocket 接口

**主要端点：**

**控制类：**
- `POST /api/control/start` - 开始录音
- `POST /api/control/stop` - 停止录音

**关键词类：**
- `POST /api/keywords/generate` - 生成专业词汇
- `POST /api/keywords/set` - 手动设置专业词汇

**内容类：**
- `GET /api/structured-content` - 获取结构化笔记
- `POST /api/structured-content/clear` - 清空笔记

**WebSocket：**
- `ws://localhost:8000/ws/captions` - 实时字幕推送

---

### 6. 配置管理 (src/config.py)

**职责：** 集中管理所有配置参数

**主要配置：**
- 路径配置（模型、日志、输出）
- 音频参数（采样率、通道、块大小）
- VAD 参数（阈值、静音时长）
- Whisper 参数（beam size、温度、compute type）
- LLM 配置（API key、模型选择）
- 默认提示词（DEFAULT_PROF_WORDS）- 用户未设置主题时的基础提示

---

### 7. 工具脚本

**launcher.py (scripts/)**
- 自动启动后端和前端
- 监控子进程日志
- UTF-8 编码处理

**view_logs.py**
- 实时查看系统日志
- 显示最新 20 行
- 监控新日志输出

**clear_cache.bat**
- 清理 Python 字节码缓存
- 确保代码修改生效

**启动ClassAudio.bat**
- 一键启动（Windows）
- 自动清理缓存
- 调用 launcher.py

---

## 数据流

### 1. 音频转写流程

```
麦克风输入
    ↓
音频流捕获 (pyaudio)
    ↓
VAD 分割 (silero-vad)
    ↓
音频块队列 (utt_q)
    ↓
┌─────────────────────────────┐
│  Transcriber 线程            │
│  ├─ Partial 解码 (实时)      │
│  └─ Final 解码 (准确)        │
└─────────────────────────────┘
    ↓
输出队列 (partial_output_q, accurate_output_q)
    ↓
WebSocket 推送到前端
```

### 2. 专业词汇流程

```
用户输入主题
    ↓
前端调用 /api/keywords/generate
    ↓
LLM 生成专业词汇
    ↓
audio_service.set_prof_words()
    ↓
应用于 Whisper prompt
    ↓
提高转写准确度
```

### 3. 笔记整理流程

```
Accurate 字幕
    ↓
llm_service.add_transcript()
    ↓
累积到 4 条
    ↓
异步处理线程
    ↓
LLM 分类整理
    ↓
存储到 content_list
    ↓
前端轮询获取
```

---

## 日志系统

### 日志文件

- `logs/audio_service.log` - 服务启动、停止、配置变更
- `logs/vad.log` - 语音检测（START/END）、静音时长
- `logs/transcriber.log` - Partial/Final 解码、质量指标

### 日志级别

- **DEBUG：** 详细的技术细节（音频长度、队列大小）
- **INFO：** 关键事件（语音检测、转写完成）
- **ERROR：** 异常和错误（含完整堆栈）

### 查看日志

```bash
# 实时查看所有日志
python view_logs.py

# 查看特定日志
tail -f logs/transcriber.log
```

---

## 技术栈

### 后端
- **FastAPI** - Web 框架
- **WebSocket** - 实时通信
- **faster-whisper** - 语音识别
- **silero-vad** - 语音活动检测
- **pyaudio** - 音频捕获
- **OpenAI API** - LLM 接口（兼容）

### 前端
- **原生 JavaScript** - 无框架依赖
- **WebSocket API** - 实时连接
- **Fetch API** - HTTP 请求
- **CSS Grid/Flexbox** - 响应式布局

### 开发工具
- **Python 3.10+**
- **CUDA** (可选，GPU 加速)
- **Git** - 版本控制

---

## 依赖管理

### 核心依赖 (requirements.txt)

```
fastapi
uvicorn
websockets
faster-whisper
pyaudio
torch
openai
```

### 安装

```bash
pip install -r requirements.txt
```

---

## 启动方式

### Windows（推荐）

```bash
启动ClassAudio.bat
```

### 通用方式

```bash
python run.py
```

### 手动启动

```bash
# 后端
python scripts/launcher.py

# 前端（浏览器自动打开）
```

---

## 常见问题

### 1. 转写停止
查看 [转写停止问题修复.md](docs/转写停止问题修复.md)

### 2. 连接断开
查看 [连接稳定性改进.md](docs/连接稳定性改进.md)

### 3. 代码修改不生效
运行 `clear_cache.bat`

### 4. 日志查看
运行 `python view_logs.py`

---

## 维护指南

### 添加新功能

1. 在相应模块添加代码
2. 更新 `config.py` 添加配置
3. 在 `server.py` 添加 API 端点
4. 更新前端 `app.js` 调用
5. 添加文档到 `docs/`

### 调试技巧

1. 查看日志文件确定问题位置
2. 使用 `view_logs.py` 实时监控
3. 检查浏览器控制台（前端错误）
4. 清理缓存后重启

### 性能优化

1. 调整 VAD 参数（`config.py`）
2. 选择合适的 Whisper 模型大小
3. 优化 LLM chunk size
4. 使用 GPU 加速（CUDA）

---

## 许可证

MIT License

---

## 相关文档

- [README.md](README.md) - 项目概述和快速开始
- [快速启动指南.md](docs/快速启动指南.md) - 详细安装配置
- [课堂主题功能说明.md](docs/课堂主题功能说明.md) - 专业词汇功能
- [日志系统说明.md](docs/日志系统说明.md) - 日志查看和排错
