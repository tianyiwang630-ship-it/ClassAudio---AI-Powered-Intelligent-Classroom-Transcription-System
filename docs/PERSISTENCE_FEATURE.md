# 数据持久化功能说明

## 📝 功能概述

实现了浏览器刷新后自动恢复数据的功能，用户可以在刷新页面后继续使用转写服务，所有之前的字幕和问答记录都会保留。

---

## 🎯 功能特性

### ✅ 刷新后会恢复的内容

1. **Accurate 字幕历史记录**
   - 所有准确字幕的完整历史
   - 包括时间戳和文本内容
   - 按照最新在上的顺序显示

2. **问答历史记录**
   - 所有提问和回答的对话记录
   - 包括问题、答案和时间戳
   - 完整保留对话上下文

3. **LLM 结构化笔记**
   - 自动从后端 API 获取
   - 显示本次会话的所有批次笔记
   - 包括课程安排、知识点、问题

4. **录音状态**
   - 如果后端正在录音，前端自动恢复为录音状态
   - 自动重新连接 WebSocket
   - 按钮状态自动同步

### ❌ 刷新后不会恢复的内容

1. **Partial 字幕**
   - 实时字幕是临时内容，刷新后清空
   - 因为 Partial 会不断变化，没有持久化价值

---

## 🔧 技术实现

### 存储方式：混合方案

| 数据类型 | 存储方式 | 原因 |
|---------|---------|------|
| **Accurate 字幕** | `localStorage` | 简单快速，浏览器本地存储 |
| **问答历史** | `localStorage` | 简单快速，浏览器本地存储 |
| **LLM 笔记** | 后端 API | 从 `data/logs/*.json` 文件读取 |
| **录音状态** | 后端 API | 从 `/api/status` 接口获取 |

### LocalStorage 键名

```javascript
const STORAGE_KEYS = {
  ACCURATE_CAPTIONS: 'classaudio_accurate_captions',
  QA_HISTORY: 'classaudio_qa_history',
  SESSION_ID: 'classaudio_session_id',
};
```

---

## 💻 核心代码实现

### 1. 保存 Accurate 字幕

```javascript
function saveAccurateCaptions() {
  try {
    localStorage.setItem(
      STORAGE_KEYS.ACCURATE_CAPTIONS,
      JSON.stringify(state.accurateCaptions)
    );
  } catch (error) {
    console.error('Failed to save accurate captions:', error);
  }
}
```

**调用时机**：
- 每次收到新的 Accurate 字幕时（`addAccurateCaption()`）
- 用户点击"清空显示"时

### 2. 加载 Accurate 字幕

```javascript
function loadAccurateCaptions() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.ACCURATE_CAPTIONS);
    if (saved) {
      state.accurateCaptions = JSON.parse(saved);
      renderAccurateCaptions(); // 渲染到页面
    }
  } catch (error) {
    console.error('Failed to load accurate captions:', error);
    state.accurateCaptions = [];
  }
}
```

**调用时机**：
- 页面初始化时（`init()` 函数）

### 3. 渲染 Accurate 字幕

```javascript
function renderAccurateCaptions() {
  if (state.accurateCaptions.length === 0) {
    // 显示空状态
    elements.accurateCaptions.innerHTML = `...`;
    return;
  }

  elements.accurateCaptions.innerHTML = '';

  // 渲染所有字幕（数组已经是最新在前）
  state.accurateCaptions.forEach(caption => {
    const captionItem = document.createElement('div');
    captionItem.className = 'caption-item';
    captionItem.innerHTML = `
      <span class="caption-time">[${caption.timestamp}]</span>
      <span class="caption-text">${caption.text}</span>
    `;
    elements.accurateCaptions.appendChild(captionItem);
  });

  state.accurateCount = state.accurateCaptions.length;
  elements.accurateCount.textContent = `${state.accurateCount} 条`;
}
```

### 4. 保存问答历史

```javascript
function saveQAHistory() {
  try {
    localStorage.setItem(
      STORAGE_KEYS.QA_HISTORY,
      JSON.stringify(qaState.qaHistory)
    );
  } catch (error) {
    console.error('Failed to save QA history:', error);
  }
}
```

