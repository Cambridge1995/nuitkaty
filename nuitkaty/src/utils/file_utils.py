"""
文件工具函数模块

提供文件操作相关的工具函数。
"""
import os
import shutil
from typing import Optional


def quote_path(path: str) -> str:
    """为包含空格的路径添加引号

    Args:
        path: 文件路径

    Returns:
        str: 添加引号后的路径
    """
    if " " in path or '"' in path:
        return f'"{path}"'
    return path


def validate_path(path: str) -> tuple[bool, str]:
    """验证路径是否有效

    Args:
        path: 文件或目录路径

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not path:
        return False, "路径不能为空"

    if not os.path.exists(path):
        return False, f"路径不存在: {path}"

    return True, ""


def ensure_directory_exists(path: str) -> bool:
    """确保目录存在,不存在则创建

    Args:
        path: 目录路径

    Returns:
        bool: 是否成功
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def is_writable(path: str) -> bool:
    """检查路径是否可写

    Args:
        path: 文件或目录路径

    Returns:
        bool: 是否可写
    """
    if os.path.isfile(path):
        return os.access(path, os.W_OK)
    elif os.path.isdir(path):
        return os.access(path, os.W_OK)
    else:
        # 检查父目录是否可写
        parent = os.path.dirname(path)
        return os.path.exists(parent) and os.access(parent, os.W_OK)


def get_file_extension(filename: str) -> str:
    """获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        str: 扩展名(包含点),如".py"
    """
    return os.path.splitext(filename)[1]
