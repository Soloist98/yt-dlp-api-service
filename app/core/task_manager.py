"""
任务管理模块 - 使用SQLAlchemy ORM重构
"""
import uuid
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, TaskModel, init_database
from app.utils.logger import logger


def NormalizeString(s: str) -> str:
    """
    去掉头尾的空格，所有特殊字符转换成 _
    """
    s = s.strip()
    special_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in special_chars:
        s = s.replace(char, '_')
    return s


class Task(BaseModel):
    """任务数据模型"""
    id: str
    url: str
    video_title: Optional[str] = None
    output_path: str
    format: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class State:
    """任务状态管理类"""

    def __init__(self):
        """初始化数据库"""
        logger.info("Initializing task manager")
        init_database()
        logger.info("Task manager initialized successfully")

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def add_task(self, url: str, output_path: str, format: str) -> str:
        """添加新任务"""
        task_id = str(uuid.uuid4())
        db = self._get_db()
        try:
            db_task = TaskModel(
                id=task_id,
                url=url,
                output_path=output_path,
                format=format,
                status="pending"
            )
            db.add(db_task)
            db.commit()
            logger.info("Task created", extra={
                "task_id": task_id,
                "url": url,
                "output_path": output_path,
                "format": format
            })
            return task_id
        except Exception as e:
            db.rollback()
            logger.error("Failed to create task", extra={
                "url": url,
                "error": str(e)
            })
            raise
        finally:
            db.close()

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取单个任务"""
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not db_task:
                logger.debug("Task not found", extra={"task_id": task_id})
                return None

            result = json.loads(db_task.result) if db_task.result else None
            return Task(
                id=db_task.id,
                url=db_task.url,
                video_title=db_task.video_title,
                output_path=db_task.output_path,
                format=db_task.format,
                status=db_task.status,
                result=result,
                error=db_task.error,
                create_time=db_task.create_time.isoformat(),
                update_time=db_task.update_time.isoformat()
            )
        except Exception as e:
            logger.error("Failed to get task", extra={
                "task_id": task_id,
                "error": str(e)
            })
            return None
        finally:
            db.close()

    def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        update_time: bool = True
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            result: 结果数据
            error: 错误信息
            update_time: 是否更新 update_time（默认True，重复提交时为False）
        """
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                old_status = db_task.status
                db_task.status = status
                if result:
                    db_task.result = json.dumps(result)
                    # 从结果中提取视频标题
                    if 'title' in result:
                        db_task.video_title = result['title']
                if error is not None:  # 允许清除错误信息
                    db_task.error = error

                # 手动更新 update_time（失败重试时）
                if update_time and status == "pending" and old_status == "failed":
                    from datetime import datetime
                    db_task.update_time = datetime.now()

                db.commit()

                log_extra = {
                    "task_id": task_id,
                    "old_status": old_status,
                    "new_status": status
                }

                if error:
                    logger.error("Task failed", extra={**log_extra, "error": error})
                elif status == "completed":
                    logger.info("Task completed", extra={
                        **log_extra,
                        "video_title": db_task.video_title
                    })
                elif status == "pending" and old_status == "failed":
                    logger.info("Task reset for retry", extra=log_extra)
                else:
                    logger.info("Task status updated", extra=log_extra)
        except Exception as e:
            db.rollback()
            logger.error("Failed to update task", extra={
                "task_id": task_id,
                "status": status,
                "error": str(e)
            })
        finally:
            db.close()

    def list_tasks(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
        order: str = "desc"
    ) -> tuple[List[Task], int]:
        """
        列出任务（支持过滤、分页和排序）

        Args:
            status: 任务状态过滤 (pending/completed/failed)
            page: 页码（从1开始）
            page_size: 每页数量
            order: 排序方向 (asc/desc)，按时间排序

        Returns:
            (tasks, total): 任务列表和总数
        """
        db = self._get_db()
        try:
            # 构建查询
            query = db.query(TaskModel)

            # 状态过滤
            if status:
                query = query.filter(TaskModel.status == status)

            # 获取总数
            total = query.count()

            # 按更新时间排序
            if order == "asc":
                query = query.order_by(TaskModel.update_time.asc())
            else:
                query = query.order_by(TaskModel.update_time.desc())

            # 分页
            offset = (page - 1) * page_size
            db_tasks = query.offset(offset).limit(page_size).all()

            # 转换为 Task 对象
            tasks = []
            for db_task in db_tasks:
                result = json.loads(db_task.result) if db_task.result else None
                task = Task(
                    id=db_task.id,
                    url=db_task.url,
                    video_title=db_task.video_title,
                    output_path=db_task.output_path,
                    format=db_task.format,
                    status=db_task.status,
                    result=result,
                    error=db_task.error,
                    create_time=db_task.create_time.isoformat(),
                    update_time=db_task.update_time.isoformat()
                )
                tasks.append(task)

            logger.debug("Listed tasks", extra={
                "count": len(tasks),
                "total": total,
                "page": page,
                "page_size": page_size,
                "status_filter": status
            })
            return tasks, total
        except Exception as e:
            logger.error("Failed to list tasks", extra={"error": str(e)})
            return [], 0
        finally:
            db.close()

    def task_exists(self, url: str) -> Optional[Task]:
        """检查任务是否已存在（只根据URL判断）"""
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(
                TaskModel.url == url
            ).first()

            if not db_task:
                return None

            logger.debug("Found existing task", extra={
                "task_id": db_task.id,
                "url": url,
                "status": db_task.status
            })

            result = json.loads(db_task.result) if db_task.result else None
            return Task(
                id=db_task.id,
                url=db_task.url,
                video_title=db_task.video_title,
                output_path=db_task.output_path,
                format=db_task.format,
                status=db_task.status,
                result=result,
                error=db_task.error,
                create_time=db_task.create_time.isoformat(),
                update_time=db_task.update_time.isoformat()
            )
        except Exception as e:
            logger.error("Failed to check task existence", extra={
                "url": url,
                "error": str(e)
            })
            return None
        finally:
            db.close()

    def clear_all_tasks(self) -> bool:
        """清除所有任务"""
        db = self._get_db()
        try:
            count = db.query(TaskModel).count()
            db.query(TaskModel).delete()
            db.commit()
            logger.warning("All tasks cleared", extra={"count": count})
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to clear tasks", extra={"error": str(e)})
            return False
        finally:
            db.close()
