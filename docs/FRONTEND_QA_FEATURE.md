# 前端问答功能设计文档

## 🎨 设计方案

采用**右侧滑出式抽屉面板**设计，符合你的所有需求：
- ✅ 从右侧滑出，字幕和笔记内容占据大部分空间
- ✅ 保留所有历史问答记录
- ✅ 支持拖动调整面板宽度（300px ~ 800px）
- ✅ 点击触发按钮展开/收起

---

## 📐 布局结构

### 正常状态（问答面板收起）

```
┌──────────────────────────────────────────────────────┐
│  ClassAudio 导航栏                                    │
├──────────────────────────────────────────────────────┤
│  主题设置 + 控制按钮                                  │
├─────────────────────────┬────────────────────────────┤
│                         │                            │
│   实时字幕 (Partial)    │   结构化笔记 (LLM整理)     │
│                         │                            │
│   准确字幕 (Accurate)   │                            │
│                         │                            │
└─────────────────────────┴────────────────────────────┘
                                                      │💬│
                                                    触发按钮
```

### 展开状态（问答面板打开）

```
┌────────────────────────────────────────┬─────────────┐
│  ClassAudio 导航栏                      │             │
├────────────────────────────────────────┤   💬 问答   │
│  主题设置 + 控制按钮                    │             │
├──────────────────┬─────────────────────┤   ╔═══════  │
│                  │                     │ ║ │   [清空] [✕]
│  实时字幕        │   结构化笔记        │ ║ │         │
│  (被压缩)        │   (被压缩)          │ ║ │ 历史记录 │
│                  │                     │ ║ │         │
│  准确字幕        │                     │ ║ │ 问: xx? │
│  (被压缩)        │                     │ ║ │ 答: ... │
│                  │                     │   │         │
└──────────────────┴─────────────────────┤   │ [输入框]│
                                         └─────────────┘
                                         ↑ 可拖动边界
```

---

## 🎯 核心功能

### 1. 触发按钮（侧边栏）

**位置**: 固定在页面右侧中间
**样式**:
- 渐变紫色背景
- 垂直文字排列："💬 问答"
- Hover 效果：向左移动 5px

**交互**:
- 点击后展开问答面板
- 展开后自动隐藏按钮

### 2. 问答抽屉面板

**尺寸**:
- 默认宽度：400px
- 最小宽度：300px
- 最大宽度：800px
- 高度：100vh（全屏高度）

**结构**:
```
┌─────────────────────────────┐
│ [头部]                      │
│   💬 课堂问答   [🗑️] [✕]   │
├─────────────────────────────┤
│ [问答历史区 - 可滚动]       │
│                             │
│   问: 今天讲了什么？        │  ← 右对齐，紫色气泡
│                             │
│   答: 今天讲了...           │  ← 左对齐，灰色背景
│   11:30:25                  │
│                             │
│   问: 作业是什么？          │
│                             │
│   答: 正在思考... • • •    │  ← 加载状态
│                             │
├─────────────────────────────┤
│ [输入区]                    │
│  [输入框____________] [提问]│
│  💡 提示：基于课堂内容回答  │
└─────────────────────────────┘
```

### 3. 可拖动调整宽度

**调整柄**:
- 位于抽屉左边缘
- 宽度 8px
- Hover 时显示紫色
- 拖动时鼠标变为 `ew-resize`

**拖动逻辑**:
```javascript
// 鼠标按下 → 记录初始位置
// 鼠标移动 → 计算新宽度（限制在 300-800px）
// 鼠标释放 → 保存新宽度
```

### 4. 历史记录保留

**存储方式**:
```javascript
qaState.qaHistory = [
  {
    question: "今天讲了什么？",
    answer: "今天讲了Transformer架构...",
    loading: false,
    timestamp: "14:30:25"
  },
  // ...更多记录
]
```

**特点**:
- ✅ 所有问答记录保存在内存中
- ✅ 刷新页面后清空（未持久化）
- ✅ 支持手动清空按钮

---

## 🎨 视觉设计

### 颜色方案

```css
主色调：
  - 紫色渐变：#667eea → #764ba2
  - 问题气泡：紫色渐变
  - 回答气泡：#f7fafc（浅灰）

强调色：
  - 蓝色边框：#4299e1（知识点）
  - 成功绿色：#48bb78
  - 危险红色：#f56565
```

### 动画效果

**抽屉滑出动画**:
```css
transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
/* 平滑的缓动曲线 */
```

