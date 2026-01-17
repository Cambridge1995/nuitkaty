"""
插件页面模块

Nuitka 插件管理页面,支持插件手动选择和自动分析。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    CardWidget,
    PushButton,
    PrimaryPushButton,
    CheckBox,
    ScrollArea,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    InfoBar,
    InfoBarPosition,
)

from nuitkaty.src.core.config import get_config
from nuitkaty.src.core.plugin_analyzer import PluginAnalyzer


class PluginPage(QWidget):
    """插件管理页面

    支持手动选择插件和自动分析入口文件所需的插件。
    """

    # 配置变更信号
    config_changed = Signal()

    def __init__(self, parent=None):
        """初始化插件页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()

        # 插件复选框字典
        self.plugin_checks = {}

        # 初始化界面
        self._init_ui()
        self._load_plugins()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 50, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("插件管理")
        layout.addWidget(title)

        # 说明
        desc = BodyLabel(
            "Nuitka 插件用于处理特定依赖库（如 PyQt、numpy 等）。"
            "您可以手动选择插件,也可以点击「自动分析」让系统检测需要的插件。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.analyze_btn = PrimaryPushButton("自动分析")
        self.analyze_btn.clicked.connect(self._analyze_plugins)

        self.select_all_btn = PushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)

        self.deselect_all_btn = PushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self._deselect_all)

        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 插件列表卡片
        layout.addWidget(self._create_plugin_list_card())

    def _create_plugin_list_card(self) -> CardWidget:
        """创建插件列表卡片

        Returns:
            CardWidget: 插件列表卡片
        """
        card = CardWidget()

        # 使用滚动区域
        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        # 移除固定最小高度，允许窗口自由调整大小

        # 内容容器
        content = QWidget()
        self.plugin_layout = QVBoxLayout(content)
        self.plugin_layout.setContentsMargins(20, 15, 20, 15)
        self.plugin_layout.setSpacing(10)

        scroll.setWidget(content)

        # 卡片布局
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(scroll)

        return card

    def _load_plugins(self) -> None:
        """加载可用插件列表"""
        # 清除现有插件
        for i in reversed(range(self.plugin_layout.count())):
            self.plugin_layout.itemAt(i).widget().setParent(None)
        self.plugin_checks.clear()

        # 获取可用插件
        available_plugins = PluginAnalyzer.get_available_plugins()

        # 获取已启用的插件
        enabled_plugins = set(self.config.get("nuitka.enabled-plugins", []))

        # 创建插件复选框
        for plugin in available_plugins:
            plugin_layout = QHBoxLayout()

            check = CheckBox()
            check.setChecked(plugin in enabled_plugins)
            check.stateChanged.connect(self._on_plugin_changed)

            plugin_label = BodyLabel(self._get_plugin_display_name(plugin))
            plugin_label.setWordWrap(True)

            plugin_layout.addWidget(check)
            plugin_layout.addWidget(plugin_label)
            plugin_layout.addStretch()

            self.plugin_layout.addLayout(plugin_layout)
            self.plugin_checks[plugin] = check

        self.plugin_layout.addStretch()

    def _get_plugin_display_name(self, plugin: str) -> str:
        """获取插件显示名称

        Args:
            plugin: 插件名称

        Returns:
            str: 显示名称
        """
        display_names = {
            "qt-plugins": "Qt 插件 (PyQt5/PyQt6/PySide2/PySide6)",
            "pillow": "Pillow (PIL)",
            "tk-inter": "Tkinter",
            "pygame": "Pygame",
        }
        return display_names.get(plugin, plugin)

    def _analyze_plugins(self) -> None:
        """自动分析入口文件所需的插件"""
        # 获取入口文件路径
        # 这里需要从 BasePage 获取,暂时使用对话框
        entry_file, _ = QFileDialog.getOpenFileName(
            self,
            "选择入口文件",
            "",
            "Python 文件 (*.py);;所有文件 (*.*)"
        )

        if not entry_file:
            return

        # 分析插件
        result = PluginAnalyzer.analyze_entry_file(entry_file)

        # 清除当前选择
        self._deselect_all()

        # 自动勾选检测到的插件
        for plugin in result.get("required_plugins", []):
            if plugin in self.plugin_checks:
                self.plugin_checks[plugin].setChecked(True)

        # 显示分析结果
        required_count = len(result.get("required_plugins", []))
        optional_count = len(result.get("optional_plugins", []))

        InfoBar.success(
            title="分析完成",
            content=f"检测到 {required_count} 个必需插件, {optional_count} 个可选插件",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000
        )

    def _select_all(self) -> None:
        """全选所有插件"""
        for check in self.plugin_checks.values():
            check.setChecked(True)

    def _deselect_all(self) -> None:
        """取消全选"""
        for check in self.plugin_checks.values():
            check.setChecked(False)

    def _on_plugin_changed(self) -> None:
        """插件选择变更处理"""
        self._save_plugins()
        self.config_changed.emit()

    def _save_plugins(self) -> None:
        """保存插件选择到配置"""
        enabled = []
        disabled = []

        for plugin, check in self.plugin_checks.items():
            if check.isChecked():
                enabled.append(plugin)
            else:
                disabled.append(plugin)

        self.config.update(**{
            "nuitka.enabled-plugins": enabled,
            "nuitka.disabled-plugins": disabled
        })

    def get_enabled_plugins(self) -> list[str]:
        """获取已启用的插件列表

        Returns:
            list[str]: 已启用的插件列表
        """
        return [p for p, check in self.plugin_checks.items() if check.isChecked()]

    def get_disabled_plugins(self) -> list[str]:
        """获取已禁用的插件列表

        Returns:
            list[str]: 已禁用的插件列表
        """
        return [p for p, check in self.plugin_checks.items() if not check.isChecked()]
