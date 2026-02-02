// ==================== 配置 ====================
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000',
  WS_URL: 'ws://localhost:8000/ws/captions',
  AUTO_REFRESH_INTERVAL: 5000, // 5秒
};

// ==================== 全局状态 ====================
const state = {
  ws: null,
  isConnected: false,
  isRecording: false,
  accurateCount: 0,
  notesCount: 0,
  autoRefreshTimer: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  reconnectTimer: null,
  lastPingTime: Date.now(),
  topicSet: false,
  currentTopic: null,
  accurateCaptions: [], // 用于持久化的字幕数组
};

// ==================== DOM 元素 ====================
const elements = {
  // 状态
  statusText: document.getElementById('status-text'),
  statusDot: document.getElementById('status-dot'),

  // 主题相关
  topicPanel: document.getElementById('topic-panel'),
  topicInput: document.getElementById('topic-input'),
  btnSetTopic: document.getElementById('btn-set-topic'),
  topicHint: document.getElementById('topic-hint'),

  // 按钮
  btnStart: document.getElementById('btn-start'),
  btnStop: document.getElementById('btn-stop'),
  btnRefresh: document.getElementById('btn-refresh'),
  btnClear: document.getElementById('btn-clear'),
  btnExport: document.getElementById('btn-export'),

  // 显示区域
  partialCaption: document.getElementById('partial-caption'),
  accurateCaptions: document.getElementById('accurate-captions'),
  structuredNotes: document.getElementById('structured-notes'),

  // 计数
  accurateCount: document.getElementById('accurate-count'),
  notesCount: document.getElementById('notes-count'),

  // 通知
  toastContainer: document.getElementById('toast-container'),
};

// ==================== 工具函数 ====================

// ==================== LocalStorage 持久化 ====================
const STORAGE_KEYS = {
  ACCURATE_CAPTIONS: 'classaudio_accurate_captions',
  QA_HISTORY: 'classaudio_qa_history',
  LLM_NOTES: 'classaudio_llm_notes',
  SESSION_ID: 'classaudio_session_id',
};

/**
 * 保存 Accurate 字幕到 localStorage
 */
function saveAccurateCaptions() {
  try {
    localStorage.setItem(STORAGE_KEYS.ACCURATE_CAPTIONS, JSON.stringify(state.accurateCaptions));
  } catch (error) {
    console.error('Failed to save accurate captions:', error);
  }
}

/**
 * 从 localStorage 加载 Accurate 字幕
 */
function loadAccurateCaptions() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.ACCURATE_CAPTIONS);
    if (saved) {
      state.accurateCaptions = JSON.parse(saved);
      renderAccurateCaptions();
    }
  } catch (error) {
    console.error('Failed to load accurate captions:', error);
    state.accurateCaptions = [];
  }
}

/**
 * 渲染所有 Accurate 字幕
 */
