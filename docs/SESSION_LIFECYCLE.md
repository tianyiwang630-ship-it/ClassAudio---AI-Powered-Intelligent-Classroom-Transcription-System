# 服务会话生命周期管理

## 📝 功能说明

实现了**服务生命周期**与**bat启动/关闭**绑定，确保每次启动服务都是全新开始。

---

## 🎯 核心概念

### 服务周期定义

```
一个服务周期 = 从启动 bat 到关闭 CMD
```

**特点**：
- ✅ 每次启动 bat（运行 `run.py`）创建新 session
- ✅ 自动清空浏览器缓存（localStorage）
- ✅ 创建新的 LLM content 文件
- ✅ 关闭 CMD 后，数据保存在文件中
- ✅ 下次启动又是全新开始

---

## 🔄 完整流程

### 第一次启动

```
用户打开 启动ClassAudio.bat
   ↓
运行 run.py
   ↓
后端服务启动
├─ 初始化音频服务
└─ 初始化 LLM 服务
   └─ 自动创建新 session: 20260118_110000_content.json
   ↓
后端打印：
   ✓ New session created: 20260118_110000
   ✓ Content will be saved to: data/logs/20260118_110000_content.json
   ↓
用户打开浏览器 http://localhost:3000
   ↓
前端检查 session ID
├─ localStorage 中没有旧 session
└─ 保存新 session ID: 20260118_110000
   ↓
前端显示：
   [info] 新会话开始
   [success] 服务就绪，后端服务连接正常
   ↓
用户开始使用（录音、转写、问答）
所有数据保存到 20260118_110000_content.json
```

### 关闭服务

```
用户关闭 CMD 窗口
   ↓
后端服务停止
   ↓
数据已保存在：
├─ data/logs/20260118_110000_content.json
└─ 浏览器 localStorage（临时缓存）
```

### 第二次启动（新服务周期）

```
用户再次打开 启动ClassAudio.bat
   ↓
运行 run.py
   ↓
后端服务启动
├─ 初始化音频服务
└─ 初始化 LLM 服务
   └─ 自动创建新 session: 20260118_140000_content.json ✨
   ↓
后端打印：
   ✓ New session created: 20260118_140000
   ✓ Content will be saved to: data/logs/20260118_140000_content.json
   ↓
用户打开浏览器（或刷新页面）
   ↓
前端检查 session ID
├─ localStorage 中有旧 session: 20260118_110000
└─ 后端返回新 session: 20260118_140000
   ↓
session ID 不匹配！
   ↓
前端自动清空所有缓存：
├─ 清空 Accurate 字幕
├─ 清空 LLM 笔记
├─ 清空问答历史
└─ 保存新 session ID: 20260118_140000
   ↓
前端显示：
   [info] 新会话开始，检测到服务重启，已清空上次数据
   [success] 服务就绪
   ↓
界面恢复到初始状态（空白）
所有新数据保存到 20260118_140000_content.json
```

---

## 💻 技术实现

### 后端：启动时创建 Session

**文件**：`src/api/server.py`

```python
@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    # ... 初始化音频服务 ...

    # 初始化 LLM 服务
    try:
        print("\n[2/2] Initializing LLM Service...")
        llm_service = LLMProcessorService()

        # 启动时立即创建新 session（清空上一次的数据）
        llm_service.start_session()
        llm_service.start_async_processing()

        print(f"      ✓ New session created: {llm_service.session_start_time}")
        print(f"      ✓ Content will be saved to: {llm_service.save_path}")
        print("      ✓ LLM Service initialized successfully!")
    except Exception as e:
        print(f"      ✗ Failed to initialize LLM Service: {e}")
```

**关键点**：
- 在 `startup_event` 中调用 `llm_service.start_session()`
- 每次后端启动都会创建新 session
- Session ID 格式：`YYYYMMDD_HHMMSS`（例如：`20260118_140000`）

---

### 后端：API 返回 Session ID

**文件**：`src/api/server.py`

```python
@app.get("/api/status", response_model=StatsResponse)
async def get_status():
    """获取服务状态"""
    audio_stats = {
        "is_running": audio_service.is_running if audio_service else False,
        # ...
    }

    llm_stats = llm_service.get_stats() if llm_service else {}

    # 添加 session_id 到 llm_stats
    if llm_service:
        llm_stats["session_id"] = llm_service.session_start_time

    return StatsResponse(
        audio_service=audio_stats,
        llm_service=llm_stats
    )
```

