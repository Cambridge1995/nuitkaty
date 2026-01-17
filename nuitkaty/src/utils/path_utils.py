"""
路径工具函数模块

提供路径处理相关的工具函数。
"""
import os
from typing import Optional


def normalize_path(path: str) -> str:
    """标准化路径格式

    将反斜杠转换为正斜杠,移除末尾分隔符。

    Args:
        path: 文件路径

    Returns:
        str: 标准化后的路径
    """
    # 转换反斜杠为正斜杠
    path = path.replace("\\", "/")
    # 移除末尾分隔符
    path = path.rstrip("/")
    return path


def join_path(base: str, *parts: str) -> str:
    """连接路径组件

    Args:
        base: 基础路径
        *parts: 路径组件

    Returns:
        str: 连接后的路径
    """
    return os.path.join(base, *parts)


def get_absolute_path(path: str, base: Optional[str] = None) -> str:
    """获取绝对路径

    Args:
        path: 相对或绝对路径
        base: 基础路径(用于相对路径)

    Returns:
        str: 绝对路径
    """
    if os.path.isabs(path):
        return path
    if base:
        return os.path.abspath(os.path.join(base, path))
    return os.path.abspath(path)


def is_python_file(path: str) -> bool:
    """检查是否为Python文件

    Args:
        path: 文件路径

    Returns:
        bool: 是否为Python文件
    """
    return path.endswith(".py") or path.endswith(".pyw")


def is_executable(path: str) -> bool:
    """检查是否为可执行文件

    Args:
        path: 文件路径

    Returns:
        bool: 是否为可执行文件
    """
    return path.endswith(".exe") or os.access(path, os.X_OK)