function renderAccurateCaptions() {
  if (state.accurateCaptions.length === 0) {
    elements.accurateCaptions.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📝</div>
        <div class="empty-text">暂无字幕记录</div>
      </div>
    `;
    state.accurateCount = 0;
    elements.accurateCount.textContent = '0 条';
    return;
  }

  // 清空容器
  elements.accurateCaptions.innerHTML = '';

  // 渲染所有字幕（最新的在上面）
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

/**
 * 保存问答历史到 localStorage
 */
function saveQAHistory() {
  try {
    localStorage.setItem(STORAGE_KEYS.QA_HISTORY, JSON.stringify(qaState.qaHistory));
  } catch (error) {
    console.error('Failed to save QA history:', error);
  }
}

/**
 * 从 localStorage 加载问答历史
 */
function loadQAHistory() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.QA_HISTORY);
    if (saved) {
      qaState.qaHistory = JSON.parse(saved);
      renderQAHistory();
    }
  } catch (error) {
    console.error('Failed to load QA history:', error);
    qaState.qaHistory = [];
  }
}

/**
 * 保存 LLM 笔记到 localStorage
 */
function saveLLMNotes(content) {
  try {
    localStorage.setItem(STORAGE_KEYS.LLM_NOTES, JSON.stringify(content));
  } catch (error) {
    console.error('Failed to save LLM notes:', error);
  }
}

/**
 * 从 localStorage 加载 LLM 笔记
 */
function loadLLMNotes() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.LLM_NOTES);
    if (saved) {
      const content = JSON.parse(saved);
      displayStructuredNotes(content);
      return content;
    }
  } catch (error) {
    console.error('Failed to load LLM notes:', error);
  }
  return null;
}

/**
 * 清除所有持久化数据
 */
function clearPersistedData() {
  localStorage.removeItem(STORAGE_KEYS.ACCURATE_CAPTIONS);
  localStorage.removeItem(STORAGE_KEYS.QA_HISTORY);
  localStorage.removeItem(STORAGE_KEYS.LLM_NOTES);
  state.accurateCaptions = [];
  qaState.qaHistory = [];
}

/**
 * 显示通知
 */
function showToast(title, message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️',
  };

  toast.innerHTML = `
    <div class="toast-icon">${icons[type]}</div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;

  elements.toastContainer.appendChild(toast);

  // 3秒后自动移除
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * 更新状态显示
 */
function updateStatus(text, status) {
  elements.statusText.textContent = text;
  elements.statusDot.className = 'status-dot';

  if (status === 'connected') {
    elements.statusDot.classList.add('connected');
  } else if (status === 'recording') {
    elements.statusDot.classList.add('recording');
  }
}

/**
 * 更新按钮状态
 */
function updateButtons(recording) {
  elements.btnStart.disabled = recording;
  elements.btnStop.disabled = !recording;
}

/**
 * 格式化时间
 */
function formatTime(date = new Date()) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

// ==================== WebSocket 管理 ====================

/**
 * 连接 WebSocket
 */
function connectWebSocket() {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    console.log('WebSocket already connected');
    return;
  }

  console.log('Connecting to WebSocket...');
  state.ws = new WebSocket(CONFIG.WS_URL);

  state.ws.onopen = () => {
    console.log('WebSocket connected');
    state.isConnected = true;
    state.reconnectAttempts = 0; // 重置重连计数器
    state.lastPingTime = Date.now(); // 重置心跳时间
    updateStatus('已连接', 'connected');
    showToast('连接成功', 'WebSocket 连接已建立', 'success');
  };

  state.ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  state.ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    showToast('连接错误', 'WebSocket 连接出错', 'error');
  };

  state.ws.onclose = (event) => {
    console.log('WebSocket disconnected', event.code, event.reason);
    state.isConnected = false;
    updateStatus('连接断开', 'disconnected');

    // 如果正在录音，尝试自动重连
    if (state.isRecording && state.reconnectAttempts < state.maxReconnectAttempts) {
      state.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, state.reconnectAttempts - 1), 10000); // 指数退避，最大 10 秒

      showToast('连接断开', `正在尝试重新连接... (${state.reconnectAttempts}/${state.maxReconnectAttempts})`, 'warning');

      state.reconnectTimer = setTimeout(() => {
        console.log(`Reconnect attempt ${state.reconnectAttempts}`);
        connectWebSocket();
      }, delay);
    } else if (state.reconnectAttempts >= state.maxReconnectAttempts) {
      showToast('连接失败', '多次重连失败，请检查后端服务或刷新页面', 'error');
      state.reconnectAttempts = 0;
    } else {
      showToast('连接断开', '请刷新页面或点击"开始录音"重新连接', 'warning');
    }
  };
}

/**
 * 断开 WebSocket
 */
function disconnectWebSocket() {
  if (state.ws) {
    state.ws.close();
    state.ws = null;
    state.isConnected = false;
  }
}

/**
 * 处理 WebSocket 消息
 */
function handleWebSocketMessage(data) {
  if (data.type === 'partial') {
    updatePartialCaption(data.text);
  } else if (data.type === 'accurate') {
    addAccurateCaption(data);
  } else if (data.type === 'ping') {
    // 收到心跳，更新时间
    state.lastPingTime = Date.now();
  }
}