**返回数据示例**：
```json
{
  "audio_service": {
    "is_running": false
  },
  "llm_service": {
    "buffer_size": 0,
    "processed_batches": 0,
    "session_id": "20260118_140000"
  }
}
```

---

### 前端：检测 Session 变化

**文件**：`frontend/app.js`

```javascript
async function restoreRecordingState() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/status`);
    const data = await response.json();

    // 检查是否是新 session（后端重启了）
    if (data.llm_service && data.llm_service.session_id) {
      const currentSessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
      const newSessionId = data.llm_service.session_id;

      if (currentSessionId !== newSessionId) {
        // 新 session，清空所有缓存
        console.log('New session detected, clearing all cached data');
        console.log(`Old session: ${currentSessionId}, New session: ${newSessionId}`);

        clearPersistedData();  // 清空 localStorage

        // 保存新 session ID
        localStorage.setItem(STORAGE_KEYS.SESSION_ID, newSessionId);

        // 刷新页面显示
        clearDisplay();

        showToast('新会话开始', '检测到服务重启，已清空上次数据', 'info');
      }
    }

    // ... 其他恢复逻辑 ...
  } catch (error) {
    console.error('Failed to restore recording state:', error);
  }
}
```

**工作原理**：
1. 前端启动时调用 `/api/status` 获取 session ID
2. 与 localStorage 中保存的 session ID 比较
3. 如果不同，说明后端重启了，清空所有缓存
4. 保存新 session ID

---

## 📊 数据存储位置

### 后端文件存储

```
data/logs/
├── 20260118_110000_content.json  ← 第一次服务周期
├── 20260118_140000_content.json  ← 第二次服务周期
└── 20260118_160000_content.json  ← 第三次服务周期
```

**特点**：
- 每次启动创建新文件
- 文件名包含启动时间
- 关闭服务后文件永久保存

### 前端 localStorage

```javascript
localStorage:
├── classaudio_session_id: "20260118_140000"     ← 当前 session ID
├── classaudio_accurate_captions: [...]           ← 字幕缓存
├── classaudio_llm_notes: [...]                   ← 笔记缓存
└── classaudio_qa_history: [...]                  ← 问答缓存
```

**特点**：
- 临时缓存，提升用户体验
- session 变化时自动清空
- 浏览器刷新不影响

---

## 🎬 用户体验场景

### 场景 1：正常使用

```
1. 启动 bat
   ↓
2. 打开浏览器
   显示："新会话开始"
   ↓
3. 开始录音，产生字幕和笔记
   ↓
4. 关闭浏览器（数据在 localStorage）
   ↓
5. 重新打开浏览器
   数据自动恢复（session ID 相同）✅
   ↓
6. 继续使用
   ↓
7. 关闭 CMD
   服务结束
```

### 场景 2：服务重启

```
1. 启动 bat（第一次）
   session: 20260118_110000
   ↓
2. 使用服务，产生一些数据
   ↓
3. 关闭 CMD
   数据保存到 20260118_110000_content.json
   ↓
4. 再次启动 bat（第二次）
   session: 20260118_140000  ← 新 session
   ↓
5. 打开浏览器
   检测到 session 变化
   自动清空 localStorage ✅
   显示："新会话开始，检测到服务重启，已清空上次数据"
   ↓
6. 界面恢复到初始状态
   准备开始新的服务周期
```

### 场景 3：浏览器刷新（服务未重启）

```
1. 服务正在运行
   session: 20260118_110000
   ↓
2. 用户刷新浏览器
   ↓
3. 前端检查 session ID
   localStorage: 20260118_110000
   后端返回:    20260118_110000
   ↓
4. session ID 相同
   从 localStorage 恢复数据 ✅
   不清空缓存
   ↓
