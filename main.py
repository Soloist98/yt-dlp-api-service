from fastapi import FastAPI
import uvicorn
from api_router import router
from config import settings
from logger import logger

app = FastAPI(
    title="yt-dlp API",
    description="API for downloading videos using yt-dlp",
    version="1.0.0"
)
app.include_router(router)


def start_api():
    """启动API服务器"""
    logger.info("Starting yt-dlp API server", extra={
        "host": settings.app_host,
        "port": settings.app_port,
        "database_type": settings.database_type,
        "database_url": settings.get_database_url(),
        "log_level": settings.log_level,
        "log_format": settings.log_format,
    })

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_config=None  # 禁用uvicorn默认日志，使用我们的日志系统
    )


if __name__ == "__main__":
    start_api()