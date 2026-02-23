from fastapi import FastAPI
import uvicorn
from api_router import router
from config import settings

app = FastAPI(
    title="yt-dlp API",
    description="API for downloading videos using yt-dlp",
    version="1.0.0"
)
app.include_router(router)


def start_api():
    """启动API服务器"""
    print(f"Starting yt-dlp API server on {settings.app_host}:{settings.app_port}...")
    print(f"Database type: {settings.database_type}")
    print(f"Database URL: {settings.get_database_url()}")
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)


if __name__ == "__main__":
    start_api()