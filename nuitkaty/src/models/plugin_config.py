"""
插件配置数据模型

Nuitka插件的启用/禁用状态,包括自动分析结果和手动选择。
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class PluginConfiguration:
    """插件配置对象

    管理Nuitka插件的启用和禁用状态,支持自动分析功能。
    """
    enabled_plugins: List[str] = field(default_factory=list)
    disabled_plugins: List[str] = field(default_factory=list)
    auto_analyzed: bool = False
    analysis_result: Dict = field(default_factory=dict)

    # 可用的插件列表（仅限 Nuitka 官方支持的插件）
    # 官方文档: https://nuitka.net/doc/user-manual.html#plugin-list
    # 注意: numpy 插件已弃用，Nuitka 现在会自动处理 numpy，无需手动启用
    AVAILABLE_PLUGINS = [
        "qt-plugins",     # Qt 插件 (PyQt5/PyQt6/PySide2/PySide6)
        "pillow",         # Pillow (PIL)
        "tk-inter",       # Tkinter
        "pygame",         # Pygame
        "anti-bloat",     # Anti-Bloat (减少体积)
    ]

    def validate_plugin_name(self, name: str) -> bool:
        """验证插件名称是否有效"""
        return name in self.AVAILABLE_PLUGINS

    def validate_no_conflicts(self) -> bool:
        """验证插件无冲突"""
        return set(self.enabled_plugins).isdisjoint(set(self.disabled_plugins))
