"""
嵌入文件数据模型

需要打包进EXE的数据文件或目录,包含源路径和目标路径的映射。
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FileType(Enum):
    """文件类型枚举"""
    FILE = "file"          # 单个文件
    DIRECTORY = "directory"  # 整个目录 (原名 DIR)
    PATTERN = "pattern"      # 文件模式

    # 兼容旧代码
    DIR = DIRECTORY


@dataclass
class EmbeddedFile:
    """嵌入文件对象

    表示需要打包进EXE的数据文件或目录配置。
    """
    source_path: str
    destination_path: str      # 目标路径 (原名 target_path)
    file_type: FileType = FileType.FILE  # 文件类型 (原名 type)
    recursive: bool = False
    pattern: Optional[str] = None

    # 兼容旧代码的属性
    @property
    def target_path(self) -> str:
        """目标路径（兼容旧代码）"""
        return self.destination_path

    @property
    def type(self) -> FileType:
        """文件类型（兼容旧代码）"""
        return self.file_type

    def validate(self) -> tuple[bool, str]:
        """验证嵌入文件配置

        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        """
        import os

        # 验证源路径存在
        if not os.path.exists(self.source_path):
            return False, f"源路径不存在: {self.source_path}"

        # 验证目标路径格式
        if "\\" in self.destination_path:
            return False, f"目标路径不能包含反斜杠: {self.destination_path}"

        if self.destination_path.startswith("/"):
            return False, f"目标路径不能以/开头: {self.destination_path}"

        # PATTERN类型必须有pattern
        if self.file_type == FileType.PATTERN and not self.pattern:
            return False, "PATTERN类型必须指定pattern参数"

        return True, ""
