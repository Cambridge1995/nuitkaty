"""
Nuitka 命令执行器模块

在后台线程执行 Nuitka 命令,将输出写入日志文件。
"""
import os
import re
import subprocess
from datetime import datetime
from PySide6.QtCore import QThread, Signal, QObject

from nuitkaty.src.models.build_task import BuildTask, LogEntry, TaskStatus


class NuitkaRunner(QThread):
    """Nuitka 命令执行器

    继承 QThread 在后台执行 Nuitka 命令,将输出写入日志文件。
    """

    # 信号定义
    output_received = Signal(str)          # 接收到一行输出 (已弃用,保留兼容性)
    progress_updated = Signal(int)         # 进度更新 (0-100) (已弃用,保留兼容性)
    build_finished = Signal(int)           # 构建完成 (退出码)
    build_failed = Signal(str)             # 构建失败 (错误消息)

    def __init__(self, task: BuildTask, parent=None):
        """初始化执行器

        Args:
            task: 打包任务对象
            parent: 父对象
        """
        super().__init__(parent)
        self.task = task
        self.process: subprocess.Popen | None = None
        self._is_running = False
        self._log_file = None

    def run(self) -> None:
        """执行 Nuitka 命令 (在后台线程中运行)"""
        self._is_running = True
        self.task.status = TaskStatus.RUNNING
        self.task.start_time = datetime.now()

        # 打开日志文件
        if self.task.log_file_path:
            try:
                # 确保输出目录存在
                log_dir = os.path.dirname(self.task.log_file_path)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)

                self._log_file = open(self.task.log_file_path, 'w', encoding='utf-8', errors='replace')
                self._write_log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self._write_log(f"命令: {self.task.command}")
                self._write_log("=" * 80)
            except Exception as e:
                self.task.status = TaskStatus.FAILED
                self.task.end_time = datetime.now()
                error_msg = f"无法创建日志文件: {e}"
                self.build_failed.emit(error_msg)
                self._is_running = False
                return

        try:
            # 解析命令行
            command_parts = self._parse_command(self.task.command)

            # 启动进程
            self.process = subprocess.Popen(
                command_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            # 实时读取输出并写入日志文件
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    line = line.rstrip('\n\r')
                    self._handle_output(line)

            # 等待进程结束
            exit_code = self.process.wait()
            self.task.exit_code = exit_code
            self.task.end_time = datetime.now()

            if exit_code == 0:
                self.task.status = TaskStatus.COMPLETED
                self._write_log("=" * 80)
                self._write_log(f"构建成功! 退出码: {exit_code}")
                self._write_log(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self._close_log_file()
                self.build_finished.emit(exit_code)
            else:
                self.task.status = TaskStatus.FAILED
                error_msg = f"构建失败,退出码: {exit_code}"
                self._write_log("=" * 80)
                self._write_log(error_msg)
                self._write_log(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self._close_log_file()
                self.build_failed.emit(error_msg)

        except FileNotFoundError as e:
            self.task.status = TaskStatus.FAILED
            self.task.end_time = datetime.now()
            error_msg = f"找不到 Nuitka 程序: {e}"
            self._write_log(f"错误: {error_msg}")
            self._close_log_file()
            self.build_failed.emit(error_msg)

        except Exception as e:
            self.task.status = TaskStatus.FAILED
            self.task.end_time = datetime.now()
            error_msg = f"构建过程出错: {e}"
            self._write_log(f"错误: {error_msg}")
            self._close_log_file()
            self.build_failed.emit(error_msg)

        finally:
            self._is_running = False

    def stop(self) -> None:
        """停止当前构建

        终止 Nuitka 进程及其所有子进程。
        """
        if self.process and self._is_running:
            import sys

            # 标记为正在停止
            self._is_running = False

            # 使用 taskkill 命令在 Windows 上终止整个进程树
            if sys.platform == "win32":
                try:
                    import subprocess as sp
                    # 获取主进程 PID
                    pid = self.process.pid

                    # 使用 taskkill /F /T 强制终止进程树
                    # /F = 强制终止
                    # /T = 终止指定进程及其子进程
                    sp.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=10
                    )
                except Exception as e:
                    # 如果 taskkill 失败，回退到常规方法
                    print(f"taskkill 失败: {e}")
                    self._terminate_process_fallback()
            else:
                # Unix-like 系统
                self._terminate_process_fallback()

            # 关闭日志文件
            self._write_log("构建已取消")
            self._close_log_file()

            # 更新任务状态
            self.task.status = TaskStatus.FAILED
            self.task.end_time = datetime.now()

    def _terminate_process_fallback(self) -> None:
        """备用进程终止方法

        当 taskkill 不可用时使用的方法。
        """
        try:
            self.process.terminate()
            # 等待最多 3 秒
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # 强制杀死
            try:
                self.process.kill()
                self.process.wait(timeout=2)
            except Exception as e:
                print(f"强制终止进程失败: {e}")
        except Exception as e:
            print(f"终止进程失败: {e}")

    def is_running(self) -> bool:
        """检查是否正在运行

        Returns:
            bool: 是否正在运行
        """
        return self._is_running and self.process is not None

    def _parse_command(self, command: str) -> list[str]:
        """解析命令行字符串为列表

        处理带引号的路径,例如:
        'nuitka --output-dir="C:/My App/dist" main.py'
        -> ['nuitka', '--output-dir=C:/My App/dist', 'main.py']

        使用 shlex.split() 正确处理 shell 转义和引号。

        Args:
            command: 命令行字符串

        Returns:
            list[str]: 解析后的命令列表
        """
        import shlex
        try:
            # shlex.split 会正确处理引号和转义字符
            # Windows 平台使用 posix=False 以兼容 Windows 路径
            return shlex.split(command, posix=False)
        except Exception as e:
            # 如果 shlex 解析失败，回退到简单的空格分割
            print(f"警告: 命令解析失败，使用简单分割: {e}")
            return command.split()

    def _write_log(self, message: str) -> None:
        """写入日志到文件

        每行自动添加 [时间][级别] 前缀

        Args:
            message: 日志消息
        """
        if self._log_file:
            try:
                # 添加时间戳和级别前缀
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                level = "INFO"  # 默认级别
                formatted_message = f"[{timestamp}] [{level}] {message}"
                self._log_file.write(formatted_message + "\n")
                self._log_file.flush()  # 立即刷新缓冲区
            except Exception:
                pass

    def _close_log_file(self) -> None:
        """关闭日志文件"""
        if self._log_file:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

    def _handle_output(self, line: str) -> None:
        """处理一行输出

        写入日志文件,不再发射信号。

        Args:
            line: 输出行
        """
        # 添加日志到任务
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message=line,
            source="nuitka"
        )
        self.task.logs.append(log_entry)

        # 写入日志文件
        self._write_log(line)

        # 不再发射信号,避免UI卡顿
        # self.output_received.emit(line)  # 已弃用

        # 尝试解析进度 (不发射信号)
        progress = self._parse_progress(line)
        if progress is not None:
            self.task.progress = progress
            # self.progress_updated.emit(progress)  # 已弃用

    def _parse_progress(self, line: str) -> int | None:
        """解析进度信息

        Nuitka 不会直接输出百分比,但可以根据某些关键字估算进度。

        Args:
            line: 输出行

        Returns:
            int | None: 进度值 (0-100),如果无法解析则返回 None
        """
        line_lower = line.lower()

        # 根据关键字估算进度
        progress_keywords = {
            "starting": 5,
            "parsing": 10,
            "importing": 15,
            "compiling": 30,
            "linking": 70,
            "copying": 90,
            "done": 100,
            "completed": 100,
            "finished": 100,
        }

        for keyword, value in progress_keywords.items():
            if keyword in line_lower:
                return value

        # 检测百分比 (某些插件可能会输出)
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            try:
                return int(percent_match.group(1))
            except ValueError:
                pass

        return None