// ==================== 字幕显示 ====================

/**
 * 更新 Partial 字幕
 */
function updatePartialCaption(text) {
  elements.partialCaption.innerHTML = text || '<div class="placeholder-text">等待语音输入...</div>';
}

/**
 * 添加 Accurate 字幕
 */
function addAccurateCaption(data) {
  // 添加到数组开头（最新的在前面）
  state.accurateCaptions.unshift({
    timestamp: data.timestamp,
    text: data.text
  });

  // 保存到 localStorage
  saveAccurateCaptions();

  // 移除空状态
  const emptyState = elements.accurateCaptions.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }

  // 创建字幕项
  const captionItem = document.createElement('div');
  captionItem.className = 'caption-item';
  captionItem.innerHTML = `
    <span class="caption-time">[${data.timestamp}]</span>
    <span class="caption-text">${data.text}</span>
  `;

  // 最新的在上面：使用 prepend 而不是 appendChild
  elements.accurateCaptions.prepend(captionItem);

  // 更新计数
  state.accurateCount++;
  elements.accurateCount.textContent = `${state.accurateCount} 条`;
}

// ==================== 结构化笔记 ====================

/**
 * 刷新结构化笔记
 */
async function refreshStructuredNotes() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/structured-content?latest=0`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    displayStructuredNotes(data.content);

  } catch (error) {
    console.error('Failed to refresh notes:', error);
    showToast('刷新失败', '无法获取结构化笔记', 'error');
  }
}

/**
 * 显示结构化笔记
 */
function displayStructuredNotes(content) {
  if (!content || content.length === 0) {
    elements.structuredNotes.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🤖</div>
        <div class="empty-text">等待 LLM 处理中...</div>
        <div class="empty-hint">至少需要 4 条准确字幕才会开始处理</div>
      </div>
    `;
    state.notesCount = 0;
    elements.notesCount.textContent = '0 批次';
    return;
  }

  // 检查内容是否真的变化了（避免闪烁）
  const currentContent = localStorage.getItem(STORAGE_KEYS.LLM_NOTES);
  const newContent = JSON.stringify(content);

  if (currentContent === newContent) {
    // 内容没变化，不更新 DOM
    return;
  }

  // 保存到 localStorage
  saveLLMNotes(content);

  let html = '';

  // 最新的在上面：反转数组顺序
  const reversedContent = [...content].reverse();

  reversedContent.forEach((item, index) => {
    const batchNumber = content.length - index;

    html += `<div class="note-batch">`;
    html += `
      <div class="batch-header">
        <div class="batch-title">批次 ${batchNumber}</div>
        <div class="batch-time">${formatTime()}</div>
      </div>
    `;

    // 课程安排
    if (item.coursework && item.coursework.length > 0) {
      html += `
        <div class="note-section">
          <div class="section-header">
            <span class="section-icon">📚</span>
            <span>课程安排</span>
          </div>
          <ul class="section-list coursework">
            ${item.coursework.map(c => `<li>${c}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // 知识点
    if (item.knowledge && item.knowledge.length > 0) {
      html += `
        <div class="note-section">
          <div class="section-header">
            <span class="section-icon">💡</span>
            <span>知识点</span>
          </div>
          <ul class="section-list knowledge">
            ${item.knowledge.map(k => `<li>${k}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // 问题
    if (item.question && item.question.length > 0) {
      html += `
        <div class="note-section">
          <div class="section-header">
            <span class="section-icon">❓</span>
            <span>问题</span>
          </div>
          <ul class="section-list question">
            ${item.question.map(q => `<li>${q}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    html += `</div>`;
  });

  elements.structuredNotes.innerHTML = html;

  state.notesCount = content.length;
  elements.notesCount.textContent = `${state.notesCount} 批次`;
}

// ==================== API 调用 ====================

/**
 * 设置课堂主题并生成专业词汇
 */
async function setCourseTopic() {
  const topic = elements.topicInput.value.trim();

  if (!topic) {
    showToast('输入错误', '请输入课堂主题', 'error');
    return;
  }

  // 禁用按钮，显示加载状态
  elements.btnSetTopic.disabled = true;
  const originalText = elements.btnSetTopic.querySelector('span:last-child').textContent;
  elements.btnSetTopic.querySelector('span:last-child').textContent = '生成中...';
  elements.topicHint.textContent = '正在生成专业词汇，请稍候...';
  elements.topicHint.style.color = '#666';

  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/keywords/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ topic })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // 更新状态
    state.topicSet = true;
    state.currentTopic = topic;

    // 更新 UI
    elements.topicInput.disabled = true;
    elements.btnSetTopic.querySelector('span:last-child').textContent = '已设置';
    elements.btnSetTopic.classList.remove('btn-topic');
    elements.btnSetTopic.classList.add('btn-success');
    elements.topicHint.textContent = `已设置主题：${topic}`;
    elements.topicHint.style.color = '#16a34a';

    // 根据录音状态显示不同提示
    if (state.isRecording) {
      showToast('主题已设置', `专业词汇已生成，将应用于下一句话`, 'success');
    } else {
      showToast('主题已设置', `专业词汇已生成（${data.prof_words.length} 字符）`, 'success');
    }

  } catch (error) {
    console.error('Failed to set topic:', error);
    showToast('设置失败', `无法生成专业词汇：${error.message}`, 'error');

    // 恢复按钮状态
    elements.btnSetTopic.disabled = false;
    elements.btnSetTopic.querySelector('span:last-child').textContent = originalText;
    elements.topicHint.textContent = '设置主题后，系统将自动生成相关专业词汇，提高转写准确度';
    elements.topicHint.style.color = '';
  }
}

