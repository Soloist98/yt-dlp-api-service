from fastapi import FastAPI
import uvicorn
from api_router import router

app = FastAPI(title="yt-dlp API", description="API for downloading videos using yt-dlp")
app.include_router(router)

def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("Starting yt-dlp API server...")
    start_api()