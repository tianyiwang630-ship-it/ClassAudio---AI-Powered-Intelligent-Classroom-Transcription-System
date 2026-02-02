# ClassAudio - AI-Powered Intelligent Classroom Transcription System

<p align="center">
  <strong>Real-time Speech Transcription | AI Smart Organization | Professional Terminology Optimization</strong>
</p>

<p align="center">
  English | <a href="README.md">中文</a>
</p>

---

## 📖 Background

In modern education and learning scenarios, high-quality classroom notes are crucial for knowledge retention. However, traditional handwritten notes suffer from several pain points:

- **Distraction Problem**: Taking notes by hand diverts students' attention from the lecture
- **Technical Terminology Barriers**: Difficult to quickly and accurately record specialized vocabulary in technical courses
- **High Organization Cost**: Significant time required after class to organize and categorize notes
- **Information Loss**: Impossible to simultaneously focus on listening and recording complete content

ClassAudio solves these pain points through AI technology, providing **real-time, accurate, and structured** classroom transcription services.

---

## ✨ Core Features

### 1. Real-time Speech Transcription
- **Low Latency Display**: Simultaneous display with < 1 second delay
- **Dual Model Architecture**:
  - Partial Mode: Quick preview (faster-whisper-small)
  - Accurate Mode: High-precision final version (faster-whisper-medium)
- **Intelligent Voice Detection**: Precise voice activity detection based on Silero-VAD

### 2. AI Smart Vocabulary Optimization
- **Classroom Topic Awareness**: Input classroom topic (e.g., "Quantum Computing", "Transformer Architecture")
- **LLM-Generated Professional Vocabulary**: Automatically generates 30+ relevant technical terms
- **Improved Transcription Accuracy**: Uses generated vocabulary as Whisper prompts, significantly improving technical term recognition

### 3. Structured Note Organization
- **Automatic Classification**: LLM categorizes transcribed content into:
  - 📚 Course Content
  - 💡 Knowledge Points
  - ❓ Questions & Discussions
- **Real-time Generation**: Automatically triggers organization every 4 transcription texts
- **JSON Export**: Supports exporting structured note data

### 4. Premium User Experience
- **Beautiful Interface**: Modern gradient design + smooth animations
- **Stable Connection**: WebSocket heartbeat keep-alive + automatic reconnection mechanism
- **One-Click Launch**: Windows double-click start, automatically opens browser

### 📹 Demo Video

https://github.com/user-attachments/assets/5fdcb5b0-063b-40a9-8a43-d4ad83525436

---

## 🎯 Core Value

### For Students
- ✅ **Focus on Listening**: No need to be distracted by handwriting, automatic complete notes generation
- ✅ **High Precision Recording**: Accurate technical term recognition, no omissions
- ✅ **Quick Review**: Structured notes facilitate post-class search and review

### For Educational Institutions
- ✅ **Improved Teaching Quality**: Students more focused on classroom interaction
- ✅ **Knowledge Retention**: Complete preservation of classroom knowledge content
- ✅ **Data Analysis**: Analyze course keywords and student questions

### For Developers
- ✅ **Open Source & Free**: MIT License, free to modify and commercialize
- ✅ **Easy to Extend**: Modular architecture, supports custom LLM and models
- ✅ **Complete Documentation**: Detailed technical documentation + troubleshooting guide

---

## 🛠️ Technical Implementation

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│  - WebSocket Real-time  - Toast Notify  - Responsive│
└────────────────────┬────────────────────────────────┘
                     │ WebSocket + HTTP API
┌────────────────────▼────────────────────────────────┐
│              FastAPI Server (Backend)                │
│  - WebSocket Push  - RESTful API  - Auto-reconnect  │
└──────┬──────────────────────────────────┬───────────┘
       │                                  │
┌──────▼──────────────┐        ┌──────────▼───────────┐
│  Audio Service      │        │   LLM Service        │
│  ┌──────────────┐   │        │  ┌────────────────┐  │
│  │ VAD Split    │   │        │  │ Content Class  │  │
│  └──────┬───────┘   │        │  └────────────────┘  │
│  ┌──────▼───────┐   │        │  ┌────────────────┐  │
│  │ Partial Decode  │        │  │ Keyword Gen    │  │
│  └──────────────┘   │        │  └────────────────┘  │
│  ┌──────────────┐   │        │                      │
│  │ Final Decode │   │        │  LLM: DeepSeek V3    │
│  └──────────────┘   │        │       Doubao Flash   │
└─────────────────────┘        └──────────────────────┘
     Whisper + VAD                   OpenAI API