/**
 * 开始录音
 */
async function startRecording() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/control/start`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    state.isRecording = true;
    updateButtons(true);
    updateStatus('录音中', 'recording');

    // 连接 WebSocket
    connectWebSocket();

    // 开启自动刷新
    startAutoRefresh();

    showToast('录音开始', '已开始捕获音频', 'success');

  } catch (error) {
    console.error('Failed to start recording:', error);
    showToast('启动失败', '无法连接到服务器，请确认服务已启动', 'error');
  }
}

/**
 * 停止录音
 */
async function stopRecording() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/control/stop`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    state.isRecording = false;
    updateButtons(false);
    updateStatus('已停止', 'connected');

    // 断开 WebSocket
    disconnectWebSocket();

    // 停止自动刷新
    stopAutoRefresh();

    // 最后刷新一次笔记
    await refreshStructuredNotes();

    showToast('录音停止', '已停止音频捕获', 'info');

  } catch (error) {
    console.error('Failed to stop recording:', error);
    showToast('停止失败', '操作失败', 'error');
  }
}

/**
 * 清空显示
 */
function clearDisplay() {
  // 清空 Partial
  updatePartialCaption('');

  // 清空 Accurate（包括持久化数据）
  state.accurateCaptions = [];
  saveAccurateCaptions();
  elements.accurateCaptions.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">📝</div>
      <div class="empty-text">暂无字幕记录</div>
    </div>
  `;
  state.accurateCount = 0;
  elements.accurateCount.textContent = '0 条';

  // 清空笔记（包括 localStorage）
  localStorage.removeItem(STORAGE_KEYS.LLM_NOTES);
  elements.structuredNotes.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">🤖</div>
      <div class="empty-text">等待 LLM 处理中...</div>
      <div class="empty-hint">至少需要 4 条准确字幕才会开始处理</div>
    </div>
  `;
  state.notesCount = 0;
  elements.notesCount.textContent = '0 批次';

  showToast('已清空', '显示内容已清空', 'success');
}

/**
 * 导出笔记
 */
