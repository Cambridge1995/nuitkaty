"""
基础页面模块

基础打包页面,包含入口文件选择、输出路径、图标、文件名等基本选项。
"""
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QButtonGroup
from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    LineEdit,
    ComboBox,
    RadioButton,
    CardWidget,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    InfoBar,
    InfoBarPosition,
)

from nuitkaty.src.core.config import get_config
from nuitkaty.src.core.nuitka_runner import NuitkaRunner
from nuitkaty.src.core.log_reader_thread import LogReaderThread
from nuitkaty.src.models.build_task import BuildTask


class BasePage(QWidget):
    """基础打包页面

    包含入口文件选择、输出路径、图标、文件名、单/多文件选择和打包按钮。
    """

    # 配置变更信号
    config_changed = Signal()

    def __init__(self, parent=None):
        """初始化基础页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()
        self.runner: NuitkaRunner | None = None
        self.log_reader_thread: LogReaderThread | None = None

        # 日志面板引用
        self.log_panel = None

        # 页面状态
        self.entry_file = ""
        self.output_dir = ""
        self.icon_path = ""
        self.output_filename = ""
        self.is_onefile = True  # True=单文件, False=多文件

        # 初始化界面
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        # 增加右边距以避免与右下角日志按钮和右上角主题切换按钮重叠
        layout.setContentsMargins(20, 20, 50, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("基础打包配置")
        layout.addWidget(title)

        # 入口文件选择
        layout.addWidget(self._create_entry_file_card())

        # 输出配置
        layout.addWidget(self._create_output_card())

        # 编译模式选择
        layout.addWidget(self._create_mode_card())

        # 打包按钮
        layout.addWidget(self._create_build_card())

        layout.addStretch()

    def _create_entry_file_card(self) -> CardWidget:
        """创建入口文件选择卡片

        Returns:
            CardWidget: 入口文件选择卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.DOCUMENT)
        title = StrongBodyLabel("入口文件")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("选择要打包的 Python 主程序文件（如 main.py）")
        desc.setStyleSheet("color: #666;")
        card_layout.addWidget(desc)

        # 文件路径输入和浏览按钮
        path_layout = QHBoxLayout()
        self.entry_file_edit = LineEdit()
        self.entry_file_edit.setPlaceholderText("例如: C:/myapp/main.py")
        self.entry_file_edit.setReadOnly(True)
        self.entry_file_edit.setClearButtonEnabled(False)

        browse_btn = PushButton("浏览...")
        browse_btn.clicked.connect(self._browse_entry_file)

        path_layout.addWidget(self.entry_file_edit)
        path_layout.addWidget(browse_btn)
        card_layout.addLayout(path_layout)

        return card

    def _create_output_card(self) -> CardWidget:
        """创建输出配置卡片

        Returns:
            CardWidget: 输出配置卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.FOLDER)
        title = StrongBodyLabel("输出配置")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("配置输出目录、文件名和图标")
        desc.setStyleSheet("color: #666;")
        card_layout.addWidget(desc)

        # 输出目录
        dir_layout = QHBoxLayout()
        dir_label = BodyLabel("输出目录:")
        dir_label.setFixedWidth(80)
        self.output_dir_edit = LineEdit()
        self.output_dir_edit.setPlaceholderText("例如: C:/output")
        self.output_dir_edit.setReadOnly(True)

        dir_browse_btn = PushButton("浏览...")
        dir_browse_btn.clicked.connect(self._browse_output_dir)

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.output_dir_edit)
        dir_layout.addWidget(dir_browse_btn)
        card_layout.addLayout(dir_layout)

        # 输出文件名
        filename_layout = QHBoxLayout()
        filename_label = BodyLabel("文件名:")
        filename_label.setFixedWidth(80)
        self.output_filename_edit = LineEdit()
        self.output_filename_edit.setPlaceholderText("例如: myapp.exe")
        self.output_filename_edit.textChanged.connect(self._on_config_changed)

        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.output_filename_edit)
        card_layout.addLayout(filename_layout)

        # 图标文件
        icon_layout = QHBoxLayout()
        icon_label = BodyLabel("图标:")
        icon_label.setFixedWidth(80)
        self.icon_path_edit = LineEdit()
        self.icon_path_edit.setPlaceholderText("可选: 选择 .ico 图标文件")
        self.icon_path_edit.setReadOnly(True)

        icon_browse_btn = PushButton("浏览...")
        icon_browse_btn.clicked.connect(self._browse_icon)

        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(icon_browse_btn)
        card_layout.addLayout(icon_layout)

        return card

    def _create_mode_card(self) -> CardWidget:
        """创建编译模式选择卡片

        Returns:
            CardWidget: 编译模式选择卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.SETTING)
        title = StrongBodyLabel("编译模式")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("选择打包方式：单文件生成一个 EXE,多文件生成包含 EXE 和依赖的文件夹")
        desc.setStyleSheet("color: #666;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        # 单选按钮组
        mode_layout = QHBoxLayout()

        self.onefile_radio = RadioButton("单文件模式 (--mode=onefile)")
        self.onedir_radio = RadioButton("多文件模式 (--mode=standalone)")
        self.onefile_radio.setChecked(True)

        # 按钮组
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.onefile_radio)
        self.mode_group.addButton(self.onedir_radio)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)

        mode_layout.addWidget(self.onefile_radio)
        mode_layout.addWidget(self.onedir_radio)
        mode_layout.addStretch()
        card_layout.addLayout(mode_layout)

        # 模式说明
        mode_desc = BodyLabel(
            "• 单文件: 生成单个 EXE,体积较大,启动稍慢,易于分发\n"
            "• 多文件: 生成文件夹,体积较小,启动较快,需要一起分发"
        )
        mode_desc.setStyleSheet("color: #888; font-size: 12px;")
        card_layout.addWidget(mode_desc)

        return card

    def _create_build_card(self) -> CardWidget:
        """创建打包按钮卡片

        Returns:
            CardWidget: 打包按钮卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # 打包状态提示区域 (默认隐藏)
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        # 状态提示标签
        from qfluentwidgets import BodyLabel
        self.build_status_label = BodyLabel("正在打包中,大约20~30min,请稍等...")
        self.build_status_label.setStyleSheet("color: #0078d4; font-size: 14px; padding: 10px;")
        self.build_status_label.hide()
        status_layout.addWidget(self.build_status_label)

        self.status_container = status_container
        card_layout.addWidget(status_container)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # 打包按钮
        self.build_btn = PrimaryPushButton("开始打包")
        self.build_btn.setFixedWidth(200)
        self.build_btn.setEnabled(False)
        self.build_btn.clicked.connect(self._on_build_clicked)

        btn_layout.addWidget(self.build_btn)

        # 取消按钮 (默认隐藏)
        self.cancel_btn = PushButton("取消打包")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.hide()
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_layout.addWidget(self.cancel_btn)

        card_layout.addLayout(btn_layout)

        return card

    def _browse_entry_file(self) -> None:
        """浏览选择入口文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择入口文件",
            "",
            "Python 文件 (*.py);;所有文件 (*.*)"
        )

        if file_path:
            self.entry_file = file_path
            self.entry_file_edit.setText(file_path)

            # 使用 config.temp() 更新内存中的配置（不保存到文件）
            self.config.temp(**{"nuitka.entry-file": file_path})

            # 自动设置输出目录和文件名，并使用 config.temp() 更新内存中的配置
            self._auto_set_output()

            # 更新按钮状态
            self._update_build_button_state()

            # 发射配置变更信号
            self.config_changed.emit()

    def _browse_output_dir(self) -> None:
        """浏览选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            ""
        )

        if dir_path:
            self.output_dir = dir_path
            self.output_dir_edit.setText(dir_path)

            # 使用 config.temp() 更新内存中的配置（不保存到文件）
            self.config.temp(**{"nuitka.output-dir": dir_path})
            print(f"[debug] to_command: {self.config.to_command()}")

            self._update_build_button_state()
            self.config_changed.emit()

    def _browse_icon(self) -> None:
        """浏览选择图标文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图标文件",
            "",
            "图标文件 (*.ico);;所有文件 (*.*)"
        )

        if file_path:
            self.icon_path = file_path
            self.icon_path_edit.setText(file_path)

            # 使用 config.temp() 更新内存中的配置（不保存到文件）
            self.config.temp(**{"nuitka.windows-icon-from-ico": file_path})
            print(f"[debug] to_command: {self.config.to_command()}")

            self.config_changed.emit()

    def _auto_set_output(self) -> None:
        """自动设置输出目录和文件名"""
        import os

        if not self.entry_file:
            return

        # 获取入口文件目录
        entry_dir = os.path.dirname(self.entry_file)
        entry_name = os.path.basename(self.entry_file)
        name_without_ext = os.path.splitext(entry_name)[0]

        # 准备临时更新的配置
        temp_updates = {}

        # 设置输出目录为入口文件所在目录下的 dist 文件夹
        if not self.output_dir:
            default_output = os.path.join(entry_dir, "dist")
            self.output_dir = default_output
            self.output_dir_edit.setText(default_output)
            temp_updates["nuitka.output-dir"] = default_output

        # 设置输出文件名
        if not self.output_filename:
            default_filename = f"{name_without_ext}.exe"
            self.output_filename = default_filename
            self.output_filename_edit.setText(default_filename)
            temp_updates["nuitka.output-filename"] = default_filename

        # 使用 config.temp() 批量更新内存中的配置（不保存到文件）
        if temp_updates:
            self.config.temp(**temp_updates)
            print(f"[debug] to_command: {self.config.to_command()}")

    def _on_mode_changed(self) -> None:
        """编译模式变更处理"""
        self.is_onefile = self.onefile_radio.isChecked()

        # 使用 config.set() 更新内存中的配置（不保存到文件）
        # 添加互斥逻辑
        if self.is_onefile:
            self.config.set("nuitka.onefile", True)
        else:
            self.config.set("nuitka.standalone", True)
        print(f"[debug] to_command: {self.config.to_command()}")

        self.config_changed.emit()

    def _on_config_changed(self) -> None:
        """配置变更处理"""
        self.output_filename = self.output_filename_edit.text()

        # 使用 config.temp() 更新内存中的配置（不保存到文件）
        if self.output_filename:
            self.config.temp(**{"nuitka.output-filename": self.output_filename})
            print(f"[debug] to_command: {self.config.to_command()}")

        self._update_build_button_state()

    def _update_build_button_state(self) -> None:
        """更新打包按钮状态"""
        enabled = bool(
            self.entry_file and
            self.output_dir and
            self.output_filename and
            self.output_filename.endswith(".exe")
        )
        self.build_btn.setEnabled(enabled)

    def _on_build_clicked(self) -> None:
        """打包按钮点击处理"""
        if self.runner and self.runner.is_running():
            # 正在运行,停止
            self._on_cancel_clicked()
            return

        # 获取配置
        entry_file = self.entry_file_edit.text()
        output_dir = self.output_dir_edit.text()
        output_filename = self.output_filename_edit.text()
        icon_path = self.icon_path_edit.text() or None

        # 构建命令
        mode = "onefile" if self.is_onefile else "standalone"
        command = self.config.to_command()

        # 创建日志文件路径
        import os
        log_file_path = os.path.join(output_dir, "nuitka_build.log")

        # 删除上一次的日志文件
        if os.path.exists(log_file_path):
            try:
                os.remove(log_file_path)
            except Exception as e:
                print(f"删除旧日志文件失败: {e}")

        # 创建任务
        task = BuildTask(
            entry_file=entry_file,
            output_dir=output_dir,
            output_filename=output_filename,
            command=command,
            log_file_path=log_file_path
        )

        # 创建并启动执行器
        self.runner = NuitkaRunner(task)
        self.runner.build_finished.connect(self._on_build_finished)
        self.runner.build_failed.connect(self._on_build_failed)
        self.runner.start()

        # 显示状态提示
        self.status_container.show()
        self.build_status_label.show()

        # 切换按钮
        self.build_btn.hide()
        self.cancel_btn.show()

        # 记录开始时间
        import time
        self._build_start_time = time.time()

        # 创建并启动日志读取线程 (每15秒读取一次)
        self.log_reader_thread = LogReaderThread(log_file_path, interval_ms=15000)
        self.log_reader_thread.logs_received.connect(self._on_logs_received)
        self.log_reader_thread.read_error.connect(self._on_log_read_error)
        self.log_reader_thread.start()

        # 清空日志面板
        if self.log_panel:
            self.log_panel.clear_logs()

    def _on_cancel_clicked(self) -> None:
        """取消按钮点击处理"""
        # 检查是否有正在运行的任务
        has_running_task = (self.runner and self.runner.is_running()) or \
                          (self.log_reader_thread and self.log_reader_thread.isRunning())

        if not has_running_task:
            # 没有正在运行的任务，直接恢复按钮状态
            self.cancel_btn.hide()
            self.build_btn.show()
            self.build_btn.setText("开始打包")
            self.build_btn.setEnabled(True)
            return

        # 开始取消流程
        self._start_cancellation()

    def _start_cancellation(self) -> None:
        """开始取消流程，显示等待状态"""
        # 更新状态标签
        self.build_status_label.setText("正在取消,请勿退出程序...")
        self.build_status_label.setStyleSheet("color: #FF6B00; font-size: 14px; padding: 10px;")

        # 禁用并隐藏取消按钮，显示"正在取消"按钮
        self.cancel_btn.hide()

        # 修改打包按钮为"正在取消"状态
        self.build_btn.setText("正在取消")
        self.build_btn.setEnabled(False)
        self.build_btn.show()

        # 断开信号连接，防止在停止过程中接收信号
        if self.runner:
            try:
                self.runner.build_finished.disconnect(self._on_build_finished)
                self.runner.build_failed.disconnect(self._on_build_failed)
            except Exception:
                pass  # 信号可能已经断开

        if self.log_reader_thread:
            try:
                self.log_reader_thread.logs_received.disconnect(self._on_logs_received)
                self.log_reader_thread.read_error.disconnect(self._on_log_read_error)
            except Exception:
                pass  # 信号可能已经断开

        # 停止 NuitkaRunner
        if self.runner and self.runner.isRunning():
            self.runner.stop()

        # 停止日志读取线程
        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        # 启动定时器检查线程是否已停止
        from PySide6.QtCore import QTimer
        self._cancel_check_timer = QTimer()
        self._cancel_check_timer.timeout.connect(self._check_cancellation_complete)
        self._cancel_check_timer.start(100)  # 每100ms检查一次

    def _check_cancellation_complete(self) -> None:
        """检查取消操作是否完成"""
        runner_stopped = not self.runner or not self.runner.isRunning()
        reader_stopped = not self.log_reader_thread or not self.log_reader_thread.isRunning()

        if runner_stopped and reader_stopped:
            # 所有线程都已停止，完成取消流程
            self._finish_cancellation()
        else:
            # 还有线程在运行，继续等待
            # 超时保护：如果超过10秒还没停止，强制完成
            if hasattr(self, '_cancel_start_time'):
                import time
                if time.time() - self._cancel_start_time > 10:
                    self._finish_cancellation()
            else:
                import time
                self._cancel_start_time = time.time()

    def _finish_cancellation(self) -> None:
        """完成取消流程，恢复UI状态"""
        # 停止检查定时器
        if hasattr(self, '_cancel_check_timer'):
            self._cancel_check_timer.stop()
            delattr(self, '_cancel_check_timer')

        if hasattr(self, '_cancel_start_time'):
            delattr(self, '_cancel_start_time')

        # 确保线程完全停止（最终清理）
        if self.runner:
            try:
                if self.runner.isRunning():
                    self.runner.wait(1000)  # 等待最多1秒
            except Exception:
                pass

        if self.log_reader_thread:
            try:
                if self.log_reader_thread.isRunning():
                    self.log_reader_thread.wait(1000)  # 等待最多1秒
            except Exception:
                pass

        # 隐藏状态区域
        self.build_status_label.hide()
        self.status_container.hide()

        # 恢复按钮状态
        self.cancel_btn.hide()
        self.build_btn.setText("开始打包")
        self.build_btn.setEnabled(True)

        # 显示取消完成提示
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.warning(
            title="已取消",
            content="打包已取消",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )

    def _on_build_finished(self, exit_code: int) -> None:
        """构建完成

        Args:
            exit_code: 退出码
        """
        # 停止日志读取线程
        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        # 隐藏状态区域
        self.build_status_label.hide()
        self.status_container.hide()

        # 切换按钮
        self.cancel_btn.hide()
        self.build_btn.show()
        self.build_btn.setText("开始打包")

        from qfluentwidgets import InfoBar, InfoBarPosition

        # 计算总耗时
        if hasattr(self, '_build_start_time'):
            import time
            elapsed = time.time() - self._build_start_time
            if elapsed > 60:
                elapsed_str = f"{int(elapsed / 60)} 分 {int(elapsed % 60)} 秒"
            else:
                elapsed_str = f"{int(elapsed)} 秒"
        else:
            elapsed_str = "未知"

        InfoBar.success(
            title="打包完成",
            content=f"构建成功完成! 退出码: {exit_code}, 耗时: {elapsed_str}",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000
        )

    def _on_build_failed(self, error_msg: str) -> None:
        """构建失败

        Args:
            error_msg: 错误消息
        """
        # 停止日志读取线程
        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        # 隐藏状态区域
        self.build_status_label.hide()
        self.status_container.hide()

        # 切换按钮
        self.cancel_btn.hide()
        self.build_btn.show()
        self.build_btn.setText("开始打包")

        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.error(
            title="打包失败",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000
        )

    @Slot(list)
    def _on_logs_received(self, log_lines: list[str]) -> None:
        """接收到新日志行 (来自 LogReaderThread)

        Args:
            log_lines: 日志行列表
        """
        if not log_lines or not self.log_panel:
            return

        # 使用批量更新方法提高性能
        # 分析日志级别 (使用第一条日志的级别)
        log_level = self._get_log_level(log_lines[0])
        self.log_panel.append_logs_batch(log_lines, log_level)

    @Slot(str)
    def _on_log_read_error(self, error_msg: str) -> None:
        """日志读取错误 (来自 LogReaderThread)

        Args:
            error_msg: 错误消息
        """
        print(f"日志读取错误: {error_msg}")

    def set_log_panel(self, log_panel) -> None:
        """设置日志面板

        Args:
            log_panel: 日志面板对象
        """
        self.log_panel = log_panel

    def _get_log_level(self, line: str) -> str:
        """从日志行获取日志级别

        Args:
            line: 日志行

        Returns:
            str: 日志级别 (INFO/WARNING/ERROR/DEBUG)
        """
        line_lower = line.lower()

        # 错误关键词
        error_keywords = ["error", "failed", "exception", "traceback", "critical"]
        if any(keyword in line_lower for keyword in error_keywords):
            return "ERROR"

        # 警告关键词
        warning_keywords = ["warning", "warn"]
        if any(keyword in line_lower for keyword in warning_keywords):
            return "WARNING"

        # 调试关键词
        debug_keywords = ["debug", "trace"]
        if any(keyword in line_lower for keyword in debug_keywords):
            return "DEBUG"

        return "INFO"
