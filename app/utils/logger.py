"""
结构化日志配置模块
使用 loguru 实现结构化日志
"""
import sys
import os
from pathlib import Path
from loguru import logger
from config import settings


def serialize_record(record):
    """序列化日志记录为JSON格式"""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # 添加额外的上下文信息
    if record["extra"]:
        subset["extra"] = record["extra"]

    # 添加异常信息
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
        }

    return subset


def json_formatter(record):
    """JSON格式化器"""
    import json
    record["extra"]["serialized"] = json.dumps(serialize_record(record), ensure_ascii=False)
    return "{extra[serialized]}\n"


def text_formatter(record):
    """文本格式化器"""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>\n"
        "{exception}"
    )


def setup_logger():
    """配置日志系统"""
    # 移除默认的处理器
    logger.remove()

    # 确定日志格式
    if settings.log_format == "json":
        formatter = json_formatter
    else:
        formatter = text_formatter

    # 控制台输出（彩色文本格式）
    logger.add(
        sys.stderr,
        format=text_formatter,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 文件输出
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.log_file,
        format=formatter if settings.log_format == "json" else text_formatter,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    # 错误日志单独文件
    error_log_file = str(log_path.parent / f"{log_path.stem}_error{log_path.suffix}")
    logger.add(
        error_log_file,
        format=formatter if settings.log_format == "json" else text_formatter,
        level="ERROR",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    logger.info("Logger initialized", extra={
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "log_file": settings.log_file,
    })

    return logger


# 初始化日志
setup_logger()

# 导出logger供其他模块使用
__all__ = ["logger"]