async function exportNotes() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/structured-content?latest=0`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!data.content || data.content.length === 0) {
      showToast('导出失败', '没有可导出的内容', 'warning');
      return;
    }

    // 生成 Markdown
    let markdown = `# ClassAudio 课堂笔记\n\n`;
    markdown += `**导出时间**: ${new Date().toLocaleString()}\n\n`;
    markdown += `**总批次数**: ${data.content.length}\n\n`;
    markdown += `---\n\n`;

    data.content.forEach((item, index) => {
      markdown += `## 批次 ${index + 1}\n\n`;

      if (item.coursework && item.coursework.length > 0) {
        markdown += `### 📚 课程安排\n\n`;
        item.coursework.forEach(c => {
          markdown += `- ${c}\n`;
        });
        markdown += `\n`;
      }

      if (item.knowledge && item.knowledge.length > 0) {
        markdown += `### 💡 知识点\n\n`;
        item.knowledge.forEach(k => {
          markdown += `- ${k}\n`;
        });
        markdown += `\n`;
      }

      if (item.question && item.question.length > 0) {
        markdown += `### ❓ 问题\n\n`;
        item.question.forEach(q => {
          markdown += `- ${q}\n`;
        });
        markdown += `\n`;
      }

      markdown += `---\n\n`;
    });

    // 下载文件
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `classaudio-notes-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('导出成功', '笔记已保存为 Markdown 文件', 'success');

  } catch (error) {
    console.error('Failed to export notes:', error);
    showToast('导出失败', '无法导出笔记', 'error');
  }
}

// ==================== 自动刷新 ====================

function startAutoRefresh() {
  if (state.autoRefreshTimer) {
    clearInterval(state.autoRefreshTimer);
  }

  state.autoRefreshTimer = setInterval(() => {
    if (state.isRecording) {
      refreshStructuredNotes();

      // 检查心跳：如果超过 60 秒没收到 ping，认为连接可能已断
      const timeSinceLastPing = Date.now() - state.lastPingTime;
      if (timeSinceLastPing > 60000 && state.isConnected) {
        console.warn('No ping received for 60 seconds, connection may be stale');
        // 不主动断开，让 WebSocket 自己处理超时
      }
    }
  }, CONFIG.AUTO_REFRESH_INTERVAL);
}

function stopAutoRefresh() {
  if (state.autoRefreshTimer) {
    clearInterval(state.autoRefreshTimer);
    state.autoRefreshTimer = null;
  }
}

// ==================== 事件监听 ====================

function setupEventListeners() {
  // 设置主题
  elements.btnSetTopic.addEventListener('click', setCourseTopic);

  // 主题输入框回车键
  elements.topicInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      setCourseTopic();
    }
  });

  // 开始录音
  elements.btnStart.addEventListener('click', startRecording);

  // 停止录音
  elements.btnStop.addEventListener('click', stopRecording);

  // 刷新笔记
  elements.btnRefresh.addEventListener('click', refreshStructuredNotes);

  // 清空显示
  elements.btnClear.addEventListener('click', () => {
    if (confirm('确定要清空所有显示内容吗？')) {
      clearDisplay();
    }
  });

  // 导出笔记
  elements.btnExport.addEventListener('click', exportNotes);

  // 页面卸载时断开连接
  window.addEventListener('beforeunload', () => {
    disconnectWebSocket();
    stopAutoRefresh();
  });
}

// ==================== 初始化 ====================

function init() {
  console.log('ClassAudio Frontend Initialized');

  // 加载持久化数据
  loadAccurateCaptions();
  loadQAHistory();
  loadLLMNotes();

  // 设置事件监听
  setupEventListeners();

  // 初始化按钮状态
  updateButtons(false);

  // 检查服务器连接（会自动恢复录音状态）
  checkServerConnection();

  console.log('Loaded data from localStorage:', {
    accurateCaptions: state.accurateCaptions.length,
    qaHistory: qaState.qaHistory.length
  });
}

/**
 * 检查服务器连接
 */
async function checkServerConnection() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`);

    if (response.ok) {
      showToast('服务就绪', '后端服务连接正常', 'success');
      updateStatus('就绪', 'connected');

      // 检查录音状态并恢复
      await restoreRecordingState();
    } else {
      throw new Error('Server not ready');
    }
  } catch (error) {
    console.error('Server connection failed:', error);
    showToast('服务未启动', '请先运行 launcher.py 启动后端服务', 'warning');
    updateStatus('服务未启动', 'disconnected');
  }
}

