# ClassAudio 新功能说明

## 1. 基于时间戳的会话文件保存

### 功能说明
每次用户开始转写时，系统会自动创建一个基于开始时间的新文件来保存 LLM 处理结果。这样每堂课的转写内容都会保存在独立的文件中。

### 文件命名格式
```
data/logs/YYYYMMDD_HHMMSS_content.json
```

**示例**:
- `20260118_143025_content.json` - 2026年1月18日 14:30:25 开始的会话
- `20260119_091500_content.json` - 2026年1月19日 09:15:00 开始的会话

### 技术实现

#### 后端变更

**LLM Service ([src/services/llm_service.py](../src/services/llm_service.py))**:
- 添加 `start_session()` 方法，在开始转写时生成时间戳文件名
- 修改 `save_to_file()` 方法，使用会话专属的文件路径
- 添加会话状态跟踪：`session_start_time` 和 `save_path`

**API 端点 ([src/api/server.py](../src/api/server.py))**:
- 修改 `/api/control/start` 端点，在启动音频捕获前调用 `llm_service.start_session()`

### 使用方式

1. **通过 API 启动转写**:
```bash
curl -X POST http://localhost:8000/api/control/start
```

响应示例:
```json
{
  "status": "started",
  "message": "Audio capture started successfully. Session: 20260118_143025"
}
```

2. **文件自动保存**:
   - 每处理完 4 条准确字幕，内容会自动保存到该会话的文件中
   - 文件位置: `data/logs/<timestamp>_content.json`

3. **停止转写**:
```bash
curl -X POST http://localhost:8000/api/control/stop
```

---

## 2. 基于转写内容的问答功能

### 功能说明
用户可以对当前会话的转写内容进行提问，LLM 会基于课堂内容回答问题。

### 技术实现

#### 提示词格式
系统会将用户问题和转写内容按照以下格式封装：

```xml
<user_query>用户的问题</user_query>

<class_content>
=== Batch 1 ===
【课程安排】
- 作业内容...

【知识点】
- 知识点1...
- 知识点2...

【问题】
- 课堂问题...

=== Batch 2 ===
...
</class_content>

请基于上述课堂内容回答用户的问题。如果课堂内容中没有相关信息，请明确告知用户。
```

#### LLM Service 方法

**新增方法**:
1. `get_content_as_text()` - 将结构化内容转换为纯文本
2. `answer_question(user_input: str)` - 调用 DeepSeek V3 回答问题

### API 端点

**端点**: `POST /api/qa/ask`

**请求格式**:
```json
{
  "question": "今天讲了什么知识点？"
}
```

**响应格式**:
```json
{
  "question": "今天讲了什么知识点？",
  "answer": "今天课堂主要讲了以下知识点：\n1. Transformer 架构的基本原理\n2. 自注意力机制的计算方法\n3. ..."
}
```

### 使用示例

#### 1. 使用 curl
```bash
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "今天的作业是什么？"}'
```

#### 2. 使用 Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/qa/ask",
    json={"question": "能总结一下今天的知识点吗？"}
)

result = response.json()
print(f"问题: {result['question']}")
print(f"回答: {result['answer']}")
```

#### 3. 使用 JavaScript (前端)
```javascript
async function askQuestion(question) {
    const response = await fetch('http://localhost:8000/api/qa/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question })
    });

    const result = await response.json();
    console.log('问题:', result.question);
    console.log('回答:', result.answer);
    return result;
}

// 使用示例
askQuestion('今天讲的主要内容是什么？');
```

### 问答示例场景

1. **查询作业信息**:
   - 问题: "今天的作业截止时间是什么时候？"
   - 系统会从 `coursework` 类别中查找相关信息

2. **复习知识点**:
   - 问题: "能解释一下 Transformer 的注意力机制吗？"
   - 系统会从 `knowledge` 类别中提取相关内容

3. **回顾课堂问题**:
   - 问题: "今天课上提了哪些问题？"
   - 系统会从 `question` 类别中汇总

### 注意事项

1. **内容依赖**:
   - 问答功能依赖当前会话的转写内容
   - 如果还没有转写内容，会返回提示信息

2. **内容来源**:
   - 问答只基于当前会话（当前文件）的内容
   - 不会跨会话查询历史课堂内容

3. **LLM 限制**:
   - 使用 DeepSeek V3 模型
   - 受模型上下文长度限制（长课程可能需要优化）

---

## 3. 完整的工作流程

### 典型使用场景

```bash
# 1. 启动服务器
python run.py

# 2. 开始新的转写会话
curl -X POST http://localhost:8000/api/control/start

