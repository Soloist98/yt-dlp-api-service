"""
配置管理模块
支持从环境变量和.env文件加载配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict
import json


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

    # 特殊站点路径配置（JSON格式）
    # 格式: {"domain_keyword": "subdirectory"}
    # 例如: {"pornhub": "adult", "youtube": "youtube"}
    site_path_mapping: str = "{}"

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

    def get_site_path_mapping(self) -> Dict[str, str]:
        """获取站点路径映射配置"""
        try:
            return json.loads(self.site_path_mapping)
        except json.JSONDecodeError:
            return {}

    def get_output_path_for_url(self, url: str, base_path: str) -> str:
        """
        根据URL获取输出路径
        如果URL包含特殊站点关键词，则添加对应的子目录
        """
        site_mapping = self.get_site_path_mapping()

        for keyword, subdirectory in site_mapping.items():
            if keyword.lower() in url.lower():
                # 确保路径不重复添加子目录
                if not base_path.endswith(subdirectory):
                    return f"{base_path}/{subdirectory}"
                return base_path

        return base_path


# 全局配置实例
settings = Settings()
