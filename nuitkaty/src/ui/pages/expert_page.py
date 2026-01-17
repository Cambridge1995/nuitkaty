"""
专精页面模块

专精页面,提供 Nuitka 的所有其他高级参数配置选项。
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea
from qfluentwidgets import (
    PushButton,
    LineEdit,
    ComboBox,
    CheckBox,
    SpinBox,
    DoubleSpinBox,
    CardWidget,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    ScrollArea,
)

from nuitkaty.src.core.config import get_config


class ExpertPage(QWidget):
    """专精页面

    提供 Nuitka 的所有其他高级参数配置选项,包括:
    - 模块包含/排除
    - 导入跟踪选项
    - 数据文件选项
    - 控制台模式选项
    - 其他高级选项
    """

    # 配置变更信号
    config_changed = Signal()

    # 专精参数定义 (参数名 -> 命令行标志)
    EXPERT_OPTIONS = {
        # 模块包含/排除
        "include_module": ("--include-module", str, ""),
        "include_package": ("--include-package", str, ""),
        "include_package_directory": ("--include-package-directory", str, ""),
        "exclude_module": ("--exclude-module", str, ""),
        "exclude_plugin": ("--exclude-plugin", str, ""),

        # 导入选项
        "no_include_stdlib": ("--no-include-stdlib", bool, False),
        "include_distribution_metadata": ("--include-distribution-metadata", bool, False),

        # 数据文件
        "include_data_files": ("--include-data-files", str, ""),
        "include_data_dirs": ("--include-data-dir", str, ""),

        # 控制台模式
        "console": ("--console", bool, False),
        "no_console": ("--no-console", bool, False),
        "force_stdout_spec": ("--force-stdout-spec", str, ""),
        "force_stderr_spec": ("--force-stderr-spec", str, ""),

        # Windows 特定
        # 注意：windows_console_mode 已移至高级页面的下拉框
        "windows_uac_uiaccess": ("--windows-uac-uiaccess", bool, False),

        # 代码生成
        # 注意：--follow-imports 是布尔开关，不是带值的选项
        # --follow-imports (跟随所有导入) / --nofollow-imports (不跟随导入)
        "follow_imports": ("--follow-imports", bool, False),
        "nofollow_imports": ("--nofollow-imports", bool, False),
        "follow_stdlib": ("--follow-stdlib", bool, False),

        # 优化选项
        "optimization_level": {
            "type": "choice",
            "choices": ["0", "1", "2"],
            "default": "0",
            "flag": "--optimization={value}"
        },
        "no_cpp_level": ("--no-cpp-level", bool, False),

        # 输出选项
        "output_dir_for_executable": ("--output-dir-for-executable", str, ""),
        "remove_output_for_distribution": ("--remove-output", bool, False),

        # 构建选项
        "no_deployment_flag": ("--no-deployment-flag", bool, False),
        "deployment_flag": ("--deployment-flag", bool, False),
        "no_deployment_mode_defused": ("--no-deployment-mode-defused", bool, False),

        # 调试选项
        "debug": ("--debug", bool, False),
        "trace_execution": ("--trace-execution", bool, False),
        "profile": ("--profile", bool, False),

        # 其他
        "experimental": ("--experimental", bool, False),
        "assume_yes_for_downloads": ("--assume-yes-for-downloads", bool, False),
        "no_progress_bar": ("--no-progress-bar", bool, False),
    }

    # 参数分组
    PARAM_GROUPS = {
        "模块包含/排除": [
            "include_module", "include_package", "include_package_directory",
            "exclude_module", "exclude_plugin"
        ],
        "导入选项": [
            "no_include_stdlib", "include_distribution_metadata",
            "follow_imports", "nofollow_imports", "follow_stdlib"
        ],
        "数据文件": [
            "include_data_files", "include_data_dirs"
        ],
        "控制台模式": [
            "console", "no_console", "force_stdout_spec", "force_stderr_spec"
        ],
        "Windows 特定": [
            "windows_uac_uiaccess"
        ],
        "代码优化": [
            "optimization_level", "no_cpp_level"
        ],
        "构建选项": [
            "output_dir_for_executable", "remove_output_for_distribution",
            "no_deployment_flag", "deployment_flag", "no_deployment_mode_defused"
        ],
        "调试选项": [
            "debug", "trace_execution", "profile"
        ],
        "其他选项": [
            "experimental", "assume_yes_for_downloads", "no_progress_bar"
        ]
    }

    def __init__(self, parent=None):
        """初始化专精页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()

        # 存储所有输入控件
        self.input_widgets = {}

        # 初始化界面
        self._init_ui()

        # 加载当前配置
        self._load_current_config()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 40, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("专精选项")
        layout.addWidget(title)

        # 说明
        desc = BodyLabel("配置 Nuitka 的高级参数,这些选项提供更细粒度的控制")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 为每个参数组创建卡片（不使用内部ScrollArea，使用主窗口的ScrollArea）
        for group_name, param_names in self.PARAM_GROUPS.items():
            card = self._create_group_card(group_name, param_names)
            layout.addWidget(card)

        layout.addStretch()

    def _create_group_card(self, group_name: str, param_names: list) -> CardWidget:
        """创建参数组卡片

        Args:
            group_name: 组名
            param_names: 参数名列表

        Returns:
            CardWidget: 参数组卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(12)

        # 标题
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.SETTING)
        title = StrongBodyLabel(group_name)
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        card_layout.addLayout(title_layout)

        # 为每个参数创建输入控件
        for param_name in param_names:
            if param_name in self.EXPERT_OPTIONS:
                param_widget = self._create_param_widget(param_name)
                card_layout.addWidget(param_widget)

        return card

    def _create_param_widget(self, param_name: str) -> QWidget:
        """创建参数输入控件

        Args:
            param_name: 参数名

        Returns:
            QWidget: 参数输入控件
        """
        option_def = self.EXPERT_OPTIONS[param_name]

        # 创建容器
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 参数标签
        label = BodyLabel(param_name.replace("_", "-").title())
        label.setFixedWidth(180)

        if isinstance(option_def, tuple):
            # 简单选项: (flag, type, default)
            flag, value_type, default_value = option_def

            if value_type == bool:
                # 复选框
                checkbox = CheckBox()
                checkbox.setChecked(default_value)
                checkbox.stateChanged.connect(lambda: self._on_param_changed(param_name))
                self.input_widgets[param_name] = checkbox
                container_layout.addWidget(label)
                container_layout.addWidget(checkbox)
                container_layout.addStretch()

            elif value_type == str:
                # 文本输入框
                line_edit = LineEdit()
                line_edit.setPlaceholderText(f"例如: {default_value or 'value'}")
                line_edit.textChanged.connect(lambda: self._on_param_changed(param_name))
                self.input_widgets[param_name] = line_edit
                container_layout.addWidget(label)
                container_layout.addWidget(line_edit)

        elif isinstance(option_def, dict):
            # 复杂选项: {type, choices, default, flag}
            option_type = option_def["type"]

            if option_type == "choice":
                # 下拉选择框
                combo_box = ComboBox()
                combo_box.addItems(option_def["choices"])
                combo_box.setCurrentText(option_def["default"])
                combo_box.currentTextChanged.connect(lambda: self._on_param_changed(param_name))
                self.input_widgets[param_name] = combo_box
                container_layout.addWidget(label)
                container_layout.addWidget(combo_box)

        return container

    def _on_param_changed(self, param_name: str) -> None:
        """参数变更处理

        Args:
            param_name: 参数名
        """
        # 更新配置
        self._update_config_from_ui()

        # 发射信号
        self.config_changed.emit()

    def _update_config_from_ui(self) -> None:
        """从 UI 更新配置"""
        expert_options = {}

        for param_name, widget in self.input_widgets.items():
            option_def = self.EXPERT_OPTIONS[param_name]

            if isinstance(option_def, tuple):
                _, value_type, _ = option_def

                if value_type == bool:
                    expert_options[param_name] = widget.isChecked()
                elif value_type == str:
                    expert_options[param_name] = widget.text()

            elif isinstance(option_def, dict):
                if option_def["type"] == "choice":
                    expert_options[param_name] = widget.currentText()

        # 保存到配置（注意：expert_options 可能不在新的 config.yml 结构中，暂时跳过保存）
        # 如果需要支持 expert_options，需要在 config.yml 中添加相应的字段

    def _load_current_config(self) -> None:
        """加载当前配置到界面"""
        # 从配置中读取 expert_options（如果存在）
        expert_options = self.config.get("nuitka.expert_options", {})

        # 迁移标志：是否需要清理配置
        needs_cleanup = False
        # 收集需要删除或更新的键
        keys_to_update = {}  # param_name -> new_value

        for param_name, widget in self.input_widgets.items():
            value = expert_options.get(param_name)

            if value is not None:
                option_def = self.EXPERT_OPTIONS[param_name]

                if isinstance(option_def, tuple):
                    _, value_type, default_value = option_def

                    if value_type == bool:
                        # 检查值类型，如果不是布尔值，需要迁移
                        if isinstance(value, bool):
                            widget.setChecked(value)
                        else:
                            # 旧的字符串值（如 "all", "none"）需要清理
                            # 对于 follow_imports 的旧值 "all"，设为 True（跟随所有导入）
                            # 对于 "none" 或 "skip_stdlib"，设为 False
                            if param_name == "follow_imports":
                                if value == "all":
                                    widget.setChecked(True)
                                    keys_to_update[param_name] = True
                                else:
                                    widget.setChecked(False)
                                    keys_to_update[param_name] = False
                            else:
                                # 其他布尔选项的旧值，设为 False（禁用）
                                widget.setChecked(False)
                                keys_to_update[param_name] = False
                            needs_cleanup = True
                    elif value_type == str:
                        widget.setText(value)

                elif isinstance(option_def, dict):
                    if option_def["type"] == "choice":
                        widget.setCurrentText(value)

        # 更新配置中的值（类型修正）
        if needs_cleanup and keys_to_update:
            for key, new_value in keys_to_update.items():
                expert_options[key] = new_value
            # 保存更新后的配置（暂时跳过，因为 expert_options 可能不在新配置结构中）

    def get_expert_args(self) -> list[str]:
        """获取专精参数命令行参数列表

        Returns:
            list[str]: 命令行参数列表
        """
        args = []
        expert_options = self.config.get("nuitka.expert_options", {})

        for param_name, option_def in self.EXPERT_OPTIONS.items():
            value = expert_options.get(param_name)

            if value is None or value == "" or value is False:
                continue

            if isinstance(option_def, tuple):
                flag, value_type, _ = option_def

                if value_type == bool and value is True:
                    args.append(flag)
                elif value_type == str and value:
                    args.append(f"{flag}={value}")

            elif isinstance(option_def, dict):
                flag_template = option_def["flag"]
                args.append(flag_template.format(value=value))

        return args

    def reset_to_defaults(self) -> None:
        """重置为默认值"""
        expert_options = {}

        for param_name, option_def in self.EXPERT_OPTIONS.items():
            if isinstance(option_def, tuple):
                _, _, default_value = option_def
                expert_options[param_name] = default_value
            elif isinstance(option_def, dict):
                expert_options[param_name] = option_def.get("default", "")

        # 更新配置（暂时跳过保存，因为 expert_options 可能不在新配置结构中）

        # 重新加载界面
        self._load_current_config()
