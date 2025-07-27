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
        self.tasks: Dict[str, Task] = {}
        self.db_file = "tasks.db"
        self._init_db()
        self._load_tasks()
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
    def _load_tasks(self) -> None:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, output_path, format, status, result, error FROM tasks")
            rows = cursor.fetchall()
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
                self.tasks[task_id] = task
            conn.close()
        except Exception as e:
            print(f"Error loading tasks from database: {e}")
    def _save_task(self, task: Task) -> None:
        try:
            self.tasks[task.id] = task
            conn = sqlite3.connect(self.db_file)
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
        self.tasks[task_id] = task
        self._save_task(task)
        return task_id
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    def update_task(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            if result:
                task.result = result
            if error:
                task.error = error
            self._save_task(task)
    def list_tasks(self) -> List[Task]:
        return list(self.tasks.values()) 