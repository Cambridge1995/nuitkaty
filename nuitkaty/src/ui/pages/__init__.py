# UI 页面模块

from nuitkaty.src.ui.pages.base_page import BasePage
from nuitkaty.src.ui.pages.advanced_page import AdvancedPage
from nuitkaty.src.ui.pages.plugin_page import PluginPage
from nuitkaty.src.ui.pages.embed_page import EmbedPage
from nuitkaty.src.ui.pages.settings_page import SettingsPage
# 暂时禁用专精页面
# from nuitkaty.src.ui.pages.expert_page import ExpertPage
from nuitkaty.src.ui.pages.command_page import CommandPage

__all__ = ["BasePage", "AdvancedPage", "PluginPage", "EmbedPage", "SettingsPage", "CommandPage"]
