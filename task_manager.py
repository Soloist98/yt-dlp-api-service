import uuid
import json
import datetime
import sqlite3
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

def NormalizeString(s: str) -> str:
    """
    去掉头尾的空格， 所有特殊字符转换成 _
    """
    s = s.strip()
    special_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in special_chars:
        s = s.replace(char, '_')
    return s

class Task(BaseModel):
    id: str
    url: str
    output_path: str
    format: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class State:
    def __init__(self):
        self.db_file = "tasks.db"
        self._init_db()
    
    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            output_path TEXT NOT NULL,
            format TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
    
    def _get_db_connection(self):
        return sqlite3.connect(self.db_file)
    
    def _load_task_from_db(self, task_id: str) -> Optional[Task]:
        """从数据库加载单个任务"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, output_path, format, status, result, error FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                task_id, url, output_path, format, status, result_json, error = row
                result = json.loads(result_json) if result_json else None
                return Task(
                    id=task_id,
                    url=url,
                    output_path=output_path,
                    format=format,
                    status=status,
                    result=result,
                    error=error
                )
            return None
        except Exception as e:
            print(f"Error loading task from database: {e}")
            return None
    
    def _save_task(self, task: Task) -> None:
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()
            result_json = json.dumps(task.result) if task.result else None
            cursor.execute('''
            INSERT OR REPLACE INTO tasks (id, url, output_path, format, status, result, error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.url,
                task.output_path,
                task.format,
                task.status,
                result_json,
                task.error,
                timestamp
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving task to database: {e}")
    
    def add_task(self, url: str, output_path: str, format: str) -> str:
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            url=url,
            output_path=output_path,
            format=format,
            status="pending"
        )
        self._save_task(task)
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """从数据库查询单个任务"""
        return self._load_task_from_db(task_id)
    
    def update_task(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """更新任务状态"""
        task = self._load_task_from_db(task_id)
        if task:
            task.status = status
            if result:
                task.result = result
            if error:
                task.error = error
            self._save_task(task)
    
    def list_tasks(self) -> List[Task]:
        """从数据库查询所有任务"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, output_path, format, status, result, error FROM tasks ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                task_id, url, output_path, format, status, result_json, error = row
                result = json.loads(result_json) if result_json else None
                task = Task(
                    id=task_id,
                    url=url,
                    output_path=output_path,
                    format=format,
                    status=status,
                    result=result,
                    error=error
                )
                tasks.append(task)
            return tasks
        except Exception as e:
            print(f"Error loading tasks from database: {e}")
            return []
    
    def task_exists(self, url: str, output_path: str, format: str) -> Optional[Task]:
        """检查任务是否已存在"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, url, output_path, format, status, result, error FROM tasks WHERE url = ? AND output_path = ? AND format = ?",
                (url, output_path, format)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                task_id, url, output_path, format, status, result_json, error = row
                result = json.loads(result_json) if result_json else None
                return Task(
                    id=task_id,
                    url=url,
                    output_path=output_path,
                    format=format,
                    status=status,
                    result=result,
                    error=error
                )
            return None
        except Exception as e:
            print(f"Error checking task existence: {e}")
            return None
    
    def clear_all_tasks(self) -> bool:
        """清除数据库中的所有任务"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing all tasks: {e}")
            return False 