# 3. 系统自动创建会话文件
# 文件: data/logs/20260118_143025_content.json

# 4. 音频转写进行中...
# - 每 4 条准确字幕触发 LLM 处理
# - 处理结果自动保存到会话文件

# 5. 课堂中随时提问
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "刚才讲的公式是什么？"}'

# 6. 停止转写
curl -X POST http://localhost:8000/api/control/stop

# 7. 查看保存的内容
cat data/logs/20260118_143025_content.json
```

### 文件结构

转写会话后的文件结构：
```
data/
└── logs/
    ├── 20260118_143025_content.json  # 第一堂课
    ├── 20260118_153000_content.json  # 第二堂课
    ├── 20260119_091500_content.json  # 第三堂课
    └── captions.txt                   # 所有会话的字幕汇总
```

---

## 4. API 端点总览

### 新增端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/qa/ask` | POST | 基于转写内容回答问题 |

### 修改端点

| 端点 | 方法 | 变更 |
|------|------|------|
| `/api/control/start` | POST | 新增会话初始化逻辑 |
| `/api/status` | GET | 新增会话信息返回 |

### 所有端点列表

```bash
# 查看所有端点
curl http://localhost:8000/

# 响应:
{
  "message": "ClassAudio API is running!",
  "version": "1.0.0",
  "endpoints": {
    "websocket": "/ws/captions",
    "start": "/api/control/start",
    "stop": "/api/control/stop",
    "status": "/api/status",
    "content": "/api/structured-content",
    "generate_keywords": "/api/keywords/generate",
    "set_keywords": "/api/keywords/set",
    "ask_question": "/api/qa/ask"  // 新增
  }
}
```

---

## 5. 错误处理

### 问答功能错误

1. **没有转写内容**:
```json
{
  "question": "...",
  "answer": "抱歉，当前还没有转写内容。请先开始转写。"
}
```

2. **LLM 调用失败**:
```json
{
  "question": "...",
  "answer": "回答问题时出错: <错误详情>"
}
```

3. **服务未初始化**:
```json
{
  "detail": "LLM service not initialized"
}
```

---

## 6. 前端集成建议

### 添加问答界面

在前端 ([frontend/app.js](../frontend/app.js)) 中添加：

```javascript
// 问答功能
async function askQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();

    if (!question) {
        alert('请输入问题');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/qa/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        const result = await response.json();

        // 显示回答
        displayAnswer(result.question, result.answer);

        // 清空输入框
        questionInput.value = '';
    } catch (error) {
        console.error('问答失败:', error);
        alert('问答失败，请稍后重试');
    }
}

function displayAnswer(question, answer) {
    const qaContainer = document.getElementById('qaContainer');

    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item';
    qaItem.innerHTML = `
        <div class="question"><strong>问:</strong> ${question}</div>
        <div class="answer"><strong>答:</strong> ${answer}</div>
    `;

    qaContainer.appendChild(qaItem);
}
```

### HTML 添加

```html
<div class="qa-section">
    <h3>课堂问答</h3>
    <div id="qaContainer" class="qa-list"></div>
    <div class="qa-input">
        <input type="text" id="questionInput" placeholder="输入你的问题...">
        <button onclick="askQuestion()">提问</button>
    </div>
</div>
```

---

## 7. 测试

### 测试会话保存

```bash
# 1. 启动转写
curl -X POST http://localhost:8000/api/control/start

# 2. 等待一段时间（让系统处理一些转写）

# 3. 检查文件是否创建
ls -la data/logs/*_content.json

# 4. 查看内容
cat data/logs/最新文件.json
```

### 测试问答功能

```bash
# 提问测试
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "测试问题"}'
```

---

## 8. 配置说明

### 相关配置项

在 [src/config.py](../src/config.py) 中：

```python
# LLM 处理配置
LLM_CHUNK_SIZE = 4  # 每 4 条字幕触发一次 LLM 处理

# 日志目录（会话文件保存位置）
LOGS_DIR = "data/logs"
```

### 数据持久化

- **会话文件**: `data/logs/<timestamp>_content.json`
- **字幕文件**: `data/logs/captions.txt`
- **服务日志**: `logs/*.log`

---

## 总结

新功能提供了：
1. ✅ 每堂课独立的转写文件（基于时间戳命名）
2. ✅ 基于课堂内容的智能问答
3. ✅ 完整的 API 支持
4. ✅ 易于集成到前端

使用这些功能，学生可以：
- 自动保存每堂课的笔记
- 随时回顾课堂内容
- 通过问答快速查找信息
