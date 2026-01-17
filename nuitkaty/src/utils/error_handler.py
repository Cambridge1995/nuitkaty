"""
错误处理工具模块

提供统一的错误处理机制,包括错误装饰器、错误对话框等。
"""
import functools
import traceback
from typing import Callable, TypeVar, Any
from PySide6.QtWidgets import QWidget

from qfluentwidgets import InfoBar, InfoBarPosition


T = TypeVar('T')


def handle_errors(
    title: str = "操作失败",
    message: str = "操作过程中发生错误",
    show_traceback: bool = False,
    default_return: Any = None
) -> Callable:
    """错误处理装饰器

    捕获函数中的异常并显示友好的错误提示。

    Args:
        title: 错误对话框标题
        message: 错误对话框消息
        show_traceback: 是否显示详细错误信息
        default_return: 发生错误时的默认返回值

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                # 文件未找到错误
                parent = _get_parent_widget(args)
                InfoBar.error(
                    title=title,
                    content=f"{message}\n文件未找到: {e}",
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return
            except PermissionError as e:
                # 权限错误
                parent = _get_parent_widget(args)
                InfoBar.error(
                    title=title,
                    content=f"{message}\n权限不足: {e}",
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return
            except ValueError as e:
                # 值错误
                parent = _get_parent_widget(args)
                InfoBar.warning(
                    title=title,
                    content=f"{message}\n{e}",
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return
            except KeyError as e:
                # 键错误
                parent = _get_parent_widget(args)
                InfoBar.warning(
                    title=title,
                    content=f"{message}\n缺少必要的配置: {e}",
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return
            except ConnectionError as e:
                # 网络连接错误
                parent = _get_parent_widget(args)
                InfoBar.error(
                    title=title,
                    content=f"{message}\n网络连接失败: {e}",
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return
            except Exception as e:
                # 其他错误
                parent = _get_parent_widget(args)
                content = message

                if show_traceback:
                    content = f"{message}\n{traceback.format_exc()}"
                else:
                    content = f"{message}\n{str(e)}"

                InfoBar.error(
                    title=title,
                    content=content,
                    parent=parent,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
                return default_return

        return wrapper

    return decorator


def _get_parent_widget(args: tuple) -> QWidget | None:
    """从参数中获取父窗口

    Args:
        args: 函数参数

    Returns:
        QWidget | None: 父窗口或 None
    """
    if args and isinstance(args[0], QWidget):
        return args[0]
    return None


def validate_path_exists(path: str, error_message: str = "路径不存在") -> None:
    """验证路径是否存在

    Args:
        path: 要验证的路径
        error_message: 错误消息

    Raises:
        FileNotFoundError: 路径不存在
    """
    import os

    if not path:
        raise ValueError(error_message)

    if not os.path.exists(path):
        raise FileNotFoundError(f"{error_message}: {path}")


def validate_file_extension(
    file_path: str,
    allowed_extensions: list[str],
    error_message: str = "文件类型不支持"
) -> None:
    """验证文件扩展名

    Args:
        file_path: 文件路径
        allowed_extensions: 允许的扩展名列表 (如 ['.py', '.exe'])
        error_message: 错误消息

    Raises:
        ValueError: 文件扩展名不支持
    """
    import os

    if not file_path:
        raise ValueError("文件路径为空")

    _, ext = os.path.splitext(file_path)

    if ext.lower() not in [e.lower() for e in allowed_extensions]:
        raise ValueError(f"{error_message}: {ext}. 支持的格式: {', '.join(allowed_extensions)}")


def validate_output_dir(path: str) -> None:
    """验证输出目录是否可写

    Args:
        path: 输出目录路径

    Raises:
        PermissionError: 目录不可写
        FileNotFoundError: 目录不存在
    """
    import os

    if not path:
        raise ValueError("输出目录为空")

    if not os.path.exists(path):
        raise FileNotFoundError(f"输出目录不存在: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"路径不是目录: {path}")

    if not os.access(path, os.W_OK):
        raise PermissionError(f"输出目录不可写: {path}")


class SafeConfigLoader:
    """安全的配置加载器

    处理配置文件损坏、缺失等问题。
    """

    @staticmethod
    def load_with_fallback(config_manager, fallback_factory):
        """加载配置,失败时使用后备方案

        Args:
            config_manager: 配置管理器
            fallback_factory: 后备配置工厂函数

        Returns:
            配置对象
        """
        try:
            return config_manager.load()
        except Exception as e:
            # 配置加载失败,使用默认配置
            print(f"配置加载失败: {e}, 使用默认配置")
            return fallback_factory()


class RetryHandler:
    """重试处理器

    为网络操作等提供重试机制。
    """

    @staticmethod
    def retry_on_error(
        func: Callable,
        max_retries: int = 3,
        retry_exceptions: tuple = (ConnectionError, TimeoutError),
        on_retry: Callable | None = None
    ) -> Any:
        """在错误时重试函数

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_exceptions: 触发重试的异常类型
            on_retry: 重试时的回调函数

        Returns:
            函数执行结果
        """
        import time

        last_exception = None

        for attempt in range(max_retries):
            try:
                return func()
            except retry_exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    if on_retry:
                        on_retry(attempt + 1, e)
                    time.sleep(1)  # 等待 1 秒后重试
                else:
                    raise
            except Exception as e:
                # 不在重试异常列表中的异常直接抛出
                raise

        # 理论上不会到达这里
        if last_exception:
            raise last_exception