**调用时机**：
- 用户提问并收到回答后（`submitQuestion()`）
- 用户点击"清空历史"后

### 5. 加载问答历史

```javascript
function loadQAHistory() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.QA_HISTORY);
    if (saved) {
      qaState.qaHistory = JSON.parse(saved);
      renderQAHistory(); // 渲染到问答面板
    }
  } catch (error) {
    console.error('Failed to load QA history:', error);
    qaState.qaHistory = [];
  }
}
```

**调用时机**：
- 页面初始化时（`init()` 函数）

### 6. 恢复录音状态

```javascript
async function restoreRecordingState() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/status`);

    if (!response.ok) {
      return;
    }

    const data = await response.json();

    // 如果后端正在录音，恢复前端状态
    if (data.audio && data.audio.is_running) {
      state.isRecording = true;
      updateButtons(true);           // 禁用"开始"按钮，启用"停止"按钮
      updateStatus('录音中', 'recording');

      // 重新连接 WebSocket
      connectWebSocket();

      // 开启自动刷新（定时获取 LLM 笔记）
      startAutoRefresh();

      showToast('状态已恢复', '检测到正在录音，已自动恢复连接', 'info');
    }
  } catch (error) {
    console.error('Failed to restore recording state:', error);
  }
}
```

**调用时机**：
- 页面初始化，检查服务器连接后（`checkServerConnection()`）

### 7. 初始化流程

```javascript
function init() {
  console.log('ClassAudio Frontend Initialized');

  // 1. 加载持久化数据
  loadAccurateCaptions();  // 从 localStorage 加载字幕
  loadQAHistory();          // 从 localStorage 加载问答

  // 2. 设置事件监听
  setupEventListeners();

  // 3. 初始化按钮状态
  updateButtons(false);

  // 4. 检查服务器连接
  //    - 如果后端在录音，自动恢复录音状态
  //    - 自动刷新 LLM 笔记
  checkServerConnection();

  console.log('Loaded data from localStorage:', {
    accurateCaptions: state.accurateCaptions.length,
    qaHistory: qaState.qaHistory.length
  });
}
```

---

## 📊 数据存储格式

### Accurate 字幕格式

```json
[
  {
    "timestamp": "14:25:30",
    "text": "今天我们学习 Transformer 架构的核心概念"
  },
  {
    "timestamp": "14:25:35",
    "text": "自注意力机制是 Transformer 的关键"
  }
]
```

**特点**：
- 数组顺序：最新的在前面（`unshift` 添加）
- 渲染时直接按数组顺序显示

### 问答历史格式

```json
[
  {
    "question": "今天的作业是什么？",
    "answer": "根据课堂内容，今天的作业是...",
    "loading": false,
    "timestamp": "14:30:15"
  },
  {
    "question": "什么是自注意力机制？",
    "answer": "自注意力机制是...",
    "loading": false,
    "timestamp": "14:32:20"
  }
]
```

**特点**：
- `loading`: 是否正在加载（刷新后会自动变为 `false`）
- `timestamp`: 提问时间

---

## 🎬 用户体验流程

### 场景 1：正常使用后刷新

```
1. 用户开始录音
   ↓
2. 系统产生多条 Accurate 字幕
   每条字幕自动保存到 localStorage
   ↓
3. 用户提问并获得回答
   问答记录自动保存到 localStorage
   ↓
4. 用户刷新浏览器（F5 或 Ctrl+R）
   ↓
5. 页面重新加载
   - 从 localStorage 恢复所有字幕 ✅
   - 从 localStorage 恢复问答历史 ✅
   - 从后端 API 获取 LLM 笔记 ✅
   - 从后端 API 获取录音状态 ✅
   ↓
6. 用户看到之前的所有内容 🎉
   继续使用转写服务
```

### 场景 2：后端正在录音时刷新

```
1. 后端正在录音中
   ↓
2. 用户刷新浏览器
   ↓
3. 前端检测到后端 is_running = true
   ↓
