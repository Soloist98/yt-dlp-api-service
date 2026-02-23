"""
任务管理模块 - 使用SQLAlchemy ORM重构
"""
import uuid
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, TaskModel, init_database


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
    output_path: str
    format: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class State:
    """任务状态管理类"""

    def __init__(self):
        """初始化数据库"""
        init_database()

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
            return task_id
        except Exception as e:
            db.rollback()
            print(f"Error adding task: {e}")
            raise
        finally:
            db.close()

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取单个任务"""
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not db_task:
                return None

            result = json.loads(db_task.result) if db_task.result else None
            return Task(
                id=db_task.id,
                url=db_task.url,
                output_path=db_task.output_path,
                format=db_task.format,
                status=db_task.status,
                result=result,
                error=db_task.error
            )
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
        finally:
            db.close()

    def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """更新任务状态"""
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                db_task.status = status
                if result:
                    db_task.result = json.dumps(result)
                if error:
                    db_task.error = error
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error updating task: {e}")
        finally:
            db.close()

    def list_tasks(self) -> List[Task]:
        """列出所有任务"""
        db = self._get_db()
        try:
            db_tasks = db.query(TaskModel).order_by(TaskModel.timestamp.desc()).all()
            tasks = []
            for db_task in db_tasks:
                result = json.loads(db_task.result) if db_task.result else None
                task = Task(
                    id=db_task.id,
                    url=db_task.url,
                    output_path=db_task.output_path,
                    format=db_task.format,
                    status=db_task.status,
                    result=result,
                    error=db_task.error
                )
                tasks.append(task)
            return tasks
        except Exception as e:
            print(f"Error listing tasks: {e}")
            return []
        finally:
            db.close()

    def task_exists(self, url: str, output_path: str, format: str) -> Optional[Task]:
        """检查任务是否已存在"""
        db = self._get_db()
        try:
            db_task = db.query(TaskModel).filter(
                TaskModel.url == url,
                TaskModel.output_path == output_path,
                TaskModel.format == format
            ).first()

            if not db_task:
                return None

            result = json.loads(db_task.result) if db_task.result else None
            return Task(
                id=db_task.id,
                url=db_task.url,
                output_path=db_task.output_path,
                format=db_task.format,
                status=db_task.status,
                result=result,
                error=db_task.error
            )
        except Exception as e:
            print(f"Error checking task existence: {e}")
            return None
        finally:
            db.close()

    def clear_all_tasks(self) -> bool:
        """清除所有任务"""
        db = self._get_db()
        try:
            db.query(TaskModel).delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error clearing all tasks: {e}")
            return False
        finally:
            db.close()
