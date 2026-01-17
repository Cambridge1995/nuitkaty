"""
高级页面模块

高级编译选项配置页面,包含性能选项、其他选项和 EXE 版本信息配置。
"""
import os
import json
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    CardWidget,
    PushButton,
    Slider,
    CheckBox,
    LineEdit,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    SwitchButton,
    SpinBox,
    TransparentToolButton,
    InfoBar,
    InfoBarPosition,
    TeachingTip,
    TeachingTipTailPosition,
    InfoBarIcon,
    ComboBox,
)

from nuitkaty.src.core.config import get_config


class AdvancedPage(QWidget):
    """高级选项配置页面

    包含性能选项、其他选项和 EXE 版本信息配置。
    """

    # 配置变更信号
    config_changed = Signal()

    def __init__(self, parent=None):
        """初始化高级页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()

        # 标记：是否正在初始化（初始化期间不触发保存）
        self._is_initializing = True

        # 气泡提示管理
        self._help_tips = {}  # {name: TeachingTip实例}
        self._help_buttons = {}  # {name: 按钮}

        # 注册所有帮助信息
        self._register_help_info()

        # 初始化界面
        self._init_ui()
        self._load_config()

        # 初始化完成，允许触发保存
        self._is_initializing = False

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 40, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("高级编译选项")
        layout.addWidget(title)

        # 性能选项
        layout.addWidget(self._create_performance_card())

        # 其他选项
        layout.addWidget(self._create_options_card())

        # EXE 信息
        layout.addWidget(self._create_version_info_card())

        layout.addStretch()

    def _create_performance_card(self) -> CardWidget:
        """创建性能选项卡片

        Returns:
            CardWidget: 性能选项卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.SPEED_HIGH)
        title = StrongBodyLabel("性能选项")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("调整编译性能和编译器选项")
        desc.setStyleSheet("color: #666;")
        card_layout.addWidget(desc)

        # 线程数量
        jobs_layout = QHBoxLayout()
        jobs_label = BodyLabel("线程数量:")
        jobs_label.setFixedWidth(100)

        jobs_input_layout = QHBoxLayout()
        self.jobs_spin = SpinBox()
        self.jobs_spin.setRange(1, 32)
        self.jobs_spin.setValue(os.cpu_count() or 4)
        self.jobs_spin.setSingleStep(1)
        self.jobs_spin.valueChanged.connect(self._on_config_changed)

        jobs_hint = BodyLabel(f"(推荐: {os.cpu_count() or 4} 核)")
        jobs_hint.setStyleSheet("color: #888;")

        jobs_input_layout.addWidget(self.jobs_spin)
        jobs_input_layout.addWidget(jobs_hint)
        jobs_input_layout.addStretch()

        jobs_layout.addWidget(jobs_label)
        jobs_layout.addLayout(jobs_input_layout)
        card_layout.addLayout(jobs_layout)

        # 低内存模式
        low_memory_layout = QHBoxLayout()
        self.low_memory_check = SwitchButton()
        low_memory_label = BodyLabel("低内存模式 (--low-memory)")
        low_memory_help_btn = self._create_help_button("low_memory", "查看低内存模式说明")

        low_memory_hint = BodyLabel("适用于内存受限环境")
        low_memory_hint.setStyleSheet("color: #888;")

        low_memory_layout.addWidget(self.low_memory_check)
        low_memory_layout.addWidget(low_memory_label)
        low_memory_layout.addWidget(low_memory_help_btn)
        low_memory_layout.addStretch()
        low_memory_layout.addWidget(low_memory_hint)
        card_layout.addLayout(low_memory_layout)

        self.low_memory_check.checkedChanged.connect(self._on_config_changed)

        # 启用 clang
        clang_layout = QHBoxLayout()
        self.clang_check = SwitchButton()
        clang_label = BodyLabel("启用 Clang 编译器 (--clang)")
        clang_help_btn = self._create_help_button("clang", "查看 Clang 编译器说明")

        clang_hint = BodyLabel("需要安装 LLVM Clang")

        clang_layout.addWidget(self.clang_check)
        clang_layout.addWidget(clang_label)
        clang_layout.addWidget(clang_help_btn)
        clang_layout.addStretch()
        clang_layout.addWidget(clang_hint)
        card_layout.addLayout(clang_layout)

        self.clang_check.checkedChanged.connect(self._on_config_changed)

        # 使用 MinGW64
        mingw_layout = QHBoxLayout()
        self.mingw_check = SwitchButton()
        mingw_label = BodyLabel("使用 MinGW64 (--mingw64)")
        mingw_help_btn = self._create_help_button("mingw", "查看 MinGW64 编译器说明")

        mingw_hint = BodyLabel("需要安装 MSYS2 MinGW64")

        mingw_layout.addWidget(self.mingw_check)
        mingw_layout.addWidget(mingw_label)
        mingw_layout.addWidget(mingw_help_btn)
        mingw_layout.addStretch()
        mingw_layout.addWidget(mingw_hint)
        card_layout.addLayout(mingw_layout)

        self.mingw_check.checkedChanged.connect(self._on_config_changed)

        return card

    def _create_options_card(self) -> CardWidget:
        """创建其他选项卡片

        Returns:
            CardWidget: 其他选项卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(10)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.SETTING)
        title = StrongBodyLabel("其他选项")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("控制编译过程和输出行为")
        desc.setStyleSheet("color: #666;")
        card_layout.addWidget(desc)

        # 选项复选框
        self.options_checks = {}

        options = [
            ("remove-output", "自动删除构建文件夹", "--remove-output"),
            ("show-progress", "显示进度条", "--show-progress"),
            ("quiet-mode", "安静模式 (仅输出错误)", "--quiet"),
            ("show-memory", "显示内存占用", "--show-memory"),
            ("windows-uac-admin", "请求管理员权限", "--windows-uac-admin"),
            ("assume-yes-for-downloads", "自动确认下载", "--assume-yes-for-downloads"),
        ]

        # 需要帮助按钮的选项（映射到 JSON 中的键名）
        options_with_help = {
            "remove-output": "remove-output",
            "show-progress": "show-progress",
            "quiet-mode": "quiet",
            "show-memory": "show-memory",
            "windows-uac-admin": "windows-uac-admin",
            "assume-yes-for-downloads": "assume-yes-for-downloads"
        }

        for key, label, arg in options:
            opt_layout = QHBoxLayout()
            check = SwitchButton()
            check_lbl = BodyLabel(label)

            opt_layout.addWidget(check)
            opt_layout.addWidget(check_lbl)

            # 为特定选项添加帮助按钮
            if key in options_with_help:
                help_key = options_with_help[key]
                help_btn = self._create_help_button(help_key, f"查看{label}说明")
                opt_layout.addWidget(help_btn)

            opt_layout.addStretch()

            card_layout.addLayout(opt_layout)

            self.options_checks[key] = check
            check.checkedChanged.connect(self._on_config_changed)

        # LTO 选项映射（英文值 -> 中文显示）
        self.lto_options_map = {
            "yes": "启用",
            "no": "禁用",
            "auto": "自动",
        }

        # 链接时优化（下拉菜单）
        lto_layout = QHBoxLayout()
        lto_label = BodyLabel("链接时优化:")
        lto_label.setFixedWidth(120)
        self.lto_combo = ComboBox()
        self.lto_combo.addItems(list(self.lto_options_map.values()))
        self.lto_combo.setCurrentIndex(2)  # 默认选择"自动"
        self.lto_combo.currentIndexChanged.connect(self._on_config_changed)
        lto_help_btn = self._create_help_button("lto", "查看链接时优化说明")

        lto_layout.addWidget(lto_label)
        lto_layout.addWidget(self.lto_combo)
        lto_layout.addWidget(lto_help_btn)
        lto_layout.addStretch()
        card_layout.addLayout(lto_layout)

        # 缓存选项映射（英文值 -> 中文显示）
        self.cache_options_map = {
            "none": "不使用该参数",
            "all": "所有缓存",
            "ccache": "C 编译缓存",
            "bytecode": "字节码缓存",
            "compression": "压缩缓存",
            "dll-dependencies": "DLL 依赖缓存",
        }

        # 禁用缓存（下拉菜单）
        disable_cache_layout = QHBoxLayout()
        disable_cache_label = BodyLabel("禁用缓存:")
        disable_cache_label.setFixedWidth(120)
        self.disable_cache_combo = ComboBox()
        self.disable_cache_combo.addItems(list(self.cache_options_map.values()))
        self.disable_cache_combo.setCurrentIndex(0)
        self.disable_cache_combo.currentIndexChanged.connect(self._on_config_changed)
        disable_cache_help_btn = self._create_help_button("disable-cache", "查看禁用缓存说明")

        disable_cache_layout.addWidget(disable_cache_label)
        disable_cache_layout.addWidget(self.disable_cache_combo)
        disable_cache_layout.addWidget(disable_cache_help_btn)
        disable_cache_layout.addStretch()
        card_layout.addLayout(disable_cache_layout)

        # 清除缓存（下拉菜单）
        clean_cache_layout = QHBoxLayout()
        clean_cache_label = BodyLabel("清除缓存:")
        clean_cache_label.setFixedWidth(120)
        self.clean_cache_combo = ComboBox()
        self.clean_cache_combo.addItems(list(self.cache_options_map.values()))
        self.clean_cache_combo.setCurrentIndex(0)
        self.clean_cache_combo.currentIndexChanged.connect(self._on_config_changed)
        clean_cache_help_btn = self._create_help_button("clean-cache", "查看清除缓存说明")

        clean_cache_layout.addWidget(clean_cache_label)
        clean_cache_layout.addWidget(self.clean_cache_combo)
        clean_cache_layout.addWidget(clean_cache_help_btn)
        clean_cache_layout.addStretch()
        card_layout.addLayout(clean_cache_layout)

        # 控制台模式下拉框
        console_mode_layout = QHBoxLayout()
        console_mode_label = BodyLabel("控制台模式:")
        console_mode_label.setFixedWidth(120)

        self.console_mode_combo = ComboBox()
        self.console_mode_combo.addItems([
            "不使用该参数",
            "有控制台 (force)",
            "无控制台 (disable)",
            "附加到父进程 (attach)",
        ])
        self.console_mode_combo.setCurrentIndex(0)
        self.console_mode_combo.currentIndexChanged.connect(self._on_config_changed)
        console_mode_help_btn = self._create_help_button("windows-console-mode", "查看控制台模式说明")

        console_mode_layout.addWidget(console_mode_label)
        console_mode_layout.addWidget(self.console_mode_combo)
        console_mode_layout.addWidget(console_mode_help_btn)
        console_mode_layout.addStretch()

        card_layout.addLayout(console_mode_layout)

        return card

    def _create_version_info_card(self) -> CardWidget:
        """创建 EXE 版本信息卡片

        Returns:
            CardWidget: 版本信息卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.INFO)
        title = StrongBodyLabel("EXE 版本信息")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 说明
        desc = BodyLabel("设置可执行文件的版本信息（显示在文件属性中）")
        desc.setStyleSheet("color: #666;")
        card_layout.addWidget(desc)

        # 版本信息输入框
        self.version_inputs = {}

        version_fields = [
            ("company_name", "公司名称", "例如: My Company"),
            ("product_name", "产品名称", "例如: My Application"),
            ("file_version", "文件版本", "例如: 1.0.0.0"),
            ("product_version", "产品版本", "例如: 1.0.0"),
            ("file_description", "文件描述", "例如: My Application"),
            ("copyright", "版权信息", "例如: Copyright © 2024"),
            ("trademarks", "商标信息", "例如: Trademark Info"),
        ]

        for key, label, placeholder in version_fields:
            field_layout = QHBoxLayout()
            field_label = BodyLabel(f"{label}:")
            field_label.setFixedWidth(100)

            line_edit = LineEdit()
            line_edit.setPlaceholderText(placeholder)
            line_edit.textChanged.connect(self._on_config_changed)

            field_layout.addWidget(field_label)
            field_layout.addWidget(line_edit)
            card_layout.addLayout(field_layout)

            self.version_inputs[key] = line_edit

        return card

    def _load_config(self) -> None:
        """从配置加载选项状态"""
        # 加载配置期间阻止信号触发
        self._is_initializing = True

        # 阻止所有控件的信号
        self.jobs_spin.blockSignals(True)
        self.low_memory_check.blockSignals(True)
        self.clang_check.blockSignals(True)
        self.mingw_check.blockSignals(True)
        for check in self.options_checks.values():
            check.blockSignals(True)
        self.lto_combo.blockSignals(True)
        self.console_mode_combo.blockSignals(True)
        self.disable_cache_combo.blockSignals(True)
        self.clean_cache_combo.blockSignals(True)
        for input_widget in self.version_inputs.values():
            input_widget.blockSignals(True)

        # 性能选项
        self.jobs_spin.setValue(self.config.get("nuitka.jobs", 4))
        self.low_memory_check.setChecked(self.config.get("nuitka.low-memory", False))
        self.clang_check.setChecked(self.config.get("nuitka.clang", False))
        self.mingw_check.setChecked(self.config.get("nuitka.mingw64", False))

        # 其他选项
        self.options_checks["remove-output"].setChecked(self.config.get("nuitka.remove-output", False))
        self.options_checks["show-progress"].setChecked(self.config.get("nuitka.show-progress", False))
        self.options_checks["quiet-mode"].setChecked(self.config.get("nuitka.quiet", False))
        self.options_checks["show-memory"].setChecked(self.config.get("nuitka.show-memory", False))
        self.options_checks["windows-uac-admin"].setChecked(self.config.get("nuitka.windows-uac-admin", False))
        self.options_checks["assume-yes-for-downloads"].setChecked(self.config.get("nuitka.assume-yes-for-downloads", False))

        # LTO 选项（下拉菜单）
        lto_value = self.config.get("nuitka.lto", "")
        # 空字符串替换为 "auto"
        if str(lto_value) == "":
            lto_value = "auto"
        # 获取对应的中文显示
        lto_display = self.lto_options_map.get(str(lto_value), "自动")
        self.lto_combo.setCurrentIndex(list(self.lto_options_map.values()).index(lto_display))

        # 缓存选项（使用下拉菜单）
        # 创建反向映射（中文 -> 英文）
        cache_reverse_map = {v: k for k, v in self.cache_options_map.items()}

        # 禁用缓存
        disable_cache_value = self.config.get("nuitka.disable-cache", "")
        if isinstance(disable_cache_value, bool):
            disable_cache_value = ""
        # 空字符串视为 "none"
        if str(disable_cache_value) == "":
            disable_cache_value = "none"
        # 获取对应的中文显示
        disable_cache_display = self.cache_options_map.get(str(disable_cache_value), "不使用该参数")
        self.disable_cache_combo.setCurrentIndex(list(self.cache_options_map.values()).index(disable_cache_display))

        # 清除缓存
        clean_cache_value = self.config.get("nuitka.clean-cache", "")
        if isinstance(clean_cache_value, bool):
            clean_cache_value = ""
        # 空字符串视为 "none"
        if str(clean_cache_value) == "":
            clean_cache_value = "none"
        # 获取对应的中文显示
        clean_cache_display = self.cache_options_map.get(str(clean_cache_value), "不使用该参数")
        self.clean_cache_combo.setCurrentIndex(list(self.cache_options_map.values()).index(clean_cache_display))

        # 控制台模式（映射到 ComboBox 索引）
        console_mode = self.config.get("nuitka.windows-console-mode", "force")
        console_mode_map = {
            "force": 1,
            "disable": 2,
            "attach": 3,
            "hide": 0,
        }
        self.console_mode_combo.setCurrentIndex(console_mode_map.get(console_mode, 1))

        # EXE 信息
        self.version_inputs["company_name"].setText(self.config.get("nuitka.company-name", ""))
        self.version_inputs["product_name"].setText(self.config.get("nuitka.product-name", ""))
        self.version_inputs["file_version"].setText(self.config.get("nuitka.file-version", ""))
        self.version_inputs["product_version"].setText(self.config.get("nuitka.product-version", ""))
        self.version_inputs["file_description"].setText(self.config.get("nuitka.file-description", ""))
        self.version_inputs["copyright"].setText(self.config.get("nuitka.copyright", ""))
        self.version_inputs["trademarks"].setText(self.config.get("nuitka.trademarks", ""))

        # 恢复所有控件的信号
        self.jobs_spin.blockSignals(False)
        self.low_memory_check.blockSignals(False)
        self.clang_check.blockSignals(False)
        self.mingw_check.blockSignals(False)
        for check in self.options_checks.values():
            check.blockSignals(False)
        self.lto_combo.blockSignals(False)
        self.console_mode_combo.blockSignals(False)
        self.disable_cache_combo.blockSignals(False)
        self.clean_cache_combo.blockSignals(False)
        for input_widget in self.version_inputs.values():
            input_widget.blockSignals(False)

        # 加载完成，重新启用信号触发
        self._is_initializing = False

    def save_config(self) -> None:
        """保存当前配置"""
        # 性能选项
        self.config.set("nuitka.jobs", self.jobs_spin.value())
        self.config.set("nuitka.low-memory", self.low_memory_check.isChecked())
        self.config.set("nuitka.clang", self.clang_check.isChecked())
        self.config.set("nuitka.mingw64", self.mingw_check.isChecked())

        # 其他选项
        self.config.set("nuitka.remove-output", self.options_checks["remove-output"].isChecked())
        self.config.set("nuitka.show-progress", self.options_checks["show-progress"].isChecked())
        self.config.set("nuitka.quiet", self.options_checks["quiet-mode"].isChecked())
        self.config.set("nuitka.show-memory", self.options_checks["show-memory"].isChecked())
        self.config.set("nuitka.windows-uac-admin", self.options_checks["windows-uac-admin"].isChecked())
        self.config.set("nuitka.assume-yes-for-downloads", self.options_checks["assume-yes-for-downloads"].isChecked())

        # LTO 选项（从下拉菜单转换为英文值）
        lto_values = list(self.lto_options_map.keys())
        lto_index = self.lto_combo.currentIndex()
        if lto_index >= 0 and lto_index < len(lto_values):
            self.config.set("nuitka.lto", lto_values[lto_index])

        # 缓存选项（从下拉菜单转换为英文值）
        cache_values = list(self.cache_options_map.keys())

        disable_cache_index = self.disable_cache_combo.currentIndex()
        if disable_cache_index >= 0 and disable_cache_index < len(cache_values):
            self.config.set("nuitka.disable-cache", cache_values[disable_cache_index])

        clean_cache_index = self.clean_cache_combo.currentIndex()
        if clean_cache_index >= 0 and clean_cache_index < len(cache_values):
            self.config.set("nuitka.clean-cache", cache_values[clean_cache_index])

        # 控制台模式（从 ComboBox 索引映射到字符串）
        console_mode_map = {
            0: "hide",
            1: "force",
            2: "disable",
            3: "attach",
        }
        console_mode = console_mode_map.get(self.console_mode_combo.currentIndex(), "force")
        self.config.set("nuitka.windows-console-mode", console_mode)

        # EXE 信息
        self.config.set("nuitka.company-name", self.version_inputs["company_name"].text())
        self.config.set("nuitka.product-name", self.version_inputs["product_name"].text())
        self.config.set("nuitka.file-version", self.version_inputs["file_version"].text())
        self.config.set("nuitka.product-version", self.version_inputs["product_version"].text())
        self.config.set("nuitka.file-description", self.version_inputs["file_description"].text())
        self.config.set("nuitka.copyright", self.version_inputs["copyright"].text())
        self.config.set("nuitka.trademarks", self.version_inputs["trademarks"].text())

        # 最后输出一次完整的命令
        print(f"[debug] to_command: {self.config.to_command()}")

    def _register_help_info(self) -> None:
        """从 JSON 文件加载所有帮助信息"""
        # 获取 JSON 文件路径（相对于当前文件）
        current_file = Path(__file__)
        # 当前文件: nuitkaty/src/ui/pages/advanced_page.py
        # 向上四级到项目根目录，然后进入 config/help_tips.json
        json_path = current_file.parent.parent.parent.parent / "config" / "help_tips.json"

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self._help_info = json.load(f)
        except FileNotFoundError:
            print(f"[警告] 帮助信息文件不存在: {json_path}")
            self._help_info = {}
        except json.JSONDecodeError as e:
            print(f"[警告] 帮助信息文件格式错误: {e}")
            self._help_info = {}

    def _create_help_button(self, name: str, tooltip_text: str = "查看说明") -> 'TransparentToolButton':
        """创建帮助按钮

        Args:
            name: 帮助名称（用于索引）
            tooltip_text: 工具提示文本

        Returns:
            帮助按钮
        """
        from qfluentwidgets import TransparentToolButton
        help_btn = TransparentToolButton(FluentIcon.MESSAGE, self)
        help_btn.setFixedSize(28, 28)
        help_btn.setToolTip(tooltip_text)
        help_btn.clicked.connect(lambda: self._toggle_help(name))
        self._help_buttons[name] = help_btn
        return help_btn

    def _toggle_help(self, name: str) -> None:
        """切换显示帮助信息

        Args:
            name: 帮助名称
        """
        # 如果气泡已存在，尝试关闭它
        if name in self._help_tips and self._help_tips[name] is not None:
            try:
                self._help_tips[name].close()
                self._help_tips[name] = None
                return
            except RuntimeError:
                self._help_tips[name] = None

        # 关闭所有其他气泡
        for other_name in list(self._help_tips.keys()):
            if other_name != name and self._help_tips[other_name] is not None:
                try:
                    self._help_tips[other_name].close()
                    self._help_tips[other_name] = None
                except RuntimeError:
                    self._help_tips[other_name] = None

        # 创建新气泡
        if name in self._help_info:
            info = self._help_info[name]
            from qfluentwidgets import TeachingTip, TeachingTipTailPosition, InfoBarIcon

            self._help_tips[name] = TeachingTip.create(
                target=self._help_buttons[name],
                icon=InfoBarIcon.INFORMATION,
                title=info['title'],
                content=info['content'],
                isClosable=True,
                tailPosition=TeachingTipTailPosition.LEFT,
                duration=-1,
                parent=self
            )

    def _on_config_changed(self) -> None:
        """配置变更处理"""
        # 初始化期间不保存配置
        if self._is_initializing:
            return

        self.save_config()
        self.config_changed.emit()
