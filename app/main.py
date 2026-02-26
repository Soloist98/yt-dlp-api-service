from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from app.api.router import router
from app.config import settings
from app.utils.logger import logger

app = FastAPI(
    title="yt-dlp API",
    description="API for downloading videos using yt-dlp",
    version="1.0.0"
)

# API 路由（添加 /api 前缀）
app.include_router(router, prefix="/api")

# 前端静态文件路径
FRONTEND_BUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "yt-dlp-api-front", "build")

# 如果前端构建目录存在，提供静态文件服务
if os.path.exists(FRONTEND_BUILD_PATH):
    # 静态资源（JS、CSS、图片等）
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_BUILD_PATH, "static")), name="static")

    # React Router 支持：所有非 API 路由返回 index.html
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API 路由已经被 router 处理，这里只处理前端路由
        if full_path.startswith("api/"):
            return {"error": "Not found"}

        # 检查是否是静态文件
        file_path = os.path.join(FRONTEND_BUILD_PATH, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # 其他所有路由返回 index.html（React Router）
        return FileResponse(os.path.join(FRONTEND_BUILD_PATH, "index.html"))


def start_api():
    """启动API服务器"""
    logger.info("Starting yt-dlp API server", extra={
        "host": settings.app_host,
        "port": settings.app_port,
        "database_type": settings.database_type,
        "database_url": settings.get_database_url(),
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "frontend_enabled": os.path.exists(FRONTEND_BUILD_PATH),
    })

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_config=None  # 禁用uvicorn默认日志，使用我们的日志系统
    )


if __name__ == "__main__":
    start_api()