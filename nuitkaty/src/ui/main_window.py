"""
主窗口模块

应用主窗口,基于 FluentWindow,包含导航栏和各功能页面。
"""
import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    FluentIcon,
    TransparentToolButton,
)

from nuitkaty.src.core.config import get_config
from nuitkaty.src.ui.widgets.config_wizard import ConfigWizard
from nuitkaty.src.ui.widgets.log_panel import CollapsibleLogPanel
from nuitkaty.src.ui.pages.base_page import BasePage
from nuitkaty.src.ui.pages.advanced_page import AdvancedPage
from nuitkaty.src.ui.pages.plugin_page import PluginPage
from nuitkaty.src.ui.pages.embed_page import EmbedPage
from nuitkaty.src.ui.pages.settings_page import SettingsPage
# 暂时禁用专精页面
# from nuitkaty.src.ui.pages.expert_page import ExpertPage
from nuitkaty.src.ui.pages.command_page import CommandPage


class MainWindow(FluentWindow):
    """主窗口

    基于 FluentWindow 的主应用窗口,包含导航栏和日志面板按钮。
    """

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 初始化配置
        self.config = get_config()

        # 窗口初始化完成标志（用于防止resizeEvent在初始化期间保存尺寸）
        self._window_initialized = False

        # 初始化日志面板
        self.log_panel = CollapsibleLogPanel(self)

        # 设置窗口属性
        self.setWindowTitle("Nuitkaty - Nuitka Python 打包工具")

        # 检测首次启动（同时加载配置）
        self._check_first_run()

        # 初始化界面
        self._init_ui()

        # 从配置加载窗口尺寸，允许用户自由调整
        window_size = self.config.get("ui.window_size", [1200, 800])
        window_width, window_height = window_size
        self.resize(window_width, window_height)


        # 修改FluentWindow内部组件的尺寸策略，允许窗口自由调整
        from PySide6.QtWidgets import QSizePolicy
        self.stackedWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        # 移除navigationInterface的最小尺寸限制
        self.navigationInterface.setMinimumSize(0, 0)
        self.stackedWidget.setMinimumSize(0, 0)

        # 连接日志面板到 BasePage 的 NuitkaRunner 信号
        self._connect_log_signals()

        # 连接各页面配置变更信号到命令页面
        self._connect_page_signals()

        # 连接页面切换事件，用于刷新页面配置
        self.stackedWidget.currentChanged.connect(self._on_page_changed)

    def _check_first_run(self) -> None:
        """检测是否为首次运行

        如果配置文件不存在或首次运行未完成,则显示配置向导。
        如果配置加载失败,使用默认配置并显示警告。
        """
        # 检查首次运行标记
        if not self.config.get("system.first_run_complete", False):
            # 首次运行未完成,显示配置向导
            if not self._show_config_wizard():
                # 用户取消了配置向导，退出应用
                import sys
                from PySide6.QtWidgets import QApplication
                QApplication.instance().quit()
                sys.exit(0)
            else:
                # 配置向导完成后重新加载
                self.config.reload()

    def _show_config_wizard(self) -> None:
        """显示配置向导

        Returns:
            bool: 用户是否完成了配置向导（True=完成，False=取消）
        """
        wizard = ConfigWizard(self)
        result = wizard.exec()

        # QDialog.Accepted = 1, QDialog.Rejected = 0
        if result == QDialog.DialogCode.Accepted:
            # 用户完成了配置向导
            # 重新加载配置
            self.config.reload()
            return True
        else:
            # 用户取消了配置向导
            return False

    def showEvent(self, event) -> None:
        """窗口显示事件

        确保窗口尺寸使用config中的值，而不是FluentWindow自动调整的尺寸。
        使用QTimer延迟执行，确保在FluentWindow完成所有自动调整后再设置尺寸。
        """
        super().showEvent(event)
        # 使用更长的延迟，确保FluentWindow完全完成所有自动调整
        from PySide6.QtCore import QTimer
        QTimer.singleShot(300, self._apply_config_window_size)

    def _apply_config_window_size(self) -> None:
        """应用config中的窗口尺寸

        考虑DPI缩放因素，确保窗口在屏幕上显示为正确的物理尺寸。
        """
        if self.config:
            window_size = self.config.get("ui.window_size", [1200, 800])
            window_width, window_height = window_size
            self.resize(window_width, window_height)
            # 标记窗口初始化完成，之后resizeEvent才会保存尺寸
            self._window_initialized = True

    def closeEvent(self, event) -> None:
        """窗口关闭事件处理

        清理所有后台线程，然后关闭窗口。

        Args:
            event: 关闭事件
        """
        # 清理所有后台线程
        self._cleanup_threads()

        # 检查配置是否完成
        first_run_complete = self.config.get("system.first_run_complete", False)
        if not first_run_complete:
            # 配置未完成，退出整个应用程序
            import sys
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()
            sys.exit(0)
        else:
            # 配置已完成，正常关闭窗口
            super().closeEvent(event)

    def _cleanup_threads(self) -> None:
        """清理所有后台线程

        停止 NuitkaRunner 和 LogReaderThread，确保线程正确退出。
        """
        # 清理基础页面的线程
        if hasattr(self, 'base_page') and self.base_page:
            # 停止日志读取线程
            if self.base_page.log_reader_thread and self.base_page.log_reader_thread.isRunning():
                self.base_page.log_reader_thread.stop()
                # 等待线程完全停止
                self.base_page.log_reader_thread.wait(3000)  # 最多等待3秒

            # 停止 NuitkaRunner
            if self.base_page.runner and self.base_page.runner.isRunning():
                self.base_page.runner.stop()
                # NuitkaRunner 继承自 QThread，可以直接等待
                self.base_page.runner.wait(5000)  # 最多等待5秒

    def _init_ui(self) -> None:
        """初始化界面"""
        # 创建导航栏
        self._create_navigation()

        # 创建右上角日志按钮
        self._create_log_button()

        # 创建占位页面
        self._create_placeholder_pages()

    def _create_navigation(self) -> None:
        """创建导航栏

        添加7个导航项:基础、高级、专精、插件、嵌入、命令、设置
        每个页面使用ScrollArea包装，当内容超过窗口尺寸时可滚动查看。
        """
        from PySide6.QtWidgets import QSizePolicy, QScrollArea

        # 基础页面
        self.basics_interface = QWidget()
        self.basics_interface.setObjectName("basicsInterface")
        self.basics_layout = QVBoxLayout(self.basics_interface)
        self.basics_layout.setContentsMargins(0, 0, 0, 0)
        # 创建ScrollArea
        self.basics_scroll = QScrollArea()
        self.basics_scroll.setWidgetResizable(True)
        self.basics_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.basics_layout.addWidget(self.basics_scroll)
        self.addSubInterface(
            self.basics_interface,
            FluentIcon.HOME,
            "基础"
        )

        # 高级页面
        self.advanced_interface = QWidget()
        self.advanced_interface.setObjectName("advancedInterface")
        self.advanced_layout = QVBoxLayout(self.advanced_interface)
        self.advanced_layout.setContentsMargins(0, 0, 0, 0)
        self.advanced_scroll = QScrollArea()
        self.advanced_scroll.setWidgetResizable(True)
        self.advanced_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.advanced_layout.addWidget(self.advanced_scroll)
        self.addSubInterface(
            self.advanced_interface,
            FluentIcon.DEVELOPER_TOOLS,
            "高级"
        )

        # 专精页面
        self.expert_interface = QWidget()
        self.expert_interface.setObjectName("expertInterface")
        self.expert_layout = QVBoxLayout(self.expert_interface)
        self.expert_layout.setContentsMargins(0, 0, 0, 0)
        self.expert_scroll = QScrollArea()
        self.expert_scroll.setWidgetResizable(True)
        self.expert_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.expert_layout.addWidget(self.expert_scroll)
        self.addSubInterface(
            self.expert_interface,
            FluentIcon.CONNECT,
            "专精"
        )

        # 插件页面
        self.plugins_interface = QWidget()
        self.plugins_interface.setObjectName("pluginsInterface")
        self.plugins_layout = QVBoxLayout(self.plugins_interface)
        self.plugins_layout.setContentsMargins(0, 0, 0, 0)
        self.plugins_scroll = QScrollArea()
        self.plugins_scroll.setWidgetResizable(True)
        self.plugins_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.plugins_layout.addWidget(self.plugins_scroll)
        self.addSubInterface(
            self.plugins_interface,
            FluentIcon.APPLICATION,
            "插件"
        )

        # 嵌入页面
        self.embed_interface = QWidget()
        self.embed_interface.setObjectName("embedInterface")
        self.embed_layout = QVBoxLayout(self.embed_interface)
        self.embed_layout.setContentsMargins(0, 0, 0, 0)
        self.embed_scroll = QScrollArea()
        self.embed_scroll.setWidgetResizable(True)
        self.embed_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.embed_layout.addWidget(self.embed_scroll)
        self.addSubInterface(
            self.embed_interface,
            FluentIcon.FOLDER,
            "嵌入"
        )

        # 命令页面
        self.command_interface = QWidget()
        self.command_interface.setObjectName("commandInterface")
        self.command_layout = QVBoxLayout(self.command_interface)
        self.command_layout.setContentsMargins(0, 0, 0, 0)
        self.command_scroll = QScrollArea()
        self.command_scroll.setWidgetResizable(True)
        self.command_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.command_layout.addWidget(self.command_scroll)
        self.addSubInterface(
            self.command_interface,
            FluentIcon.CODE,
            "命令"
        )

        # 设置页面 (放在底部)
        self.settings_interface = QWidget()
        self.settings_interface.setObjectName("settingsInterface")
        self.settings_layout = QVBoxLayout(self.settings_interface)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.settings_layout.addWidget(self.settings_scroll)
        self.addSubInterface(
            self.settings_interface,
            FluentIcon.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM
        )

        # 默认显示基础页面
        self.navigationInterface.setCurrentItem(self.basics_interface.objectName())

    def resizeEvent(self, event) -> None:
        """窗口大小变化事件

        更新日志按钮的位置，并保存窗口尺寸到配置。
        只在窗口初始化完成后才保存尺寸，防止初始化期间的自动调整覆盖config。
        """
        super().resizeEvent(event)

        # 计算按钮位置：按钮应该在窗口内容区域的右侧，留出足够边距
        # 使用窗口宽度减去按钮宽度和额外边距，确保不与内容重叠
        button_right_margin = 60  # 按钮距离窗口右边缘的距离

        # 更新日志按钮位置 (右上角,在标题栏下方)
        if hasattr(self, 'log_button'):
            self.log_button.move(self.width() - button_right_margin, 50)

        # 只在窗口初始化完成后才保存窗口尺寸到配置
        if self._window_initialized and self.config:
            self.config.update(**{"ui.window_size": [self.width(), self.height()]})

    def moveEvent(self, event) -> None:
        """窗口移动事件

        当主窗口移动时，更新日志面板的位置。
        """
        super().moveEvent(event)

        # 更新日志面板位置（如果可见）
        if hasattr(self, 'log_panel'):
            self.log_panel.update_position()

    def _create_log_button(self) -> None:
        """创建右上角日志按钮"""
        # 在右上角添加日志按钮（原主题切换按钮位置）
        from qfluentwidgets import RoundMenu, Action, FluentIcon

        # 创建日志按钮
        self.log_button = TransparentToolButton(FluentIcon.DOCUMENT, self)
        self.log_button.setFixedSize(48, 48)
        self.log_button.clicked.connect(lambda: self.log_panel.toggle_panel(self))

        # 设置按钮位置 (右上角,在标题栏下方)
        self.log_button.move(self.width() - 60, 50)
        self.log_button.show()

        # 窗口大小变化时更新按钮位置
        self.log_button.raise_()

        # 添加右键菜单
        menu = RoundMenu(parent=self)
        menu.addAction(Action(FluentIcon.DELETE, "清空日志", triggered=self.log_panel._clear_logs))
        menu.addAction(Action(FluentIcon.SAVE, "保存日志", triggered=self._save_logs))
        self.log_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_button.customContextMenuRequested.connect(lambda pos: menu.exec())

    def _save_logs(self) -> None:
        """保存日志到文件"""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存日志",
            "",
            "日志文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            if self.log_panel.save_to_file(file_path):
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.success(
                    title="保存成功",
                    content=f"日志已保存到: {file_path}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

    def _connect_log_signals(self) -> None:
        """连接日志信号到 BasePage 的 NuitkaRunner"""
        # 在 _create_placeholder_pages 中创建 BasePage 后连接
        # 这里先添加占位符,实际连接在页面创建后进行
        pass

    def _create_placeholder_pages(self) -> None:
        """创建页面内容

        为基础、高级、插件和嵌入页面创建实际组件,其他页面使用占位内容。
        每个页面被包装在ScrollArea中，当内容超过窗口尺寸时可滚动查看。
        """
        # 基础页面 - 使用 BasePage
        self.base_page = BasePage()
        self.base_page.set_log_panel(self.log_panel)  # 连接日志面板
        self.basics_scroll.setWidget(self.base_page)

        # 高级页面 - 使用 AdvancedPage
        self.advanced_page = AdvancedPage()
        self.advanced_scroll.setWidget(self.advanced_page)

        # 插件页面 - 使用 PluginPage
        self.plugin_page = PluginPage()
        self.plugins_scroll.setWidget(self.plugin_page)

        # 嵌入页面 - 使用 EmbedPage
        self.embed_page = EmbedPage()
        self.embed_scroll.setWidget(self.embed_page)

        # 设置页面 - 使用 SettingsPage
        self.settings_page = SettingsPage()
        self.settings_scroll.setWidget(self.settings_page)

        # 专精页面 - 暂时禁用
        # self.expert_page = ExpertPage()
        # self.expert_scroll.setWidget(self.expert_page)
        self.expert_page = None  # 设置为 None 以便后续检查

        # 命令页面 - 使用 CommandPage
        self.command_page = CommandPage()
        self.command_scroll.setWidget(self.command_page)

    def _connect_page_signals(self) -> None:
        """连接各页面的配置变更信号到命令页面"""
        # 连接基础页面配置变更
        if hasattr(self, 'base_page'):
            self.base_page.config_changed.connect(self.command_page.refresh_command)

        # 连接高级页面配置变更
        if hasattr(self, 'advanced_page'):
            self.advanced_page.config_changed.connect(self.command_page.refresh_command)

        # 连接插件页面配置变更
        if hasattr(self, 'plugin_page'):
            self.plugin_page.config_changed.connect(self.command_page.refresh_command)

        # 连接嵌入页面配置变更
        if hasattr(self, 'embed_page'):
            self.embed_page.config_changed.connect(self.command_page.refresh_command)

        # 连接专精页面配置变更（暂时禁用）
        # if self.expert_page is not None:
        #     self.expert_page.config_changed.connect(self.command_page.refresh_command)

    def _on_page_changed(self, index):
        """页面切换事件处理

        当切换到高级页面时，重新加载配置以显示上次保存的状态。

        Args:
            index: 当前页面的索引
        """
        # 获取当前显示的页面
        current_widget = self.stackedWidget.widget(index)
        if current_widget and hasattr(current_widget, 'objectName'):
            item_name = current_widget.objectName()
            if item_name == "advancedInterface" and hasattr(self, 'advanced_page'):
                # 重新加载配置到高级页面
                self.advanced_page._load_config()

    def get_config(self):
        """获取当前配置

        Returns:
            Config: 当前配置对象
        """
        return self.config
