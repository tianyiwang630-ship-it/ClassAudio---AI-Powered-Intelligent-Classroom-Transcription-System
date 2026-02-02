# ClassAudio - AI驱动的智能课堂转写系统

<p align="center">
  <strong>实时语音转写 | AI智能整理 | 专业术语优化</strong>
</p>

<p align="center">
  <a href="README_EN.md">English</a> | 中文
</p>

---

## 📖 项目背景

在现代教育和学习场景中，高质量的课堂笔记对知识吸收至关重要。然而，传统的手写笔记存在以下痛点：

- **分心问题**：手写笔记会分散学生对课堂内容的注意力
- **专业术语障碍**：技术课程中的专业词汇难以快速准确记录
- **整理成本高**：课后需要花费大量时间整理和分类笔记
- **信息缺失**：无法同时专注听讲和记录完整内容

ClassAudio 通过 AI 技术解决这些痛点，提供**实时、准确、结构化**的课堂转写服务。

---

## ✨ 核心功能

### 1. 实时语音转写
- **低延迟显示**：边说边显示，延迟 < 1 秒
- **双模型架构**：
  - Partial 模式：快速预览（faster-whisper-small）
  - Accurate 模式：高精度终稿（faster-whisper-medium）
- **智能语音检测**：基于 Silero-VAD 的精准语音活动检测

### 2. AI 智能词汇优化
- **课堂主题感知**：输入课堂主题（如 "量子计算"、"Transformer 架构"）
- **LLM 生成专业词汇**：自动生成 30+ 相关专业术语
- **提升转写准确度**：将生成的词汇作为 Whisper 的提示词，大幅提高专业术语识别率

### 3. 结构化笔记整理
- **自动分类**：LLM 将转写内容分类为：
  - 📚 课程内容（Course Content）
  - 💡 知识点（Knowledge Points）
  - ❓ 问题讨论（Questions & Discussions）
- **实时生成**：每 4 条转写文本自动触发整理
- **JSON 导出**：支持导出结构化笔记数据

### 4. 优质用户体验
- **美观界面**：现代化渐变设计 + 流畅动画
- **稳定连接**：WebSocket 心跳保活 + 自动重连机制
- **一键启动**：Windows 双击启动，自动打开浏览器

### 📹 演示视频

https://github.com/user-attachments/assets/5fdcb5b0-063b-40a9-8a43-d4ad83525436

---

## 🎯 核心价值

### 对学生
- ✅ **专注听讲**：无需分心手写，自动生成完整笔记
- ✅ **高精度记录**：专业术语准确识别，无遗漏
- ✅ **快速复习**：结构化笔记便于课后查找和复习

### 对教育机构
- ✅ **提升教学质量**：学生更专注课堂互动
- ✅ **知识留存**：完整保留课堂知识内容
- ✅ **数据分析**：可分析课程关键词和学生提问

### 对开发者
- ✅ **开源免费**：MIT 协议，可自由修改和商用
- ✅ **易于扩展**：模块化架构，支持自定义 LLM 和模型
- ✅ **完整文档**：详细技术文档 + 故障排查指南

---

## 🛠️ 技术实现

### 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Frontend)                   │
│  - WebSocket 实时连接  - Toast 通知  - 响应式 UI     │
└────────────────────┬────────────────────────────────┘
                     │ WebSocket + HTTP API
┌────────────────────▼────────────────────────────────┐
│              FastAPI 服务器 (Backend)                │
│  - WebSocket 推送  - RESTful API  - 自动重连机制     │
└──────┬──────────────────────────────────┬───────────┘
       │                                  │
┌──────▼──────────────┐        ┌──────────▼───────────┐
│  Audio Service      │        │   LLM Service        │
│  ┌──────────────┐   │        │  ┌────────────────┐  │
│  │ VAD 分割     │   │        │  │ 内容分类整理    │  │
│  └──────┬───────┘   │        │  └────────────────┘  │
│  ┌──────▼───────┐   │        │  ┌────────────────┐  │
│  │ Partial 解码 │   │        │  │ 关键词生成      │  │
│  └──────────────┘   │        │  └────────────────┘  │
│  ┌──────────────┐   │        │                      │
│  │ Final 解码   │   │        │  LLM: DeepSeek V3    │
│  └──────────────┘   │        │       Doubao Flash   │
└─────────────────────┘        └──────────────────────┘
     Whisper + VAD                   OpenAI API