4. 自动执行以下操作：
   - 恢复"录音中"状态 ✅
   - 启用"停止录音"按钮 ✅
   - 重新连接 WebSocket ✅
   - 开启自动刷新（定时获取 LLM 笔记） ✅
   - 显示提示："状态已恢复" ✅
   ↓
5. 用户可以继续操作
   - 点击"停止录音"
   - 查看实时字幕
   - 查看问答历史
```

### 场景 3：用户清空显示

```
1. 用户点击"清空显示"按钮
   ↓
2. 确认对话框：确定要清空吗？
   ↓
3. 清空以下内容：
   - Partial 字幕
   - Accurate 字幕（同时清空 localStorage）
   - LLM 笔记
   ↓
4. 问答历史不受影响（需单独清空）
```

---

## 🔍 关键优化点

### 1. 避免重复渲染

**问题**：每次添加新字幕时，如果重新渲染整个列表会很慢。

**解决方案**：
- 新字幕到来时：只创建新的 DOM 元素并 `prepend`
- 刷新页面时：才使用 `renderAccurateCaptions()` 批量渲染

```javascript
// 添加新字幕：只创建一个 DOM 元素
function addAccurateCaption(data) {
  state.accurateCaptions.unshift(data); // 添加到数组
  saveAccurateCaptions();               // 保存到 localStorage

  const captionItem = document.createElement('div');
  // ... 创建 DOM
  elements.accurateCaptions.prepend(captionItem); // 只添加新元素
}

// 恢复数据：批量渲染
function renderAccurateCaptions() {
  elements.accurateCaptions.innerHTML = ''; // 清空
  state.accurateCaptions.forEach(caption => {
    // ... 创建所有 DOM
  });
}
```

### 2. 错误处理

所有 localStorage 操作都包裹在 `try-catch` 中：

```javascript
function saveAccurateCaptions() {
  try {
    localStorage.setItem(STORAGE_KEYS.ACCURATE_CAPTIONS, JSON.stringify(state.accurateCaptions));
  } catch (error) {
    console.error('Failed to save accurate captions:', error);
    // 不中断用户操作，静默失败
  }
}
```

**可能的错误**：
- `QuotaExceededError`: localStorage 空间不足（通常 5-10MB）
- `SecurityError`: 隐私模式下可能禁用 localStorage

### 3. 数据量限制

**问题**：长时间录音会产生大量字幕，可能超出 localStorage 容量。

**当前方案**：无限制存储

**未来优化建议**：
- 限制最多保存 1000 条字幕
- 超过后删除最旧的字幕
- 或者提供"归档"功能，保存到文件

---

## 🧪 测试场景

### 测试 1：Accurate 字幕持久化

**步骤**：
1. 开始录音，说几句话，产生 5-10 条 Accurate 字幕
2. 刷新浏览器（F5）
3. 观察字幕区域

**预期结果**：
- ✅ 所有字幕都显示出来
- ✅ 顺序正确（最新在上）
- ✅ 计数正确（显示"10 条"）

### 测试 2：问答历史持久化

**步骤**：
1. 打开问答面板
2. 提问 2-3 个问题并获得回答
3. 刷新浏览器
4. 再次打开问答面板

**预期结果**：
- ✅ 所有问答记录都显示
- ✅ 问题和答案都完整
- ✅ 时间戳正确

### 测试 3：录音状态恢复

**步骤**：
1. 开始录音（后端正在录音）
2. 刷新浏览器
3. 观察按钮状态和提示

**预期结果**：
- ✅ 状态显示"录音中"
- ✅ "开始录音"按钮禁用
- ✅ "停止录音"按钮启用
- ✅ WebSocket 自动连接
- ✅ 显示提示："状态已恢复"

### 测试 4：清空显示

**步骤**：
1. 有一些字幕和问答记录
2. 点击"清空显示"按钮
3. 确认清空
4. 刷新浏览器

**预期结果**：
- ✅ 字幕已清空，刷新后仍然是空的
- ✅ 问答历史仍然保留（不受影响）
- ✅ LLM 笔记已清空

### 测试 5：清空问答历史

**步骤**：
1. 有一些问答记录
2. 打开问答面板，点击"清空历史"（🗑️ 按钮）
3. 确认清空
4. 刷新浏览器

**预期结果**：
- ✅ 问答历史已清空，刷新后仍然是空的
- ✅ Accurate 字幕不受影响

### 测试 6：跨会话恢复

**步骤**：
1. 开始录音，产生一些字幕
2. 停止录音
3. 关闭浏览器标签页
4. 重新打开页面

**预期结果**：
- ✅ 之前的字幕仍然显示
- ✅ 问答历史仍然显示
- ✅ 状态为"就绪"（不是"录音中"）

---

## 📱 浏览器兼容性

### LocalStorage 支持

| 浏览器 | 支持情况 | 容量限制 |
|-------|---------|---------|
| Chrome | ✅ | 5-10 MB |
| Firefox | ✅ | 5-10 MB |
| Safari | ✅ | 5 MB |
| Edge | ✅ | 5-10 MB |

**注意事项**：
- 隐私模式下可能禁用 localStorage
- 用户清除浏览器数据会删除 localStorage
- 不同域名的数据相互隔离

---

## 🎓 使用建议

### 最佳实践

1. **定期清空数据**
   - 长时间使用后，点击"清空显示"释放空间
   - 避免 localStorage 容量不足

2. **导出重要笔记**
   - 使用"导出笔记"功能保存到本地文件
   - LocalStorage 可能被清除，文件更安全

3. **多设备使用**
   - LocalStorage 只在当前浏览器有效
   - 换设备或浏览器后数据不会同步
   - 如需跨设备，使用"导出笔记"功能

### 数据安全

- ✅ **自动保存**：每条字幕和问答都实时保存
- ✅ **刷新安全**：意外刷新不会丢失数据
- ⚠️ **清除浏览器数据会删除 localStorage**
- ⚠️ **隐私模式下可能无法使用**

---

## 🔧 技术细节

### LocalStorage API

```javascript
// 保存数据（字符串）
localStorage.setItem('key', 'value');