**问答条目出现动画**:
```css
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

**加载动画**（三个小点跳动）:
```css
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
```

---

## 💻 技术实现

### HTML 结构

```html
<!-- 触发按钮 -->
<div class="qa-trigger" id="qa-trigger">
  <span class="qa-trigger-icon">💬</span>
  <span class="qa-trigger-text">问答</span>
</div>

<!-- 抽屉面板 -->
<div class="qa-drawer" id="qa-drawer">
  <!-- 拖动调整柄 -->
  <div class="qa-resize-handle" id="qa-resize-handle"></div>

  <!-- 头部 -->
  <div class="qa-drawer-header">
    <div class="qa-drawer-title">💬 课堂问答</div>
    <div class="qa-drawer-actions">
      <button id="qa-clear-btn">🗑️</button>
      <button id="qa-close-btn">✕</button>
    </div>
  </div>

  <!-- 历史记录 -->
  <div class="qa-history" id="qa-history">
    <!-- 动态渲染问答条目 -->
  </div>

  <!-- 输入区 -->
  <div class="qa-input-container">
    <div class="qa-input-wrapper">
      <input id="qa-input" placeholder="输入你的问题..." />
      <button id="qa-submit-btn">➤ 提问</button>
    </div>
    <div class="qa-input-hint">
      💡 提示：AI 会基于当前课堂的转写内容回答问题
    </div>
  </div>
</div>
```

### JavaScript 核心函数

#### 1. 打开/关闭抽屉

```javascript
function openQADrawer() {
  qaState.isOpen = true;
  qaElements.drawer.classList.add('open');
  qaElements.trigger.classList.add('hidden');
  qaElements.mainContent.classList.add('qa-open');
  qaElements.mainContent.style.marginRight = `${qaState.drawerWidth}px`;

  // 聚焦输入框
  setTimeout(() => qaElements.input.focus(), 300);
}

function closeQADrawer() {
  qaState.isOpen = false;
  qaElements.drawer.classList.remove('open');
  qaElements.trigger.classList.remove('hidden');
  qaElements.mainContent.classList.remove('qa-open');
  qaElements.mainContent.style.marginRight = '0';
}
```

#### 2. 提交问题

```javascript
async function submitQuestion() {
  const question = qaElements.input.value.trim();

  // 添加到历史（显示加载状态）
  const qaItem = {
    question: question,
    answer: '',
    loading: true,
    timestamp: formatTime(),
  };
  qaState.qaHistory.push(qaItem);
  renderQAHistory();

  // 调用 API
  const response = await fetch(`${API_URL}/api/qa/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  const data = await response.json();

  // 更新答案
  qaItem.answer = data.answer;
  qaItem.loading = false;
  renderQAHistory();
}
```

#### 3. 拖动调整宽度

```javascript
function setupResizeHandle() {
  qaElements.resizeHandle.addEventListener('mousedown', (e) => {
    qaState.isResizing = true;
    startX = e.clientX;
    startWidth = qaState.drawerWidth;
  });

  document.addEventListener('mousemove', (e) => {
    if (!qaState.isResizing) return;

    const deltaX = startX - e.clientX;
    const newWidth = clamp(
      startWidth + deltaX,
      qaState.minWidth,
      qaState.maxWidth
    );

    qaState.drawerWidth = newWidth;
    qaElements.drawer.style.width = `${newWidth}px`;

    if (qaState.isOpen) {
      qaElements.mainContent.style.marginRight = `${newWidth}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    qaState.isResizing = false;
  });
}
```

---

## 📱 响应式设计

### 桌面端（> 768px）
- 抽屉宽度：300px ~ 800px
- 触发按钮：右侧中间，竖排文字
- 主内容区：动态调整 margin-right

### 移动端（≤ 768px）
- 抽屉宽度：100%（全屏覆盖）
- 触发按钮：右下角，横排文字
- 主内容区：不调整 margin
- 禁用拖动调整功能

```css
@media (max-width: 768px) {
  .qa-drawer {
    width: 100%;
  }

  .qa-trigger {
    bottom: 20px;
    right: 20px;
    top: auto;
    writing-mode: horizontal-tb;
    border-radius: 50px;
  }

  .qa-resize-handle {
    display: none;
  }
}
```

---

## 🔒 安全性

### XSS 防护

所有用户输入和 LLM 输出都经过 HTML 转义：

```javascript
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 使用
html += `<div class="qa-question">${escapeHtml(item.question)}</div>`;
html += `<div class="qa-answer">${escapeHtml(item.answer)}</div>`;
```

---

## 🎬 用户交互流程

### 完整使用流程

```
1. 用户看到右侧"💬 问答"触发按钮
   ↓
