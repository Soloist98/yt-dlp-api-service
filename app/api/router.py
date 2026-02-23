from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio
import httpx
from app.core.task_manager import State, Task
from app.core.downloader import download_video
from app.config import settings
from app.utils.logger import logger

router = APIRouter()

state = State()

# 使用配置的线程池大小创建全局线程池
executor = ThreadPoolExecutor(max_workers=settings.thread_pool_size)

class BatchTaskQueryRequest(BaseModel):
    task_ids: list[str]

class DownloadRequest(BaseModel):
    url: str
    output_path: str = settings.default_download_path
    format: str = "bestvideo+bestaudio/best"
    quiet: bool = False


class BatchDownloadRequest(BaseModel):
    tasks: list[DownloadRequest]


async def process_download_task(task_id: str, url: str, output_path: str, format: str, quiet: bool):
    result = None
    try:
        logger.info("Starting download task", extra={
            "task_id": task_id,
            "url": url,
            "output_path": output_path,
            "format": format
        })

        loop = asyncio.get_event_loop()
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

        logger.info("Download task completed successfully", extra={
            "task_id": task_id,
            "url": url
        })
    except Exception as e:
        state.update_task(task_id, "failed", result=result, error=str(e))
        logger.error("Download task failed", extra={
            "task_id": task_id,
            "url": url,
            "error": str(e)
        })


def create_or_get_task(request: DownloadRequest) -> str:
    # 使用配置化的路径映射处理特殊站点
    request.output_path = settings.get_output_path_for_url(
        request.url,
        request.output_path
    )

    # 从数据库查找已存在任务（只根据URL判断）
    existing_task = state.task_exists(request.url)
    if existing_task:
        # 如果任务已完成，直接返回
        if existing_task.status == "completed":
            logger.info("Reusing completed task", extra={
                "task_id": existing_task.id,
                "url": request.url,
                "video_title": existing_task.video_title
            })
            return existing_task.id

        # 如果任务失败，重置状态并重新下载
        if existing_task.status == "failed":
            logger.info("Retrying failed task", extra={
                "task_id": existing_task.id,
                "url": request.url,
                "previous_error": existing_task.error
            })
            # 重置任务状态为 pending，清除错误信息
            state.update_task(existing_task.id, "pending", error="")
            # 重新启动下载任务
            asyncio.create_task(process_download_task(
                task_id=existing_task.id,
                url=request.url,
                output_path=request.output_path,
                format=request.format,
                quiet=request.quiet
            ))
            return existing_task.id

        # 如果任务正在进行中，直接返回
        if existing_task.status == "pending":
            logger.info("Task already in progress", extra={
                "task_id": existing_task.id,
                "url": request.url
            })
            return existing_task.id

    # 创建新任务
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
    """提交单个下载任务"""
    logger.info("Received download request", extra={"url": request.url})
    task_id = create_or_get_task(request)
    return {"status": "success", "task_id": task_id}


@router.post("/batch_download", response_class=JSONResponse)
async def batch_download(request: BatchDownloadRequest):
    """批量提交下载任务"""
    logger.info("Received batch download request", extra={"count": len(request.tasks)})
    task_ids = [create_or_get_task(task_req) for task_req in request.tasks]
    return {"status": "success", "task_ids": task_ids}


@router.get("/task/{task_id}", response_class=JSONResponse)
async def get_task_status(task_id: str):
    """查询单个任务状态"""
    task = state.get_task(task_id)
    if not task:
        logger.warning("Task not found", extra={"task_id": task_id})
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    response = {
        "status": "success",
        "data": {
            "id": task.id,
            "url": task.url,
            "video_title": task.video_title,
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
    """列出所有任务"""
    tasks = state.list_tasks()
    logger.debug("Listed all tasks", extra={"count": len(tasks)})
    return {"status": "success", "data": tasks}

@router.post("/batch_tasks", response_class=JSONResponse)
async def batch_get_tasks(request: BatchTaskQueryRequest):
    logger.debug("Batch task query", extra={"count": len(request.task_ids)})
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


@router.get("/fetch", response_class=JSONResponse)
async def fetch_91porn_page(page: int = 1):
    """获取91porn页面内容"""
    url = f"https://91porn.com/v.php?category=rf&viewtype=basic&page={page}"

    # 检查cookie配置
    if not settings.porn91_cookie:
        logger.warning("No 91porn cookie configured", extra={"page": page})
        raise HTTPException(
            status_code=500,
            detail="91porn cookie not configured in .env file"
        )

    # 配置请求头
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "cookie": settings.porn91_cookie
    }

    logger.info("Fetching 91porn page", extra={"page": page, "url": url})

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            logger.info("Successfully fetched 91porn page", extra={
                "page": page,
                "status_code": response.status_code,
                "content_length": len(response.text)
            })

            return {
                "status": "success",
                "data": {
                    "page": page,
                    "url": url,
                    "content": response.text,
                    "status_code": response.status_code
                }
            }
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error fetching 91porn page", extra={
            "page": page,
            "status_code": e.response.status_code,
            "error": str(e)
        })
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to fetch page: {str(e)}"
        )
    except httpx.RequestError as e:
        logger.error("Request error fetching 91porn page", extra={
            "page": page,
            "error": str(e)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Request failed: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error fetching 91porn page", extra={
            "page": page,
            "error": str(e)
        })
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )