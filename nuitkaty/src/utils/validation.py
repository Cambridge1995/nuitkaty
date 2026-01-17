"""
输入验证工具模块

提供各种输入验证函数。
"""
import os
import re


def validate_interpreter_path(path: str) -> tuple[bool, str]:
    """验证 Python 解释器路径是否有效

    Args:
        path: Python解释器路径

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not path:
        return False, "Python解释器路径不能为空"

    if not os.path.exists(path):
        return False, f"Python解释器路径不存在: {path}"

    if not path.endswith("python.exe"):
        return False, f"无效的Python解释器文件: {path}"

    return True, ""


def validate_pip_url(url: str) -> tuple[bool, str]:
    """验证 pip 镜像源 URL

    Args:
        url: 镜像源URL

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not url:
        return False, "pip镜像源URL不能为空"

    if not url.startswith(("http://", "https://")):
        return False, f"无效的URL格式,必须以http://或https://开头: {url}"

    return True, ""


def validate_jobs(jobs: int) -> tuple[bool, str]:
    """验证线程数量

    Args:
        jobs: 线程数量

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    cpu_count = os.cpu_count() or 1
    max_jobs = cpu_count * 2

    if not isinstance(jobs, int):
        return False, "线程数量必须是整数"

    if jobs < 1:
        return False, f"线程数量必须大于0, 当前值: {jobs}"

    if jobs > max_jobs:
        return False, f"线程数量不能超过CPU核心数的2倍({max_jobs}), 当前值: {jobs}"

    return True, ""


def validate_file_version(version: str) -> tuple[bool, str]:
    """验证文件版本格式 (x.x.x.x)

    Args:
        version: 版本字符串

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not version:
        return False, "文件版本不能为空"

    parts = version.split(".")
    if len(parts) != 4:
        return False, f"文件版本格式错误,应为x.x.x.x格式: {version}"

    if not all(p.isdigit() for p in parts):
        return False, f"文件版本必须全部为数字: {version}"

    return True, ""


def validate_output_filename(filename: str) -> tuple[bool, str]:
    """验证输出文件名

    Args:
        filename: 输出文件名

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not filename:
        return False, "输出文件名不能为空"

    if not filename.endswith(".exe"):
        return False, "输出文件名必须以.exe结尾"

    # 检查非法字符
    illegal_chars = '<>:"|?*'
    for char in illegal_chars:
        if char in filename:
            return False, f"文件名包含非法字符'{char}': {filename}"

    return True, ""


def validate_entry_file(path: str) -> tuple[bool, str]:
    """验证入口文件路径

    Args:
        path: 入口文件路径

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if not path:
        return False, "入口文件路径不能为空"

    if not os.path.exists(path):
        return False, f"入口文件不存在: {path}"

    if not path.endswith(".py"):
        return False, f"入口文件必须是Python文件(.py): {path}"

    return True, ""