```

### Core Tech Stack

**Backend**
- **FastAPI** - High-performance async web framework
- **WebSocket** - Real-time bidirectional communication
- **faster-whisper** - CUDA-accelerated Whisper implementation
- **Silero-VAD** - Lightweight voice activity detection
- **PyAudio** - Real-time audio stream capture

**Frontend**
- **Native JavaScript** - No framework dependencies, performance-first
- **WebSocket API** - Real-time data push
- **CSS Grid/Flexbox** - Modern responsive layout

**AI Models**
- **Whisper (Small & Medium)** - OpenAI speech recognition model
- **DeepSeek V3** - For professional vocabulary generation
- **Doubao Flash** - For content structured organization

### Key Technical Highlights

1. **Dual Model Parallel Architecture**
   - Partial model provides quick feedback (0.5-1s latency)
   - Final model ensures high precision (quality metric monitoring)

2. **Dynamic Prompt Injection**
   - LLM generates professional vocabulary based on classroom topic
   - Dynamically injected into Whisper's `initial_prompt` parameter
   - Significantly improves technical term recognition accuracy

3. **Intelligent Voice Segmentation**
   - VAD real-time voice activity detection
   - Adaptive silence threshold (800ms)
   - Avoids sentence truncation and over-segmentation

4. **Robustness Design**
   - WebSocket heartbeat keep-alive (30s interval)
   - Automatic reconnection mechanism (exponential backoff)
   - Detailed logging system (hierarchical logs + real-time viewer)

---

## 🚀 Quick Start

### Requirements

- **Python 3.10+**
- **CUDA** (optional, GPU acceleration)
- **Microphone Device**

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/classaudio.git
cd classaudio
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Download Models**

**Important: This repository does not include model files (~3GB), manual download required.**

- **Whisper Models**:
  - Download [faster-whisper-small.en](https://huggingface.co/Systran/faster-whisper-small.en)
  - Download [faster-whisper-medium.en](https://huggingface.co/Systran/faster-whisper-medium.en)
  - Place in `data/models/` directory

- **VAD Model**:
  - Download [silero-vad](https://github.com/snakers4/silero-vad)
  - Place in `data/vad/silero-vad-master/` directory

**Directory Structure Example:**
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

4. **Configure API Keys**

**Method 1: Use Environment Variables (Recommended)**
```bash
cp .env.example .env
# Edit .env file and fill in your API keys
```

**Method 2: Use Local Config File**
```bash
cp src/config.example.py src/config_local.py
# Edit config_local.py and fill in your API keys
```

**Required API Keys:**
- `DEEPSEEK_API_KEY` - For keyword generation (DeepSeek V3)
- `DOUBAO_API_KEY` - For content organization (Doubao Flash)

5. **Launch Application**

**Windows Users (Recommended):**
```bash
启动ClassAudio.bat
```

**General Method:**
```bash
python run.py
```

Browser will automatically open at `http://localhost:8000`.

### Usage Flow

1. **Set Classroom Topic** (Optional but Recommended)
   - Enter topic in top input box, e.g., "Quantum Computing", "Deep Learning"
   - Click "Set Topic", wait for LLM to generate professional vocabulary (~5-15 seconds)

2. **Start Recording**
   - Click "Start Recording" button
   - Speak into microphone
   - Real-time captions will display immediately

3. **View Results**
   - **Partial Captions**: Real-time preview (gray)
   - **Accurate Captions**: Final result (green, with quality metrics)
   - **Structured Notes**: Automatically categorized display on right side

---

## 📁 Project Structure

```
classaudio/
├── src/                        # Source code
│   ├── services/               # Core services
│   │   ├── audio_service.py    # Audio transcription service
│   │   └── llm_service.py      # LLM processing service
│   ├── api/                    # API interfaces
│   │   └── server.py           # FastAPI server
│   ├── agent/                  # LLM agent
│   │   ├── keywords.py         # Keyword generation
│   │   ├── llm.py              # LLM interface
│   │   └── prompt.py           # Prompt templates
│   ├── config.py               # Configuration file
│   └── config.example.py       # Config example
│
├── frontend/                   # Frontend interface
│   ├── index.html              # Main page
│   ├── app.js                  # Frontend logic
│   └── styles.css              # Style file
│
├── scripts/                    # Utility scripts
│   └── launcher.py             # Launcher
│
├── docs/                       # Documentation
│   ├── 快速启动指南.md
│   ├── 课堂主题功能说明.md
│   ├── 故障排查指南.md
│   └── 日志系统说明.md
│
├── data/                       # Data directory (Git ignored)
│   ├── models/                 # Whisper models (manual download)
│   ├── vad/                    # VAD model (manual download)
│   └── logs/                   # Runtime logs
│
├── .env.example                # Environment variables example
├── .gitignore                  # Git ignore config
├── requirements.txt            # Python dependencies
├── run.py                      # Entry point
└── README.md                   # This file
```

---

## 📚 Documentation

- [Quick Start Guide](docs/快速启动指南.md) - Detailed installation and configuration
- [Classroom Topic Feature](docs/课堂主题功能说明.md) - Smart professional vocabulary generation
- [Troubleshooting Guide](docs/故障排查指南.md) - Common problem solutions
- [Logging System Guide](docs/日志系统说明.md) - Log viewing and analysis
- [Project Architecture](PROJECT_STRUCTURE.md) - Complete technical documentation

---

## 🛠️ Utility Scripts

### Log Viewer
View system logs in real-time:
```bash
python view_logs.py
```

### Cache Cleanup
Clean Python bytecode cache:
```bash
clear_cache.bat  # Windows
# Or manually delete __pycache__ directories
```

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Submit Pull Request

---

## 📄 License

This project is licensed under [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - CUDA acceleration implementation
- [Silero-VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

---

## 📧 Contact

For questions or suggestions, please submit an [Issue](https://github.com/yourusername/classaudio/issues).

---

<p align="center">
  Made with ❤️ for better learning experience
</p>
