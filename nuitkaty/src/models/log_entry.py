"""
日志记录数据模型

单条日志信息。
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class LogEntryModel:
    """日志条目对象

    表示单条日志信息,包含时间戳、级别和消息内容。
    """
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = "system"  # 日志来源 (nuitka/system)
