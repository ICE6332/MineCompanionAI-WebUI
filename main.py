from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from api import websocket, monitor_ws, stats
from api.routes import llm
from api.middleware import SecurityHeadersMiddleware
from api.monitor_ws import register_monitor_subscriptions
from api.health import router as health_router
from core.logging_config import setup_logging
from config.settings import settings
from core.monitor.event_bus import EventBus
from core.monitor.metrics_collector import MetricsCollector
from core.monitor.connection_manager import ConnectionManager
from core.llm.service import LLMService
from core.storage.memory import MemoryCacheStorage
from core.storage.redis import RedisCacheStorage
from core.memory.conversation_context import ConversationContext


logger = setup_logging(level=os.getenv("LOG_LEVEL", "INFO"), log_file=os.getenv("LOG_FILE"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 初始化共享资源
    cache_storage = (
        RedisCacheStorage(settings.redis_url) if settings.storage_backend == "redis" else MemoryCacheStorage()
    )
    app.state.cache_storage = cache_storage
    app.state.event_bus = EventBus(history_size=settings.event_history_size)
    app.state.metrics = MetricsCollector()
    app.state.connection_manager = ConnectionManager()
    app.state.llm_service = LLMService(cache_storage=cache_storage)
    app.state.conversation_context = ConversationContext()

    logger.info("存储后端: %s", settings.storage_backend)
    # 注册监控事件订阅，将事件广播到前端监控页面
    register_monitor_subscriptions(app.state.event_bus)
    yield

    # Shutdown: 清理资源
    logger.info("开始清理资源...")

    # 1. 先关闭所有 WebSocket 连接
    connection_manager = getattr(app.state, "connection_manager", None)
    if connection_manager is not None:
        try:
            await connection_manager.close_all()
        except Exception as exc:  # noqa: BLE001
            logger.warning("关闭 WebSocket 连接失败: %s", exc)

    # 2. 关闭缓存存储
    if hasattr(cache_storage, "close"):
        try:
            await cache_storage.close()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.warning("关闭缓存存储失败: %s", exc)

    logger.info("资源清理完成")


app = FastAPI(
    title="MineCompanionAI-WebUI",
    version="0.5.0-beta",
    description="AI Companion Control Panel & Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加安全头部中间件
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(monitor_ws.router, tags=["Monitor"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(llm.router)
app.include_router(health_router)


@app.get("/health", include_in_schema=False)
@app.get("/health/", include_in_schema=False)
async def root_health_check():
    return {"status": "ok", "version": app.version}


@app.get("/api/health")
@app.get("/api/health/")
async def health_check():
    return {"status": "ok", "version": app.version}


# 静态文件目录配置
STATIC_DIR = Path(__file__).parent / "static" / "dist"

if STATIC_DIR.exists():
    # 生产模式：提供编译后的前端
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """返回编译后的前端 index.html"""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        # 如果 index.html 不存在，跳转到 API 文档
        return RedirectResponse(url="/docs")

    # 挂载静态资源目录（CSS, JS, 字体等）
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    logger.info("✅ 生产模式：静态文件服务已启用 (路径: %s)", STATIC_DIR)
else:
    # 开发模式：前端由 Vite 开发服务器提供，根路径跳转到 API 文档
    @app.get("/", include_in_schema=False)
    async def dev_mode_redirect():
        """开发模式：跳转到 API 文档"""
        return RedirectResponse(url="/docs")
    logger.info("⚠️ 开发模式：未找到静态文件目录，根路径跳转到 /docs")


if __name__ == "__main__":
    import asyncio
    import socket

    # 禁用 reload 避免子进程残留，由自定义 socket 控制端口复用
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
        access_log=False,
        timeout_keep_alive=5,
        limit_concurrency=100,
    )
    server = uvicorn.Server(config)

    def create_reusable_socket() -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                logger.warning("SO_REUSEPORT 不可用，系统可能未提供该选项")
        sock.bind((config.host or "0.0.0.0", int(config.port)))
        sock.listen(config.backlog)
        sock.setblocking(False)
        return sock

    async def serve() -> None:
        sock = create_reusable_socket()
        try:
            await server.serve(sockets=[sock])
        finally:
            sock.close()

    asyncio.run(serve())