// 保存对象（需要 JSON.stringify）
localStorage.setItem('key', JSON.stringify(object));

// 读取数据
const value = localStorage.getItem('key');

// 读取对象（需要 JSON.parse）
const object = JSON.parse(localStorage.getItem('key'));

// 删除数据
localStorage.removeItem('key');

// 清空所有数据
localStorage.clear();
```

### 容量检测

```javascript
function getLocalStorageSize() {
  let total = 0;
  for (let key in localStorage) {
    if (localStorage.hasOwnProperty(key)) {
      total += localStorage[key].length + key.length;
    }
  }
  return (total / 1024).toFixed(2) + ' KB';
}
```

---

## 🎉 总结

### 已实现的功能

1. ✅ **Accurate 字幕持久化**
   - 使用 localStorage 存储
   - 刷新后自动恢复
   - 最新在上的顺序

2. ✅ **问答历史持久化**
   - 使用 localStorage 存储
   - 刷新后自动恢复
   - 完整保留对话上下文

3. ✅ **LLM 笔记自动加载**
   - 从后端 API 获取
   - 刷新后自动加载本次会话的笔记

4. ✅ **录音状态自动恢复**
   - 从后端 API 获取状态
   - 如果后端在录音，前端自动恢复
   - WebSocket 自动重连

### 用户体验提升

- 🎯 **无缝体验**：刷新后所有数据都在
- 🎯 **自动恢复**：录音状态自动同步
- 🎯 **数据安全**：实时保存，不怕意外刷新
- 🎯 **简单易用**：用户无需手动操作

### 技术亮点

- 💡 混合存储方案：LocalStorage + 后端 API
- 💡 自动持久化：每次操作都实时保存
- 💡 错误处理：所有 localStorage 操作都有 try-catch
- 💡 性能优化：增量更新 DOM，避免重复渲染

---

**实现日期**：2026-01-18
**涉及文件**：
- `frontend/app.js`（持久化逻辑、状态恢复）

所有功能已完成并可立即使用！🎉
