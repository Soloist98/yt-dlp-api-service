"""
数据库模型定义
使用SQLAlchemy ORM
"""
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()


class TaskModel(Base):
    """任务数据库模型"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    url = Column(Text, nullable=False, index=True)
    video_title = Column(String(500), nullable=True)  # 视频标题
    output_path = Column(String(500), nullable=False)
    format = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)

    def __repr__(self):
        return f"<Task(id={self.id}, url={self.url}, title={self.video_title}, status={self.status})>"


# 创建数据库引擎
engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,  # 自动检测连接是否有效
    pool_recycle=3600,   # 1小时后回收连接
    echo=False           # 生产环境设为False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
