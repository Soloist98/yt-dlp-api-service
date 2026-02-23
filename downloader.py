import os
import yt_dlp
from typing import Dict, Any, List
from task_manager import NormalizeString
from logger import logger


def download_video(url: str, output_path: str = "./downloads", format: str = "best", quiet: bool = False) -> Dict[
    str, Any]:
    """下载视频"""
    os.makedirs(output_path, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'quiet': quiet,
        'no_warnings': quiet,
        'format': format,
        'no_abort_on_error': True,
    }

    logger.info("Starting video download", extra={
        "url": url,
        "output_path": output_path,
        "format": format
    })
    logger.debug("YTDLP VERSION ============== ", extra={"version": yt_dlp.version.__version__})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            result = ydl.sanitize_info(info)
            logger.info("Video download completed", extra={
                "url": url,
                "title": result.get("title", "unknown")
            })
            return result
    except Exception as e:
        logger.error("Video download failed", extra={
            "url": url,
            "error": str(e)
        })
        raise


def get_video_info(url: str, quiet: bool = False) -> Dict[str, Any]:
    """获取视频信息"""
    ydl_opts = {
        'quiet': quiet,
        'no_warnings': quiet,
        'skip_download': True,
    }

    logger.debug("Fetching video info", extra={"url": url})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            result = ydl.sanitize_info(info)
            logger.debug("Video info fetched successfully", extra={
                "url": url,
                "title": result.get("title", "unknown")
            })
            return result
    except Exception as e:
        logger.error("Failed to fetch video info", extra={
            "url": url,
            "error": str(e)
        })
        raise


def list_available_formats(url: str) -> List[Dict[str, Any]]:
    """列出可用的视频格式"""
    logger.debug("Listing available formats", extra={"url": url})

    try:
        info = get_video_info(url)
        if not info:
            return []
        formats = info.get('formats', [])
        logger.debug("Formats listed successfully", extra={
            "url": url,
            "format_count": len(formats)
        })
        return formats
    except Exception as e:
        logger.error("Failed to list formats", extra={
            "url": url,
            "error": str(e)
        })
        raise