/**
 * 从后端恢复录音状态
 */
async function restoreRecordingState() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/status`);

    if (!response.ok) {
      return;
    }

    const data = await response.json();

    // 检查是否是新 session（后端重启了）
    if (data.llm_service && data.llm_service.session_id) {
      const currentSessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
      const newSessionId = data.llm_service.session_id;

      if (currentSessionId !== newSessionId) {
        // 新 session，清空所有缓存
        console.log('New session detected, clearing all cached data');
        console.log(`Old session: ${currentSessionId}, New session: ${newSessionId}`);

        clearPersistedData();

        // 保存新 session ID
        localStorage.setItem(STORAGE_KEYS.SESSION_ID, newSessionId);

        // 刷新页面显示
        clearDisplay();

        showToast('新会话开始', '检测到服务重启，已清空上次数据', 'info');
      }
    }

    // 如果后端正在录音，恢复前端状态
    if (data.audio && data.audio.is_running) {
      state.isRecording = true;
      updateButtons(true);
      updateStatus('录音中', 'recording');

      // 重新连接 WebSocket
      connectWebSocket();

      // 开启自动刷新
      startAutoRefresh();

      showToast('状态已恢复', '检测到正在录音，已自动恢复连接', 'info');
    }
  } catch (error) {
    console.error('Failed to restore recording state:', error);
  }
}

// ==================== 问答面板功能 ====================

// 问答面板状态
const qaState = {
  isOpen: false,
  qaHistory: [], // 保留所有历史问答记录
  isAsking: false,
  drawerWidth: 400, // 默认宽度
  minWidth: 300,
  maxWidth: 800,
  isResizing: false,
};

// 问答面板DOM元素
const qaElements = {
  trigger: document.getElementById('qa-trigger'),
  drawer: document.getElementById('qa-drawer'),
  closeBtn: document.getElementById('qa-close-btn'),
  clearBtn: document.getElementById('qa-clear-btn'),
  collapseBtn: document.getElementById('qa-collapse-btn'),
  input: document.getElementById('qa-input'),
  submitBtn: document.getElementById('qa-submit-btn'),
  history: document.getElementById('qa-history'),
  resizeHandle: document.getElementById('qa-resize-handle'),
  mainContent: document.getElementById('main-content'),
};

/**
 * 打开问答面板
 */
function openQADrawer() {
  qaState.isOpen = true;
  qaElements.drawer.classList.add('open');
  qaElements.trigger.classList.add('hidden');
  qaElements.mainContent.classList.add('qa-open');

  // 更新主内容区的margin
  qaElements.mainContent.style.marginRight = `${qaState.drawerWidth}px`;

  // 聚焦输入框
  setTimeout(() => qaElements.input.focus(), 300);
}

/**
 * 关闭问答面板
 */
function closeQADrawer() {
  qaState.isOpen = false;
  qaElements.drawer.classList.remove('open');
  qaElements.trigger.classList.remove('hidden');
  qaElements.mainContent.classList.remove('qa-open');
  qaElements.mainContent.style.marginRight = '0';
}

/**
 * 清空问答历史
 */
function clearQAHistory() {
  if (qaState.qaHistory.length === 0) {
    showToast('无需清空', '没有问答记录', 'info');
    return;
  }

  if (confirm('确定要清空所有问答记录吗？')) {
    qaState.qaHistory = [];
    saveQAHistory(); // 保存到 localStorage
    renderQAHistory();
    showToast('已清空', '问答历史已清空', 'success');
  }
}

/**
 * 渲染问答历史
 */
function renderQAHistory() {
  if (qaState.qaHistory.length === 0) {
    qaElements.history.innerHTML = `
      <div class="qa-empty-state">
        <div class="qa-empty-icon">💭</div>
        <div class="qa-empty-text">还没有提问记录</div>
        <div class="qa-empty-hint">在下方输入框提问，AI 会基于课堂内容回答</div>
      </div>
    `;
    return;
  }

  let html = '';
  qaState.qaHistory.forEach(item => {
    html += `
      <div class="qa-item">
        <div class="qa-question">${escapeHtml(item.question)}</div>
        <div class="qa-answer ${item.loading ? 'loading' : ''}">${
          item.loading
            ? '<span>正在思考</span><span class="qa-loading-dots"><span></span><span></span><span></span></span>'
            : escapeHtml(item.answer)
        }</div>
        ${!item.loading ? `<div class="qa-timestamp">${item.timestamp}</div>` : ''}
      </div>
    `;
  });

  qaElements.history.innerHTML = html;

  // 滚动到底部
  qaElements.history.scrollTop = qaElements.history.scrollHeight;
}

/**
 * 提交问题
 */
async function submitQuestion() {
  const question = qaElements.input.value.trim();

  if (!question) {
    showToast('输入错误', '请输入问题', 'warning');
    return;
  }

  if (qaState.isAsking) {
    showToast('请稍候', '正在处理上一个问题', 'info');
    return;
  }

  // 添加问题到历史（显示加载状态）
  const qaItem = {
    question: question,
    answer: '',
    loading: true,
    timestamp: formatTime(),
  };
  qaState.qaHistory.push(qaItem);
  renderQAHistory();

  // 清空输入框并禁用
  qaElements.input.value = '';
  qaElements.input.disabled = true;
  qaElements.submitBtn.disabled = true;
  qaState.isAsking = true;

  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/qa/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // 更新历史记录
    qaItem.answer = data.answer;
    qaItem.loading = false;
    saveQAHistory(); // 保存到 localStorage
    renderQAHistory();

  } catch (error) {
    console.error('Failed to ask question:', error);

    // 显示错误消息
    qaItem.answer = '抱歉，问答服务暂时不可用。请稍后再试。';
    qaItem.loading = false;
    saveQAHistory(); // 保存到 localStorage
    renderQAHistory();

    showToast('提问失败', '无法获取回答', 'error');
  } finally {
    // 恢复输入框
    qaElements.input.disabled = false;
    qaElements.submitBtn.disabled = false;
    qaState.isAsking = false;
    qaElements.input.focus();
  }
}

/**
 * 拖动调整面板宽度
 */
function setupResizeHandle() {
  let startX = 0;
  let startWidth = 0;

  qaElements.resizeHandle.addEventListener('mousedown', (e) => {
    qaState.isResizing = true;
    startX = e.clientX;
    startWidth = qaState.drawerWidth;

    qaElements.resizeHandle.classList.add('active');
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';

    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!qaState.isResizing) return;

    const deltaX = startX - e.clientX;
    const newWidth = Math.max(
      qaState.minWidth,
      Math.min(qaState.maxWidth, startWidth + deltaX)
    );

    qaState.drawerWidth = newWidth;
    qaElements.drawer.style.width = `${newWidth}px`;

    if (qaState.isOpen) {
      qaElements.mainContent.style.marginRight = `${newWidth}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    if (qaState.isResizing) {
      qaState.isResizing = false;
      qaElements.resizeHandle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}

/**
 * HTML转义（防止XSS）
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 设置问答面板事件监听
 */
function setupQAEventListeners() {
  // 打开抽屉
  qaElements.trigger.addEventListener('click', openQADrawer);

  // 关闭抽屉
  qaElements.closeBtn.addEventListener('click', closeQADrawer);

  // 左侧收起按钮
  qaElements.collapseBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // 防止触发拖动
    closeQADrawer();
  });

  // 清空历史
  qaElements.clearBtn.addEventListener('click', clearQAHistory);

  // 提交问题
  qaElements.submitBtn.addEventListener('click', submitQuestion);

  // 输入框回车提交
  qaElements.input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitQuestion();
    }
  });

  // 设置拖动调整
  setupResizeHandle();
}

// ==================== 页面加载完成后初始化 ====================

// 页面加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    init();
    setupQAEventListeners();
  });
} else {
  init();
  setupQAEventListeners();
}