5. 用户看到之前的所有数据
```

---

## 🔍 关键代码变更

### 后端变更

1. **修改 `src/api/server.py`**：

   - 在 `startup_event` 中调用 `llm_service.start_session()`
   - 在 `/api/status` 中返回 `session_id`

2. **修改 `/api/control/start`**：

   - 检查 `audio_service.is_running`
   - 已在录音时不重复创建 session

### 前端变更

1. **修改 `frontend/app.js`**：

   - 添加 session ID 检测逻辑
   - session 变化时自动清空缓存
   - 显示"新会话开始"提示

---

## 📱 测试场景

### 测试 1：首次启动

**步骤**：
1. 关闭所有浏览器
2. 清空 `data/logs/` 目录
3. 启动 bat
4. 打开浏览器

**预期结果**：
- ✅ 后端打印：`New session created: YYYYMMDD_HHMMSS`
- ✅ 浏览器显示："新会话开始"
- ✅ 界面为空（无旧数据）

### 测试 2：服务重启

**步骤**：
1. 启动 bat，使用服务，产生一些数据
2. 关闭 CMD
3. 再次启动 bat
4. 刷新浏览器（或重新打开）

**预期结果**：
- ✅ 后端创建新 session 文件
- ✅ 浏览器显示："新会话开始，检测到服务重启，已清空上次数据"
- ✅ 界面清空，显示为初始状态
- ✅ console 打印：`New session detected`

### 测试 3：浏览器刷新（服务未重启）

**步骤**：
1. 启动 bat，使用服务，产生一些数据
2. 不关闭 CMD
3. 刷新浏览器

**预期结果**：
- ✅ 后端不创建新 session
- ✅ 浏览器显示："服务就绪"（不显示"新会话开始"）
- ✅ 所有数据从 localStorage 恢复
- ✅ console 不打印 `New session detected`

### 测试 4：数据文件验证

**步骤**：
1. 启动 bat（第一次），使用服务
2. 关闭 CMD
3. 查看 `data/logs/` 目录，记录文件名
4. 启动 bat（第二次），使用服务
5. 关闭 CMD
6. 再次查看 `data/logs/` 目录

**预期结果**：
- ✅ 有两个不同的 session 文件
- ✅ 文件名包含不同的时间戳
- ✅ 每个文件包含对应周期的完整数据

---

## 🎓 使用建议

### 最佳实践

1. **一次课堂一个服务周期**
   - 开始上课时启动 bat
   - 整节课期间不要关闭 CMD
   - 下课时关闭 CMD

2. **数据管理**
   - 每个服务周期的数据自动保存到独立文件
   - 文件名包含时间，方便区分
   - 定期清理 `data/logs/` 旧文件

3. **浏览器使用**
   - 可以随时刷新浏览器
   - 可以关闭后重新打开
   - 服务未重启时，数据自动恢复

### 注意事项

⚠️ **关闭 CMD = 结束服务周期**
- 关闭 CMD 后，下次启动会创建新 session
- 旧数据会被清空（但保存在文件中）

⚠️ **刷新浏览器 ≠ 重启服务**
- 只要 CMD 没关闭，刷新浏览器不影响
- 数据从 localStorage 自动恢复

⚠️ **多个浏览器标签页**
- session ID 在 localStorage 中共享
- 所有标签页会同时检测到 session 变化

---

## 🎉 总结

### 已实现的功能

1. ✅ **服务周期绑定**
   - 启动 bat = 创建新 session
   - 关闭 CMD = 结束服务周期

2. ✅ **自动清空缓存**
   - 检测到新 session
   - 自动清空 localStorage
   - 界面恢复初始状态

3. ✅ **独立数据文件**
   - 每个周期独立文件
   - 文件名包含时间戳
   - 便于管理和查阅

4. ✅ **用户友好提示**
   - "新会话开始"提示
   - Console 日志详细
   - 状态清晰可见

### 技术亮点

- 💡 使用 session ID 跟踪服务周期
- 💡 前后端协同检测 session 变化
- 💡 自动化缓存管理，无需手动操作
- 💡 数据持久化到文件，安全可靠

### 用户体验提升

- 🎯 **服务周期清晰**：启动 bat = 新开始
- 🎯 **数据不混乱**：每次服务独立文件
- 🎯 **操作简单**：自动清空，无需手动
- 🎯 **提示明确**："新会话开始"易懂

---

**实现日期**：2026-01-18
**涉及文件**：
- `src/api/server.py`（启动时创建 session，API 返回 session ID）
- `frontend/app.js`（检测 session 变化，自动清空缓存）

所有功能已完成并可立即使用！🎊
