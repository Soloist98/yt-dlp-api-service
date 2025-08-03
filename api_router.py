from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio
import os
import platform
from task_manager import State, Task
from downloader import download_video, get_video_info, list_available_formats

router = APIRouter()

state = State()


class DownloadRequest(BaseModel):
    url: str

    output_path: str = "./downloads" if platform.system() == "Windows" else "/mnt/nas/movie"
    format: str = "bestvideo+bestaudio/best"
    quiet: bool = False


class BatchDownloadRequest(BaseModel):
    tasks: list[DownloadRequest]

class BatchTaskQueryRequest(BaseModel):
    task_ids: list[str]

async def process_download_task(task_id: str, url: str, output_path: str, format: str, quiet: bool):
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: download_video(
                    url=url,
                    output_path=output_path,
                    format=format,
                    quiet=quiet,
                )
            )
        state.update_task(task_id, "completed", result=result)
    except Exception as e:
        state.update_task(task_id, "failed", error=str(e))


def create_or_get_task(request: DownloadRequest) -> str:
    # 特殊处理
    if "pornhub" in request.url:
        if not request.output_path.endswith("pornhub"):
            request.output_path = f"{request.output_path}/pornhub"

    # 从数据库查找已存在任务
    existing_task = state.task_exists(request.url, request.output_path, request.format)
    if existing_task:
        return existing_task.id

    task_id = state.add_task(request.url, request.output_path, request.format)
    asyncio.create_task(process_download_task(
        task_id=task_id,
        url=request.url,
        output_path=request.output_path,
        format=request.format,
        quiet=request.quiet
    ))
    return task_id


@router.post("/download", response_class=JSONResponse)
async def api_download_video(request: DownloadRequest):
    task_id = create_or_get_task(request)
    return {"status": "success", "task_id": task_id}


@router.post("/batch_download", response_class=JSONResponse)
async def batch_download(request: BatchDownloadRequest):
    task_ids = [create_or_get_task(task_req) for task_req in request.tasks]
    return {"status": "success", "task_ids": task_ids}


@router.get("/task/{task_id}", response_class=JSONResponse)
async def get_task_status(task_id: str):
    task = state.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    response = {
        "status": "success",
        "data": {
            "id": task.id,
            "url": task.url,
            "status": task.status
        }
    }
    if task.status == "completed" and task.result:
        response["data"]["result"] = task.result
    elif task.status == "failed" and task.error:
        response["data"]["error"] = task.error
    return response

@router.get("/tasks", response_class=JSONResponse)
async def list_all_tasks():
    tasks = state.list_tasks()
    return {"status": "success", "data": tasks}

@router.delete("/tasks", response_class=JSONResponse)
async def clear_all_tasks():
    """清除数据库中的所有任务"""
    success = state.clear_all_tasks()
    if success:
        return {"status": "success", "message": "All tasks have been cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear tasks")

@router.post("/batch_tasks", response_class=JSONResponse)
async def batch_get_tasks(request: BatchTaskQueryRequest):
    results = []
    all_finished = True
    for task_id in request.task_ids:
        task = state.get_task(task_id)
        if not task:
            results.append({
                "id": task_id,
                "status": "not_found"
            })
            continue
        task_info = {
            "id": task.id,
            "url": task.url,
            "status": task.status
        }
        if task.status == "completed" and task.result:
            task_info["result"] = task.result
        elif task.status == "failed" and task.error:
            task_info["error"] = task.error
        if task.status not in ("completed", "failed"):
            all_finished = False
        results.append(task_info)
    return {"status": "success", "data": results, "all_finished": all_finished}

@router.get("/info", response_class=JSONResponse)
async def api_get_video_info(url: str = Query(..., description="The URL of the video")):
    try:
        result = get_video_info(url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats", response_class=JSONResponse)
async def api_list_formats(url: str = Query(..., description="The URL of the video")):
    try:
        result = list_available_formats(url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{task_id}/file", response_class=FileResponse)
async def download_completed_video(task_id: str):
    task = state.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"Task is not completed yet. Current status: {task.status}")
    if not task.result:
        raise HTTPException(status_code=500, detail="Task completed but no result information available")
    try:
        filename = task.result.get("requested_downloads", [{}])[0].get("filename")
        if not filename:
            requested_filename = task.result.get("requested_filename")
            if requested_filename:
                filename = requested_filename
            else:
                title = task.result.get("title", "video")
                ext = task.result.get("ext", "mp4")
                filename = os.path.join(task.output_path, f"{title}.{ext}")
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail="Video file not found on server")
        file_basename = os.path.basename(filename)
        return FileResponse(
            path=filename,
            filename=file_basename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing video file: {str(e)}")

