"""
日志读取线程模块

在后台线程中定期读取日志文件，避免阻塞主线程UI。
"""
import os
from datetime import datetime
from PySide6.QtCore import QThread, Signal, QObject, QMutex, QMutexLocker


class LogReaderThread(QThread):
    """日志读取线程

    在后台线程中定期读取日志文件，发送信号通知主线程更新UI。
    """

    # 信号定义
    logs_received = Signal(list)  # 接收到新日志行列表
    read_error = Signal(str)      # 读取错误

    def __init__(self, log_file_path: str, interval_ms: int = 15000, parent=None):
        """初始化日志读取线程

        Args:
            log_file_path: 日志文件路径
            interval_ms: 读取间隔（毫秒），默认15秒
            parent: 父对象
        """
        super().__init__(parent)
        self.log_file_path = log_file_path
        self.interval_ms = interval_ms
        self._last_position = 0  # 记录上次读取位置
        self._is_running = False
        self._log_file_exists = False
        self._mutex = QMutex()  # 互斥锁，保护共享状态

    def run(self) -> None:
        """运行日志读取循环"""
        self._is_running = True
        self._log_file_exists = os.path.exists(self.log_file_path)

        # 如果文件已存在，从头开始读取
        if self._log_file_exists:
            self._last_position = 0

        while self._is_running:
            try:
                # 检查是否被请求中断
                if self.isInterruptionRequested():
                    break

                self._read_new_logs()
            except Exception as e:
                # 只在线程还在运行时才发射错误信号
                if self._is_running:
                    self.read_error.emit(f"读取日志文件出错: {e}")

            # 使用可中断的等待，每次检查一小段时间
            # 这样可以更快地响应停止请求
            for _ in range(self.interval_ms // 100):
                if not self._is_running or self.isInterruptionRequested():
                    break
                self.msleep(100)  # 每次等待100ms

    def stop(self) -> None:
        """停止日志读取线程"""
        # 使用互斥锁保护状态修改
        with QMutexLocker(self._mutex):
            self._is_running = False

        # 请求中断线程
        self.requestInterruption()

        # 等待线程结束（最多等待5秒）
        if not self.wait(5000):
            # 如果线程没有在5秒内停止，强制终止
            self.terminate()
            self.wait(1000)  # 再等待1秒确保线程已终止

    def reset_position(self) -> None:
        """重置读取位置到文件开头"""
        self._last_position = 0

    def _read_new_logs(self) -> None:
        """读取日志文件中的新内容

        发送信号通知主线程更新UI。
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(self.log_file_path):
                # 如果文件之前存在但现在不存在了，重置状态
                if self._log_file_exists:
                    self._log_file_exists = False
                    self._last_position = 0
                return

            # 文件刚被创建
            if not self._log_file_exists:
                self._log_file_exists = True
                self._last_position = 0

            # 获取当前文件大小
            file_size = os.path.getsize(self.log_file_path)

            # 如果文件为空或没有新内容
            if file_size == 0 or file_size <= self._last_position:
                return

            # 读取新内容
            new_lines = []
            with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self._last_position)
                new_lines = f.readlines()
                # 在 with 块内更新读取位置，确保文件句柄有效
                self._last_position = f.tell()

            # 如果有新内容，发送信号
            if new_lines:
                # 过滤空行并去除换行符
                filtered_lines = []
                for line in new_lines:
                    stripped = line.rstrip('\n\r')
                    if stripped:
                        filtered_lines.append(stripped)

                if filtered_lines:
                    self.logs_received.emit(filtered_lines)

        except ValueError as e:
            # 文件被关闭或无法访问时的处理
            if "closed file" in str(e) or "I/O operation" in str(e):
                # 文件已被关闭，可能是打包完成，静默忽略
                pass
            else:
                self.read_error.emit(f"读取日志失败: {e}")
        except (OSError, IOError) as e:
            # 文件访问错误，可能是文件被删除或移动，静默忽略
            pass
        except Exception as e:
            # 其他未预期的错误
            self.read_error.emit(f"读取日志失败: {e}")

    def set_interval(self, interval_ms: int) -> None:
        """设置读取间隔

        Args:
            interval_ms: 新的读取间隔（毫秒）
        """
        self.interval_ms = interval_ms
