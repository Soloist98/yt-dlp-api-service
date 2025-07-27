import os
import yt_dlp
from typing import Dict, Any, List
from task_manager import NormalizeString

def download_video(url: str, output_path: str = "./downloads", format: str = "best", quiet: bool = False) -> Dict[str, Any]:
    os.makedirs(output_path, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(output_path, NormalizeString(format) + '-%(title)s.%(ext)s'),
        'quiet': quiet,
        'no_warnings': quiet,
        'format': format,
        'no_abort_on_error': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.sanitize_info(info)

def get_video_info(url: str, quiet: bool = False) -> Dict[str, Any]:
    ydl_opts = {
        'quiet': quiet,
        'no_warnings': quiet,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.sanitize_info(info)

def list_available_formats(url: str) -> List[Dict[str, Any]]:
    info = get_video_info(url)
    if not info:
        return []
    return info.get('formats', []) 