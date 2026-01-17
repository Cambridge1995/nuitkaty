"""
配置向导对话框模块

首次启动时显示的配置向导,引导用户完成 Python 解释器、pip 镜像源和 GCC 编译器的配置。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QFileDialog, QStackedWidget, QPushButton, QTextEdit
)
from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    ComboBox,
    ProgressBar,
    IndeterminateProgressRing,
    Flyout,
    FlyoutAnimationType,
    InfoBar,
    InfoBarPosition,
    FluentIcon,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    isDarkTheme,
    MessageBoxBase,
)

from nuitkaty.src.core.config import get_config
from nuitkaty.src.core.path_detector import PathDetector


class ConfigWizard(QDialog):
    """配置向导对话框

    三步配置向导: Python 解释器 -> pip 镜像源 -> GCC 编译器
    """

    # 配置完成信号
    config_finished = Signal()

    def __init__(self, parent=None):
        """初始化配置向导

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        self.config = get_config()
        self.detected_pythons = []
        self.detected_mirrors = []
        self.detected_gcc = {"msvc": None, "mingw64": None}

        # 临时配置
        self.python_path = ""
        self.python_auto_detected = False
        self.pip_mirror_url = ""
        self.pip_auto_detected = False
        self.gcc_type = "auto"  # auto, msvc, mingw64
        self.gcc_path = ""
        self.gcc_auto_detected = False
        self.gcc_types = []  # 存储 ComboBox 中每个选项对应的编译器类型

        # 当前页面索引
        self.current_page_index = 0
        self.total_pages = 5

        # 设置窗口属性
        self.setWindowTitle("配置向导 - Nuitkaty")
        self.resize(700, 550)
        self.setWindowFlags(Qt.WindowType.Dialog)

        # 创建页面堆栈
        self.page_stack = QStackedWidget()
        self.pages = []

        # 创建向导页面
        self._create_welcome_page()
        self._create_python_page()
        self._create_pip_page()
        self._create_gcc_page()
        self._create_complete_page()

        # 创建导航按钮
        self._create_navigation_buttons()

        # 设置对话框布局
        self._setup_dialog_layout()

        # 初始化按钮状态
        self._update_navigation_buttons()

    def _create_welcome_page(self) -> None:
        """创建欢迎页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 欢迎文字
        title = SubtitleLabel("欢迎使用 Nuitka Python 打包工具")
        desc = BodyLabel(
            "本工具将帮助您将 Python 程序打包为独立的 Windows EXE 可执行文件。\n\n"
            "配置向导将引导您完成以下设置:\n"
            "• Python 解释器路径\n"
            "• pip 镜像源（用于加速依赖下载）\n"
            "• GCC 编译器（用于编译 C 代码）\n\n"
            "配置过程大约需要 2-3 分钟。"
        )
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()

        self.page_stack.addWidget(page)
        self.pages.append({"title": "欢迎使用 Nuitkaty", "subtitle": "首次使用需要完成一些基本配置"})

    def _create_python_page(self) -> None:
        """创建 Python 解释器配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明文字
        desc = BodyLabel("Nuitka 需要使用 Python 解释器来编译您的程序。"
                        "请选择 Python 3.8 或更高版本。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Python 路径选择
        path_layout = QHBoxLayout()
        self.python_combo = ComboBox()
        self.python_combo.setMinimumWidth(400)
        self.python_combo.setPlaceholderText("请选择 Python 解释器")

        detect_btn = PushButton("自动检测")
        detect_btn.clicked.connect(self._detect_python)

        browse_btn = PushButton("浏览...")
        browse_btn.clicked.connect(self._browse_python)

        path_layout.addWidget(self.python_combo)
        path_layout.addWidget(detect_btn)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        layout.addStretch()

        self.page_stack.addWidget(page)
        self.pages.append({"title": "配置 Python 解释器", "subtitle": "选择用于打包的 Python 解释器"})

    def _create_pip_page(self) -> None:
        """创建 pip 镜像源配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明文字
        desc = BodyLabel("选择一个快速pip镜像源可以显著加快依赖包的下载速度（自动选择可以自动测速并选择最快的镜像源）。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 镜像源选择区域
        mirror_container = QWidget()
        mirror_layout = QVBoxLayout(mirror_container)
        mirror_layout.setContentsMargins(0, 0, 0, 0)
        mirror_layout.setSpacing(10)

        # 镜像源下拉框
        self.mirror_combo = ComboBox()
        self.mirror_combo.setMinimumWidth(500)
        self.mirror_combo.setPlaceholderText("请选择镜像源")

        # 添加所有默认镜像源选项（从 PathDetector 获取）
        from nuitkaty.src.core.path_detector import PathDetector
        default_mirrors = PathDetector.DEFAULT_PIP_MIRRORS
        for mirror in default_mirrors:
            self.mirror_combo.addItem(mirror['name'])
            # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
            self.mirror_combo.setItemData(self.mirror_combo.count() - 1, mirror['url'])

        # 默认选择第一个（PyPI官方）
        # 使用 blockSignals 防止触发 currentIndexChanged 信号
        self.mirror_combo.blockSignals(True)
        self.mirror_combo.setCurrentIndex(0)
        self.mirror_combo.blockSignals(False)

        # 连接信号：用户手动更改镜像源选择时，标记为手动选择
        self.mirror_combo.currentIndexChanged.connect(self._on_mirror_combo_changed)

        # 自动选择按钮和加载指示器
        auto_layout = QHBoxLayout()
        auto_layout.setSpacing(10)

        self.auto_select_btn = PrimaryPushButton("自动选择")
        self.auto_select_btn.clicked.connect(self._on_auto_select_clicked)

        # IndeterminateProgressRing 加载指示器（初始隐藏）- 这是真正转圈的动画
        self.test_progress_ring = IndeterminateProgressRing(self)
        self.test_progress_ring.setFixedSize(30, 30)
        self.test_progress_ring.hide()

        # 提示标签（初始隐藏）
        self.test_hint_label = BodyLabel("正在测速中，请勿操作...")
        self.test_hint_label.hide()

        auto_layout.addWidget(self.auto_select_btn)
        auto_layout.addWidget(self.test_progress_ring)
        auto_layout.addWidget(self.test_hint_label)
        auto_layout.addStretch()

        mirror_layout.addWidget(self.mirror_combo)
        mirror_layout.addLayout(auto_layout)

        layout.addWidget(mirror_container)

        # 结果标签
        self.speed_result = BodyLabel("")
        self.speed_result.hide()
        layout.addWidget(self.speed_result)

        layout.addStretch()

        self.page_stack.addWidget(page)
        self.pages.append({"title": "配置 pip 镜像源", "subtitle": "选择最快的镜像源以加速依赖下载"})

    def _create_gcc_page(self) -> None:
        """创建 GCC 编译器配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明文字
        desc = BodyLabel("Nuitka 需要 C 编译器来将 Python 代码编译为机器码。"
                        "推荐使用 MSVC 或 MinGW64。")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # GCC 路径选择 - 与 Python 解释器页面类似的布局
        path_layout = QHBoxLayout()
        self.gcc_combo = ComboBox()
        self.gcc_combo.setMinimumWidth(400)
        self.gcc_combo.setPlaceholderText("请选择 GCC 编译器")

        detect_btn = PushButton("自动检测")
        detect_btn.clicked.connect(self._detect_gcc)

        browse_btn = PushButton("浏览...")
        browse_btn.clicked.connect(self._browse_gcc)

        path_layout.addWidget(self.gcc_combo)
        path_layout.addWidget(detect_btn)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 检测结果提示
        self.gcc_status = BodyLabel("点击「自动检测」按钮或「浏览」选择编译器...")
        self.gcc_status.setWordWrap(True)
        layout.addWidget(self.gcc_status)

        # 下载按钮
        download_layout = QHBoxLayout()
        download_layout.addStretch()

        download_btn = PushButton("下载 GCC")
        download_btn.clicked.connect(self._download_gcc)

        download_layout.addWidget(download_btn)
        layout.addLayout(download_layout)

        layout.addStretch()

        self.page_stack.addWidget(page)
        self.pages.append({"title": "配置 GCC 编译器", "subtitle": "选择 C 编译器用于编译生成的 C 代码"})

    def _create_complete_page(self) -> None:
        """创建完成页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 完成文字
        title = SubtitleLabel("配置完成！")
        desc = BodyLabel(
            "您已完成所有必要配置,现在可以开始使用 Nuitka 打包工具了。\n\n"
            "• 如果需要修改配置,可以随时进入「设置」页面\n"
            "• 点击「完成」开始使用工具"
        )
        desc.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()

        self.page_stack.addWidget(page)
        self.pages.append({"title": "配置完成", "subtitle": "所有必要配置已完成"})

    def _create_navigation_buttons(self) -> None:
        """创建导航按钮"""
        # 上一步按钮
        self.prev_btn = PushButton("上一步")
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.prev_btn.setEnabled(False)  # 第一页禁用

        # 下一步按钮
        self.next_btn = PrimaryPushButton("下一步")
        self.next_btn.clicked.connect(self._on_next_clicked)

        # 取消按钮 - 取消配置向导则退出整个应用程序
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

    def _setup_dialog_layout(self) -> None:
        """设置对话框布局"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 添加页面堆栈
        layout.addWidget(self.page_stack)

        # 添加导航按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 10)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.prev_btn)
        button_layout.addWidget(self.next_btn)

        layout.addLayout(button_layout)

    def _on_prev_clicked(self) -> None:
        """上一步按钮点击处理"""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self._update_navigation_buttons()

    def _on_next_clicked(self) -> None:
        """下一步按钮点击处理"""
        if self.current_page_index < self.total_pages - 1:
            # 进入下一页时触发相应操作
            self._on_page_leaving(self.current_page_index)
            self.current_page_index += 1
            self.page_stack.setCurrentIndex(self.current_page_index)
            self._on_page_entering(self.current_page_index)
            self._update_navigation_buttons()
        else:
            # 最后一页，完成向导
            self.accept()

    def _on_page_leaving(self, page_index: int) -> None:
        """离开页面时的处理

        Args:
            page_index: 即将离开的页面索引
        """
        # 从 Python 页面离开时,保存选择的 Python 路径
        if page_index == 1:
            if self.python_combo.currentData():
                self.python_path = self.python_combo.currentData()

        # 从 pip 页面离开时,保存选择的镜像源
        elif page_index == 2:
            if self.mirror_combo.currentData():
                self.pip_mirror_url = self.mirror_combo.currentData()

    def _on_page_entering(self, page_index: int) -> None:
        """进入页面时的处理

        Args:
            page_index: 即将进入的页面索引
        """
        # 进入 Python 页面时自动检测
        if page_index == 1:
            self._detect_python()

        # pip 页面不再自动测试，需要用户点击"自动选择"按钮
        # elif page_index == 2:
        #     self._test_mirrors()

        # 进入 GCC 页面时自动检测
        elif page_index == 3:
            self._detect_gcc()

        # 进入完成页面时保存配置
        elif page_index == 4:
            self._save_config()

    def _update_navigation_buttons(self) -> None:
        """更新导航按钮状态"""
        # 更新上一步按钮
        self.prev_btn.setEnabled(self.current_page_index > 0)

        # 更新下一步/完成按钮
        if self.current_page_index == self.total_pages - 1:
            self.next_btn.setText("完成")
        else:
            self.next_btn.setText("下一步")

    def _detect_python(self) -> None:
        """检测系统中的 Python 解释器"""
        detector = PathDetector()
        self.detected_pythons = detector.detect_python_interpreters()

        self.python_combo.clear()

        if not self.detected_pythons:
            self.python_combo.setPlaceholderText("未检测到 Python,请手动选择")
            InfoBar.warning(
                title="未找到 Python",
                content="未检测到 Python 解释器,请点击「浏览」手动选择",
                parent=self,
                position=InfoBarPosition.TOP
            )
        else:
            # 添加检测到的所有 Python 环境
            for py in self.detected_pythons:
                # PathDetector 返回格式: {"name": "Python 3.11.x", "path": "..."}
                # 显示格式: "Python 3.11.x - C:\..."
                display_text = f"{py['name']} - {py['path']}"
                self.python_combo.addItem(display_text)
                # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
                self.python_combo.setItemData(self.python_combo.count() - 1, py['path'])

            # 阻断信号，防止 setCurrentIndex 触发 currentIndexChanged
            self.python_combo.blockSignals(True)
            # 默认选择第一个
            self.python_combo.setCurrentIndex(0)
            self.python_combo.blockSignals(False)
            # 标记为自动检测
            self.python_auto_detected = True

            # 移除成功提示框，避免干扰用户
            # InfoBar.success(
            #     title="检测成功",
            #     content=f"检测到 {len(self.detected_pythons)} 个 Python 解释器,请选择要使用的版本",
            #     parent=self,
            #     position=InfoBarPosition.TOP,
            #     duration=3000
            # )

    def _browse_python(self) -> None:
        """浏览选择 Python 解释器"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Python 解释器",
            "",
            "Python 可执行文件 (python.exe);;所有文件 (*.*)"
        )

        if file_path:
            self.python_combo.addItem(file_path)
            # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
            self.python_combo.setItemData(self.python_combo.count() - 1, file_path)
            self.python_combo.blockSignals(True)
            self.python_combo.setCurrentIndex(self.python_combo.count() - 1)
            self.python_combo.blockSignals(False)
            # 标记为手动选择
            self.python_auto_detected = False

    def _on_auto_select_clicked(self) -> None:
        """自动选择按钮点击处理 - 测试速度并选择最快的镜像源"""
        # 禁用所有导航按钮和控件
        self._set_navigation_enabled(False)
        self.mirror_combo.setEnabled(False)
        self.auto_select_btn.setEnabled(False)

        # 显示加载状态 - ProgressRing 会自动开始转圈动画
        self.test_progress_ring.show()
        self.test_hint_label.show()
        self.speed_result.hide()

        # 开始测试镜像源速度
        self._test_mirrors()

    def _on_mirror_combo_changed(self) -> None:
        """镜像源下拉框选择变化处理

        当用户手动更改镜像源选择时，标记为手动选择（非自动检测）。
        """
        # 在自动选择过程中会触发此信号，需要过滤掉
        # 只有在不在测试过程中时才标记为手动选择
        if not self.test_progress_ring.isVisible():
            self.pip_auto_detected = False

    def _set_navigation_enabled(self, enabled: bool) -> None:
        """设置导航按钮的启用状态

        Args:
            enabled: 是否启用
        """
        self.prev_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)

    def _test_mirrors(self) -> None:
        """测试镜像源速度（带重试机制）"""
        self.speed_result.hide()
        self.mirror_combo.clear()

        # 异步测试镜像源
        from PySide6.QtCore import QThread

        # 加载当前配置（用于获取用户自定义的镜像源列表）
        config = self.config

        class MirrorTestThread(QThread):
            progress = Signal(int)
            finished = Signal(list)
            retry = Signal(int, str)  # (重试次数, 镜像源名称)

            def __init__(self, config, max_retries: int = 2):
                super().__init__()
                self.config = config
                self.max_retries = max_retries

            def run(self):
                import time
                from nuitkaty.src.core.path_detector import PathDetector
                from nuitkaty.src.utils.error_handler import RetryHandler

                detector = PathDetector()

                # 使用重试机制测试镜像源,传递 config 参数
                def test_with_retry():
                    return detector.detect_pip_mirrors(timeout=3, config=self.config)

                try:
                    mirrors = RetryHandler.retry_on_error(
                        test_with_retry,
                        max_retries=self.max_retries,
                        retry_exceptions=(ConnectionError, TimeoutError, OSError),
                        on_retry=lambda attempt, e: self.retry.emit(attempt, f"网络异常,正在重试... ({str(e)})")
                    )
                    self.progress.emit(100)
                    self.finished.emit(mirrors)
                except Exception as e:
                    # 重试失败，返回空列表
                    self.progress.emit(100)
                    self.finished.emit([])

        self.test_thread = MirrorTestThread(config, max_retries=2)
        # ProgressRing 不需要设置进度值，忽略 progress 信号
        # self.test_thread.progress.connect(self.speed_progress.setValue)
        self.test_thread.finished.connect(self._on_mirrors_tested)
        self.test_thread.retry.connect(self._on_mirror_retry)
        self.test_thread.start()

    def _on_mirror_retry(self, attempt: int, message: str) -> None:
        """镜像源测试重试回调

        Args:
            attempt: 当前重试次数
            message: 重试消息
        """
        self.speed_result.setText(f"🔄 网络不稳定，第 {attempt} 次重试中...")
        self.speed_result.show()

    def _on_mirrors_tested(self, mirrors: list) -> None:
        """镜像源测试完成回调

        Args:
            mirrors: 镜像源列表
        """
        # 隐藏加载状态 - ProgressRing 会自动停止动画
        self.test_progress_ring.hide()
        self.test_hint_label.hide()

        # 恢复所有按钮和控件
        self._set_navigation_enabled(True)
        self.mirror_combo.setEnabled(True)
        self.auto_select_btn.setEnabled(True)

        self.detected_mirrors = mirrors

        # 清空现有选项
        self.mirror_combo.clear()

        if not mirrors:
            self.mirror_combo.setPlaceholderText("无法连接到任何镜像源")
            self.speed_result.setText("⚠️ 网络连接失败,请检查网络后重试")
            self.speed_result.show()
        else:
            # 重新填充测试结果
            for mirror in mirrors:
                # 修复: 使用 'time' 而非 'response_time'
                if mirror['time'] == -1:
                    # 不可用的镜像源
                    display_text = f"{mirror['name']} (不可用)"
                else:
                    display_text = f"{mirror['name']} ({mirror['time']:.0f}ms)"
                self.mirror_combo.addItem(display_text)
                # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
                self.mirror_combo.setItemData(self.mirror_combo.count() - 1, mirror['url'])

            # 选择第一个可用的镜像源（最快的）
            self.mirror_combo.blockSignals(True)
            self.mirror_combo.setCurrentIndex(0)
            self.mirror_combo.blockSignals(False)

            fastest = mirrors[0]
            if fastest['time'] == -1:
                self.speed_result.setText(f"⚠️ 未检测到可用镜像源")
            else:
                self.speed_result.setText(f"✓ 最快镜像源: {fastest['name']} ({fastest['time']:.0f}ms)")
            self.speed_result.show()

            if fastest['time'] != -1:
                # 标记为自动选择
                self.pip_auto_detected = True
                InfoBar.success(
                    title="测试完成",
                    content=f"已选择最快的镜像源: {fastest['name']}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

    def _detect_gcc(self) -> None:
        """检测 GCC 编译器

        检测优先级：MSVC（推荐） > MinGW64
        """
        detector = PathDetector()
        compilers = detector.detect_gcc()

        # 清空 ComboBox 和类型列表
        self.gcc_combo.clear()
        self.gcc_types.clear()

        # 将返回的列表转换为期望的字典格式
        self.detected_gcc = {"msvc": None, "mingw64": None}
        for compiler in compilers:
            if compiler["type"] == "msvc":
                self.detected_gcc["msvc"] = {
                    "name": compiler["name"],
                    "path": compiler["path"]
                }
            elif compiler["type"] == "mingw64":
                self.detected_gcc["mingw64"] = {
                    "name": compiler["name"],
                    "path": compiler["path"]
                }

        # Nuitka 推荐优先级：MSVC > MinGW64
        # 按优先级将检测到的编译器添加到 ComboBox
        has_msvc = bool(self.detected_gcc['msvc'])
        has_mingw64 = bool(self.detected_gcc['mingw64'])

        if has_msvc:
            # MSVC 是 Nuitka 在 Windows 上的首选编译器
            display_text = f"⭐ {self.detected_gcc['msvc']['name']} (推荐) - {self.detected_gcc['msvc']['path']}"
            self.gcc_combo.addItem(display_text)
            # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
            self.gcc_combo.setItemData(self.gcc_combo.count() - 1, self.detected_gcc['msvc']['path'])
            self.gcc_types.append("msvc")

            # 默认选择 MSVC
            self.gcc_type = "msvc"
            self.gcc_path = self.detected_gcc['msvc']['path']

        if has_mingw64:
            # MinGW64 作为备选
            display_text = f"{self.detected_gcc['mingw64']['name']} - {self.detected_gcc['mingw64']['path']}"
            self.gcc_combo.addItem(display_text)
            # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
            self.gcc_combo.setItemData(self.gcc_combo.count() - 1, self.detected_gcc['mingw64']['path'])
            self.gcc_types.append("mingw64")

            # 只有在没有 MSVC 时才默认选择 MinGW64
            if not has_msvc:
                self.gcc_type = "mingw64"
                self.gcc_path = self.detected_gcc['mingw64']['path']

        # 更新状态提示
        if self.gcc_combo.count() > 0:
            # 标记为自动检测
            self.gcc_auto_detected = True
            if has_msvc and has_mingw64:
                self.gcc_status.setText(
                    f"✓ 检测到 {len(compilers)} 个编译器\n"
                    f"⭐ 已默认选择 MSVC（Nuitka 推荐）\n"
                    f"如需切换，请在下拉框中选择"
                )
            elif has_msvc:
                self.gcc_status.setText(
                    f"✓ 检测到 MSVC\n"
                    f"{self.detected_gcc['msvc']['name']}\n\n"
                    f"⭐ 这是 Nuitka 在 Windows 上的推荐编译器"
                )
            else:  # 只有 MinGW64
                self.gcc_status.setText(
                    f"✓ 检测到 MinGW64\n"
                    f"{self.detected_gcc['mingw64']['name']}"
                )

            InfoBar.success(
                title="检测成功",
                content=f"已检测到 {len(compilers)} 个编译器，已默认选择推荐的编译器",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        else:
            self.gcc_status.setText(
                "⚠️ 未检测到 GCC 编译器\n\n"
                "您可以点击「下载 GCC」获取编译器，\n"
                "或点击「浏览」手动选择已安装的编译器路径。"
            )
            InfoBar.warning(
                title="未找到编译器",
                content="请下载并安装编译器，或手动选择编译器路径",
                parent=self,
                position=InfoBarPosition.TOP
            )

        # 默认选择第一个（MSVC，如果检测到的话）
        if self.gcc_combo.count() > 0:
            self.gcc_combo.blockSignals(True)
            self.gcc_combo.setCurrentIndex(0)
            self.gcc_combo.blockSignals(False)
            # 更新选中状态
            self._on_gcc_combo_changed()

        # 连接选择变化信号
        self.gcc_combo.currentIndexChanged.connect(self._on_gcc_combo_changed)

    def _on_gcc_combo_changed(self) -> None:
        """GCC 编译器选择变化处理

        当用户手动更改 GCC 选择时，标记为手动选择（非自动检测）。
        注意：此信号在 _detect_gcc() 完成后才连接，所以不会影响自动检测过程。
        """
        index = self.gcc_combo.currentIndex()
        if index >= 0 and index < len(self.gcc_types):
            self.gcc_type = self.gcc_types[index]
        if self.gcc_combo.currentData():
            self.gcc_path = self.gcc_combo.currentData()
        else:
            self.gcc_path = ""
        # 标记为手动选择
        self.gcc_auto_detected = False

    def _browse_gcc(self) -> None:
        """浏览选择 GCC 编译器路径"""
        # 支持选择目录或文件
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        # 询问用户是选择目录还是文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 GCC 编译器",
            "",
            "编译器文件 (cl.exe;gcc.exe;g++.exe);;所有文件 (*.*)"
        )

        if file_path:
            # 验证文件是否为编译器
            file_name = os.path.basename(file_path).lower()
            if file_name in ['cl.exe', 'gcc.exe', 'g++.exe']:
                # 确定编译器类型
                if file_name == 'cl.exe':
                    gcc_type = "msvc"
                    gcc_name = "MSVC 编译器"
                else:
                    gcc_type = "mingw64"
                    gcc_name = "MinGW64 编译器"

                # 获取父目录作为路径
                gcc_path = os.path.dirname(file_path)

                # 添加到 ComboBox
                display_text = f"{gcc_name} (手动选择) - {gcc_path}"
                self.gcc_combo.addItem(display_text)
                # qfluentwidgets ComboBox 的 addItem() 不返回索引，需要使用 count()-1
                self.gcc_combo.setItemData(self.gcc_combo.count() - 1, gcc_path)
                self.gcc_types.append(gcc_type)
                self.gcc_combo.blockSignals(True)
                self.gcc_combo.setCurrentIndex(self.gcc_combo.count() - 1)
                self.gcc_combo.blockSignals(False)

                # 更新状态
                self.gcc_type = gcc_type
                self.gcc_path = gcc_path
                # 标记为手动选择
                self.gcc_auto_detected = False
                self.gcc_status.setText(f"✓ 已选择 {gcc_name}\n路径: {gcc_path}")

                InfoBar.success(
                    title="选择成功",
                    content=f"已选择 {gcc_name}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
            else:
                InfoBar.error(
                    title="文件无效",
                    content="请选择 cl.exe、gcc.exe 或 g++.exe 文件",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

    def _download_gcc(self) -> None:
        """下载 GCC 编译器"""
        dialog = DownloadGCCDialog(self)
        dialog.exec()

    def _save_config(self) -> None:
        """保存配置"""
        # 从当前下拉框选择获取最新的配置值（确保使用用户最终选择）
        # Python 路径
        py_index = self.python_combo.currentIndex()
        if py_index >= 0:
            py_data = self.python_combo.itemData(py_index)
            if py_data:
                self.python_path = py_data

        # pip 镜像源 URL
        mirror_index = self.mirror_combo.currentIndex()
        if mirror_index >= 0:
            mirror_data = self.mirror_combo.itemData(mirror_index)
            if mirror_data:
                self.pip_mirror_url = mirror_data

        # GCC 路径和类型
        gcc_index = self.gcc_combo.currentIndex()
        if gcc_index >= 0:
            gcc_data = self.gcc_combo.itemData(gcc_index)
            if gcc_data:
                self.gcc_path = gcc_data
                if gcc_index >= 0 and gcc_index < len(self.gcc_types):
                    self.gcc_type = self.gcc_types[gcc_index]

        # 创建并保存配置 - 使用新的 Config 类
        # 准备所有配置更新
        updates = {}

        # 保存 Python 配置 - 使用 python.path
        updates["python.path"] = self.python_path

        # 保存 pip 配置
        updates["pip.mirror_url"] = self.pip_mirror_url

        # 保存完整的 mirrors 列表
        if self.detected_mirrors:
            mirrors_to_save = self.detected_mirrors
        else:
            # 使用默认镜像源列表
            from nuitkaty.src.core.path_detector import PathDetector
            default_mirrors = PathDetector.DEFAULT_PIP_MIRRORS
            # default_mirrors 是字典列表，直接使用
            mirrors_to_save = default_mirrors

        # 更新 mirrors 列表
        for i, mirror in enumerate(mirrors_to_save):
            updates[f"pip.mirrors.{i}.name"] = mirror['name']
            updates[f"pip.mirrors.{i}.url"] = mirror['url']

        # 保存 GCC 配置
        if self.gcc_type and self.gcc_type != "auto":
            updates["gcc.compiler_type"] = self.gcc_type
        if self.gcc_path:
            updates["gcc.path"] = self.gcc_path

        # 设置首次运行完成标记
        updates["system.first_run_complete"] = True

        # 批量更新配置
        self.config.update(**updates)

    def _on_cancel_clicked(self) -> None:
        """取消按钮点击处理 - 直接退出应用程序"""
        import sys
        from PySide6.QtWidgets import QApplication
        # 关闭向导对话框
        self.reject()
        # 退出整个应用程序
        QApplication.instance().quit()
        sys.exit(0)

    def accept(self) -> None:
        """接受对话框,完成配置"""
        # 发射完成信号
        self.config_finished.emit()

        # 关闭向导
        super().accept()


class DownloadGCCDialog(QDialog):
    """下载 GCC 对话框

    显示 GCC 下载链接和安装说明，内容可选择可复制。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("下载 GCC 编译器")
        self.resize(650, 450)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # 标题
        title = SubtitleLabel("下载 GCC 编译器")
        layout.addWidget(title)

        # 文本区域
        self.textWidget = QTextEdit()
        self.textWidget.setReadOnly(True)
        self.textWidget.setPlainText(
            "Nuitka 需要 C 编译器才能工作。请选择以下方式之一安装 GCC：\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "方式一：安装 MSYS2（推荐）\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 访问 MSYS2 官网下载并安装\n"
            "   下载链接: https://www.msys2.org/\n\n"
            "2. 安装完成后，打开 MSYS2 终端\n"
            "   运行命令: pacman -S mingw-w64-x86_64-gcc\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "方式二：安装 MinGW-w64\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 访问 MinGW-w64 GitHub Releases\n"
            "   下载链接: https://github.com/niXman/mingw-builds-binaries/releases\n\n"
            "2. 下载最新的 x86_64-posix-seh 版本\n\n"
            "3. 解压到指定目录，并将 bin 目录添加到系统 PATH\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "方式三：使用 Visual Studio（已安装）\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "如果您的系统已安装 Visual Studio，\n"
            "Nuitka 可以自动使用 MSVC 编译器。\n\n"
            "返回配置向导，点击「自动检测」按钮。\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "安装完成后:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "点击配置向导中的「自动检测」按钮，\n"
            "系统将自动查找已安装的编译器。\n"
        )

        # 设置样式
        self.textWidget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        font = self.textWidget.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.textWidget.setFont(font)

        layout.addWidget(self.textWidget)

        # 关闭按钮
        from qfluentwidgets import PrimaryPushButton
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = PrimaryPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
