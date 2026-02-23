"""
配置管理模块
支持从环境变量和.env文件加载配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    database_type: str = "sqlite"  # sqlite 或 mysql
    database_url: Optional[str] = None  # 完整的数据库URL（优先级最高）

    # MySQL配置（当database_type为mysql时使用）
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "yt_dlp_api"

    # SQLite配置（当database_type为sqlite时使用）
    sqlite_db_file: str = "tasks.db"

    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # 下载配置
    default_download_path: str = "./downloads"
    max_concurrent_downloads: int = 5
    thread_pool_size: int = 10

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json 或 text
    log_file: str = "logs/app.log"
    log_rotation: str = "100 MB"  # 日志轮转大小
    log_retention: str = "30 days"  # 日志保留时间
    log_compression: str = "zip"  # 日志压缩格式

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        if self.database_url:
            return self.database_url

        if self.database_type == "mysql":
            return (
                f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
                f"?charset=utf8mb4"
            )
        else:
            return f"sqlite:///{self.sqlite_db_file}"


# 全局配置实例
settings = Settings()