2. 点击按钮
   ↓
3. 抽屉从右侧滑出（400px 宽度）
   主内容区被压缩（margin-right: 400px）
   触发按钮隐藏
   输入框自动聚焦
   ↓
4. 用户输入问题："今天讲了什么？"
   ↓
5. 点击"提问"按钮（或按 Enter）
   ↓
6. 问题立即显示在历史区（右对齐紫色气泡）
   下方显示"正在思考... • • •"（加载动画）
   输入框禁用
   ↓
7. 后端 API 返回答案
   ↓
8. 答案替换加载动画（左对齐灰色背景）
   显示时间戳
   输入框恢复可用
   自动聚焦
   ↓
9. 用户可以继续提问
   或点击 [✕] 关闭抽屉
   ↓
10. 关闭后：
    - 抽屉滑回右侧隐藏
    - 主内容区恢复原宽度
    - 触发按钮重新显示
    - 历史记录保留在内存中
```

### 拖动调整宽度流程

```
1. 鼠标悬停在抽屉左边缘
   ↓
2. 调整柄变为紫色，鼠标变为 ↔️
   ↓
3. 按住鼠标左键
   ↓
4. 左右拖动
   - 向左拖：宽度增大（最大 800px）
   - 向右拖：宽度减小（最小 300px）
   ↓
5. 释放鼠标
   ↓
6. 宽度固定，主内容区自动适应
```

---

## 📊 状态管理

```javascript
const qaState = {
  isOpen: false,           // 抽屉是否打开
  qaHistory: [],           // 问答历史记录
  isAsking: false,         // 是否正在提问
  drawerWidth: 400,        // 当前宽度
  minWidth: 300,           // 最小宽度
  maxWidth: 800,           // 最大宽度
  isResizing: false,       // 是否正在拖动调整
};
```

---

## 🧪 测试场景

### 基础功能测试

1. **打开/关闭抽屉**
   - ✅ 点击触发按钮能打开
   - ✅ 点击 ✕ 按钮能关闭
   - ✅ 动画流畅（0.4s）

2. **提问功能**
   - ✅ 输入问题后点击"提问"
   - ✅ 显示加载动画
   - ✅ 获取答案后正确显示
   - ✅ 按 Enter 也能提交

3. **历史记录**
   - ✅ 问答记录正确显示
   - ✅ 滚动到最新记录
   - ✅ 点击"清空"按钮能清空

4. **拖动调整**
   - ✅ 能拖动调整宽度
   - ✅ 宽度限制在 300-800px
   - ✅ 主内容区自动适应

### 边界情况测试

1. **空输入**
   - ✅ 提示"请输入问题"

2. **重复提问**
   - ✅ 正在处理时禁用按钮

3. **API 错误**
   - ✅ 显示错误消息
   - ✅ 不中断使用

4. **移动端**
   - ✅ 全屏显示
   - ✅ 触发按钮位置正确

---

## 📝 TODO / 未来优化

### 可选增强功能

- [ ] 持久化问答历史（LocalStorage）
- [ ] 导出问答记录为 Markdown
- [ ] 问题快捷模板（常见问题）
- [ ] 答案支持 Markdown 渲染
- [ ] 语音输入问题
- [ ] 复制答案到剪贴板
- [ ] 点赞/踩答案反馈
- [ ] 搜索历史问答

---

## 🎓 使用提示

### 给用户的建议

1. **最佳提问时机**
   - 课堂进行一段时间后（有足够转写内容）
   - LLM 已处理至少 1-2 个批次

2. **问题示例**
   - ✅ "今天讲了哪些知识点？"
   - ✅ "作业的截止时间是什么时候？"
   - ✅ "能解释一下刚才提到的概念吗？"
   - ❌ "明天天气怎么样？"（超出范围）

3. **调整面板宽度**
   - 小屏幕用户：保持默认 400px
   - 大屏幕用户：可拖宽到 600-800px
   - 专注字幕时：收起抽屉

---

## 总结

✅ 已完成的功能：
1. 右侧滑出式抽屉设计
2. 保留所有历史问答记录
3. 拖动调整面板宽度
4. 平滑动画效果
5. 响应式适配
6. XSS 安全防护
7. 完整的前后端集成

这个设计完全满足你的需求，并且提供了良好的用户体验！🎉
