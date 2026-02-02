"""
FastAPI Server for ClassAudio
提供 WebSocket 和 HTTP API 接口
"""
import asyncio
import json
import sys
import queue
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.services.audio_service import AudioTranscriptionService, CaptionOutput
from src.services.llm_service import LLMProcessorService
from src.agent.keywords import generate_prof_words

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass


# ====== FastAPI 应用 ======
app = FastAPI(
    title="ClassAudio API",
    description="实时课堂转写和智能笔记 API",
    version="1.0.0"
)

# CORS 配置（允许前端跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== 全局服务实例 ======
audio_service: AudioTranscriptionService = None
llm_service: LLMProcessorService = None


# ====== 请求/响应模型 ======
class StatusResponse(BaseModel):
    status: str
    message: str


class StatsResponse(BaseModel):
    audio_service: Dict[str, Any]
    llm_service: Dict[str, Any]


class TopicRequest(BaseModel):
    topic: str


class ProfWordsResponse(BaseModel):
    prof_words: str
    topic: str


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str


# ====== 生命周期事件 ======
@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    global audio_service, llm_service

    print("=" * 60)
    print("ClassAudio Backend Starting...")
    print("=" * 60)

    # 初始化音频服务
    try:
        print("\n[1/2] Initializing Audio Service...")
        audio_service = AudioTranscriptionService()
        print("      Loading Whisper models (this may take a few minutes)...")
        audio_service.initialize()
        print("      ✓ Audio Service initialized successfully!")
    except Exception as e:
        print(f"      ✗ Failed to initialize Audio Service: {e}")
        print("      WARNING: Audio transcription will not work!")
        print("      Please check:")
        print("        - Whisper models are downloaded")
        print("        - VAD models are available")
        print("        - CUDA is available (if using GPU)")
        import traceback
        traceback.print_exc()
        audio_service = None

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
        print("      WARNING: Content structuring will not work!")
        import traceback
        traceback.print_exc()
        llm_service = None

    # 设置音频服务的回调：将 accurate 字幕传递给 LLM 服务
    if audio_service and llm_service:
        def on_accurate_caption(caption: CaptionOutput):
            llm_service.add_transcript(caption.text)

        audio_service.set_accurate_callback(on_accurate_caption)
        print("\n      ✓ Services connected!")

    print("\n" + "=" * 60)
    if audio_service and llm_service:
        print("All services initialized successfully!")
    else:
        print("WARNING: Some services failed to initialize!")
        print("Server will start but functionality may be limited.")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global audio_service, llm_service

    print("Shutting down services...")

    if audio_service:
        audio_service.stop_capture()

    if llm_service:
        llm_service.stop_async_processing()

    print("Services stopped!")


# ====== HTTP API ======
@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
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
            "ask_question": "/api/qa/ask"
        }
    }


@app.get("/api/status", response_model=StatsResponse)
async def get_status():
    """获取服务状态"""
    audio_stats = {
        "is_running": audio_service.is_running if audio_service else False,
        "partial_queue_size": audio_service.partial_output_q.qsize() if audio_service else 0,
        "accurate_queue_size": audio_service.accurate_output_q.qsize() if audio_service else 0,
    }

    llm_stats = llm_service.get_stats() if llm_service else {}
    # 添加 session_id 到 llm_stats
    if llm_service:
        llm_stats["session_id"] = llm_service.session_start_time

    return StatsResponse(
        audio_service=audio_stats,
        llm_service=llm_stats
    )


@app.post("/api/control/start", response_model=StatusResponse)
async def start_recording():
    """开始录音和转写"""
    if not audio_service:
        raise HTTPException(status_code=500, detail="Audio service not initialized")

    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    try:
        # 只有在未录音时才启动新的 LLM 会话
        # 如果已经在录音中（例如前端刷新后重连），则不创建新 session
        if not audio_service.is_running:
            # 启动新的 LLM 会话（生成时间戳文件名）
            llm_service.start_session()

            # 启动音频捕获
            audio_service.start_capture()

            return StatusResponse(
                status="started",
                message=f"Audio capture started successfully. Session: {llm_service.session_start_time}"
            )
        else:
            # 已经在录音中，返回当前会话信息
            return StatusResponse(
                status="already_running",
                message=f"Audio capture is already running. Session: {llm_service.session_start_time}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")


@app.post("/api/control/stop", response_model=StatusResponse)
async def stop_recording():
    """停止录音和转写"""
    if not audio_service:
        raise HTTPException(status_code=500, detail="Audio service not initialized")

    try:
        audio_service.stop_capture()
        return StatusResponse(status="stopped", message="Audio capture stopped successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")


