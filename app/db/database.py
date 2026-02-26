"""
数据库模型定义
使用SQLAlchemy ORM
"""
from sqlalchemy import Column, String, Text, DateTime, create_engine, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings
import sys

Base = declarative_base()


class TaskModel(Base):
    """任务数据库模型"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    url = Column(Text, nullable=False)  # TEXT 类型，不直接索引
    video_title = Column(String(500), nullable=True)
    output_path = Column(String(500), nullable=False)
    format = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now, index=True)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, index=True)

    # 为 TEXT 类型的 url 列创建前缀索引（MySQL 限制）
    __table_args__ = (
        Index('ix_tasks_url_prefix', url, mysql_length=255),
    )

    def __repr__(self):
        return f"<Task(id={self.id}, url={self.url[:50] if self.url else ''}..., title={self.video_title}, status={self.status})>"


# 创建数据库引擎
try:
    engine = create_engine(
        settings.get_database_url(),
        pool_pre_ping=True,  # 自动检测连接是否有效
        pool_recycle=3600,   # 1小时后回收连接
        echo=False,          # 生产环境设为False
        connect_args={
            "connect_timeout": 10  # 连接超时10秒
        } if settings.database_type == "mysql" else {}
    )
except Exception as e:
    print(f"错误: 无法创建数据库引擎: {e}")
    print(f"数据库类型: {settings.database_type}")
    print(f"数据库URL: {settings.get_database_url()}")
    sys.exit(1)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """初始化数据库，创建所有表"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"错误: 无法初始化数据库: {e}")
        print(f"请检查数据库连接配置")
        print(f"运行诊断脚本: ./scripts/check-db.sh")
        sys.exit(1)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