```

### 核心技术栈

**后端**
- **FastAPI** - 高性能异步 Web 框架
- **WebSocket** - 实时双向通信
- **faster-whisper** - CUDA 加速的 Whisper 实现
- **Silero-VAD** - 轻量级语音活动检测
- **PyAudio** - 实时音频流捕获

**前端**
- **原生 JavaScript** - 无框架依赖，性能优先
- **WebSocket API** - 实时数据推送
- **CSS Grid/Flexbox** - 现代化响应式布局

**AI 模型**
- **Whisper (Small & Medium)** - OpenAI 语音识别模型
- **DeepSeek V3** - 用于专业词汇生成
- **Doubao Flash** - 用于内容结构化整理

### 关键技术亮点

1. **双模型并行架构**
   - Partial 模型提供快速反馈（0.5-1s 延迟）
   - Final 模型保证高精度（质量指标监控）

2. **动态提示词注入**
   - LLM 根据课堂主题生成专业词汇
   - 动态注入到 Whisper 的 `initial_prompt` 参数
   - 显著提升专业术语识别准确率

3. **智能语音分割**
   - VAD 实时检测语音活动
   - 自适应静音阈值（800ms）
   - 避免句子截断和过度分割

4. **鲁棒性设计**
   - WebSocket 心跳保活（30s 间隔）
   - 自动重连机制（指数退避）
   - 详细日志系统（分级日志 + 实时查看工具）

---

## 🚀 快速开始

### 环境要求

- **Python 3.10+**
- **CUDA** (可选，GPU 加速)
- **麦克风设备**

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/classaudio.git
cd classaudio
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **下载模型**

**重要：本仓库不包含模型文件（约 3GB），需手动下载。**

- **Whisper 模型**：
  - 下载 [faster-whisper-small.en](https://huggingface.co/Systran/faster-whisper-small.en)
  - 下载 [faster-whisper-medium.en](https://huggingface.co/Systran/faster-whisper-medium.en)
  - 放置到 `data/models/` 目录

- **VAD 模型**：
  - 下载 [silero-vad](https://github.com/snakers4/silero-vad)
  - 放置到 `data/vad/silero-vad-master/` 目录

**目录结构示例：**
```
data/
├── models/
│   ├── faster-whisper-small.en/
│   └── models--Systran--faster-whisper-medium.en/
│       └── snapshots/
│           └── a29b04bd15381511a9af671baec01072039215e3/
└── vad/
    └── silero-vad-master/
```

4. **配置 API Keys**

**方法 1：使用环境变量（推荐）**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API keys
```

**方法 2：使用本地配置文件**
```bash
cp src/config.example.py src/config_local.py
# 编辑 config_local.py，填入你的 API keys
```

**需要的 API Keys：**
- `DEEPSEEK_API_KEY` - 用于关键词生成（DeepSeek V3）
- `DOUBAO_API_KEY` - 用于内容整理（Doubao Flash）

5. **启动应用**

**Windows 用户（推荐）：**
```bash
启动ClassAudio.bat
```

**通用方式：**
```bash
python run.py
```

浏览器会自动打开 `http://localhost:8000`。

### 使用流程

1. **设置课堂主题**（可选但推荐）
   - 在页面顶部输入框输入主题，如 "量子计算"、"深度学习"
   - 点击"设置主题"，等待 LLM 生成专业词汇（约 5-15 秒）

2. **开始录音**
   - 点击"开始录音"按钮
   - 对着麦克风说话
   - 实时字幕会即时显示

3. **查看结果**
   - **Partial 字幕**：实时预览（灰色）
   - **Accurate 字幕**：最终结果（绿色，带质量指标）
   - **结构化笔记**：页面右侧自动分类显示

---

## 📁 项目结构

```
classaudio/
├── src/                        # 源代码
│   ├── services/               # 核心服务
│   │   ├── audio_service.py    # 音频转写服务
│   │   └── llm_service.py      # LLM 处理服务
│   ├── api/                    # API 接口
│   │   └── server.py           # FastAPI 服务器
│   ├── agent/                  # LLM 代理
│   │   ├── keywords.py         # 关键词生成
│   │   ├── llm.py              # LLM 接口
│   │   └── prompt.py           # 提示词模板
│   ├── config.py               # 配置文件
│   └── config.example.py       # 配置示例
│
├── frontend/                   # 前端界面
│   ├── index.html              # 主页面
│   ├── app.js                  # 前端逻辑
│   └── styles.css              # 样式文件
│
├── scripts/                    # 工具脚本
│   └── launcher.py             # 启动器
│
├── docs/                       # 文档
│   ├── 快速启动指南.md
│   ├── 课堂主题功能说明.md
│   ├── 故障排查指南.md
│   └── 日志系统说明.md
│
├── data/                       # 数据目录（Git 忽略）
│   ├── models/                 # Whisper 模型（需手动下载）
│   ├── vad/                    # VAD 模型（需手动下载）
│   └── logs/                   # 运行时日志
│
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略配置
├── requirements.txt            # Python 依赖
├── run.py                      # 启动入口
└── README.md                   # 本文件
```

---

## 📚 文档

- [快速启动指南](docs/快速启动指南.md) - 详细安装和配置
- [课堂主题功能说明](docs/课堂主题功能说明.md) - 智能专业词汇生成
- [故障排查指南](docs/故障排查指南.md) - 常见问题解决方案
- [日志系统说明](docs/日志系统说明.md) - 日志查看和分析
- [项目架构](PROJECT_STRUCTURE.md) - 完整技术文档

---

## 🛠️ 工具脚本

### 日志查看器
实时查看系统日志：
```bash
python view_logs.py
```

### 缓存清理
清理 Python 字节码缓存：
```bash
clear_cache.bat  # Windows
# 或手动删除 __pycache__ 目录
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别模型
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - CUDA 加速实现
- [Silero-VAD](https://github.com/snakers4/silero-vad) - 语音活动检测
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架

---

## 📧 联系方式

如有问题或建议，请提交 [Issue](https://github.com/yourusername/classaudio/issues)。

---

<p align="center">
  Made with ❤️ for better learning experience
</p>