@app.post("/api/keywords/generate", response_model=ProfWordsResponse)
async def generate_keywords(request: TopicRequest):
    """
    根据课堂主题生成专业词汇提示词

    Args:
        request: 包含课堂主题的请求

    Returns:
        生成的专业词汇提示词
    """
    try:
        # 使用 LLM 生成专业词汇
        prof_words = await asyncio.get_event_loop().run_in_executor(
            None,
            generate_prof_words,
            request.topic
        )

        # 自动设置到 audio_service
        if audio_service:
            audio_service.set_prof_words(prof_words)

        return ProfWordsResponse(
            prof_words=prof_words,
            topic=request.topic
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate keywords: {str(e)}")


@app.post("/api/keywords/set", response_model=StatusResponse)
async def set_keywords(request: ProfWordsResponse):
    """
    手动设置专业词汇提示词

    Args:
        request: 包含专业词汇的请求
    """
    if not audio_service:
        raise HTTPException(status_code=500, detail="Audio service not initialized")

    try:
        audio_service.set_prof_words(request.prof_words)
        return StatusResponse(status="success", message="Prof words updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set keywords: {str(e)}")


@app.get("/api/structured-content")
async def get_structured_content(latest: int = 0):
    """
    获取 LLM 整理的结构化内容

    Args:
        latest: 返回最新的 N 条，0 表示返回全部
    """
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    if latest > 0:
        content = llm_service.get_latest_content(n=latest)
    else:
        content = llm_service.get_all_content()

    return JSONResponse(content={
        "total": len(llm_service.get_all_content()),
        "returned": len(content),
        "content": content
    })


@app.post("/api/structured-content/clear", response_model=StatusResponse)
async def clear_structured_content():
    """清空 LLM 服务的所有数据"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    llm_service.clear()
    return StatusResponse(status="cleared", message="LLM service data cleared")


@app.post("/api/qa/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    基于转写内容回答用户问题

    Args:
        request: 包含用户问题的请求

    Returns:
        LLM 的回答
    """
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    try:
        # 在后台线程中调用 LLM（避免阻塞）
        answer = await asyncio.get_event_loop().run_in_executor(
            None,
            llm_service.answer_question,
            request.question
        )

        return AnswerResponse(
            question=request.question,
            answer=answer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


# ====== WebSocket API ======
@app.websocket("/ws/captions")
async def websocket_captions(websocket: WebSocket):
    """
    WebSocket 端点：实时推送字幕
    发送格式：
    {
        "type": "partial" | "accurate",
        "text": "字幕内容",
        "timestamp": "HH:MM:SS",
        "no_speech_prob": 0.1,  // 仅 accurate
        "avg_logprob": -0.5     // 仅 accurate
    }
    """
    await websocket.accept()
    print("WebSocket client connected")

    try:
        # 心跳任务：每 30 秒发送一次 ping，保持连接活跃
        async def send_heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": ""
                    })
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                    break

        # 启动三个异步任务：partial, accurate, heartbeat
        async def send_partial():
            while True:
                try:
                    # 非阻塞获取 partial 字幕
                    caption = await asyncio.get_event_loop().run_in_executor(
                        None,
                        audio_service.get_partial_caption,
                        True,  # block
                        1.0    # timeout
                    )

                    await websocket.send_json({
                        "type": caption.type,
                        "text": caption.text,
                        "timestamp": caption.timestamp
                    })

                except queue.Empty:
                    # 队列为空（没有数据）是正常的，继续等待
                    await asyncio.sleep(0.1)
                    continue
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error sending partial: {e}")
                    break

        async def send_accurate():
            while True:
                try:
                    # 非阻塞获取 accurate 字幕
                    caption = await asyncio.get_event_loop().run_in_executor(
                        None,
                        audio_service.get_accurate_caption,
                        True,  # block
                        1.0    # timeout
                    )

                    await websocket.send_json({
                        "type": caption.type,
                        "text": caption.text,
                        "timestamp": caption.timestamp,
                        "no_speech_prob": caption.no_speech_prob,
                        "avg_logprob": caption.avg_logprob
                    })

                except queue.Empty:
                    # 队列为空（没有数据）是正常的，继续等待
                    await asyncio.sleep(0.1)
                    continue
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error sending accurate: {e}")
                    break

        # 并发运行三个任务
        await asyncio.gather(
            send_partial(),
            send_accurate(),
            send_heartbeat()
        )

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ====== 健康检查 ======
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "audio_service": "initialized" if audio_service else "not initialized",
        "llm_service": "initialized" if llm_service else "not initialized"
    }


# ====== 运行服务器 ======
if __name__ == "__main__":
    import uvicorn

    # 运行服务器
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境设为 False
        log_level="info"
    )
