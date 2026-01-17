"""
打包任务数据模型

一次完整的Nuitka打包操作,包含入口文件、输出路径、所有Nuitka参数、
执行状态和日志输出。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4, UUID


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, DEBUG
    message: str
    source: str = "nuitka"  # nuitka 或 system


@dataclass
class BuildTask:
    """打包任务对象

    表示一次完整的Nuitka打包操作,包含所有必要的输入参数和执行状态。
    """
    task_id: str = field(default_factory=lambda: str(uuid4()))
    entry_file: str = ""
    output_dir: str = ""
    output_filename: str = ""
    icon_path: Optional[str] = None
    command: str = ""
    log_file_path: Optional[str] = None  # 日志文件路径
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    logs: List[LogEntry] = field(default_factory=list)
    # config_snapshot 将在运行时注入
