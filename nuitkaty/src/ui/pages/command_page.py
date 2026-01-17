"""
命令页面模块

命令页面,展示生成的完整 Nuitka 命令,支持复制到剪贴板。
"""
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtGui import QTextDocument, QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    PlainTextEdit,
    CardWidget,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    InfoBar,
    InfoBarPosition,
    ScrollArea,
)

from nuitkaty.src.core.config import get_config


class CommandSyntaxHighlighter(QSyntaxHighlighter):
    """命令语法高亮器

    为 Nuitka 命令添加简单的语法高亮。
    """

    def __init__(self, document: QTextDocument):
        """初始化语法高亮器

        Args:
            document: 文本文档对象
        """
        super().__init__(document)

        # 定义高亮规则
        self.highlighting_rules = []

        # Python 命令高亮 (蓝色)
        python_format = QTextCharFormat()
        python_format.setForeground(QColor("#569CD6"))  # VS Code blue
        python_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"^python\b", python_format))

        # Nuitka 模块高亮 (蓝色)
        nuitka_format = QTextCharFormat()
        nuitka_format.setForeground(QColor("#569CD6"))  # VS Code blue
        nuitka_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r"-m nuitka", nuitka_format))

        # 参数标志高亮 (绿色)
        param_format = QTextCharFormat()
        param_format.setForeground(QColor("#4EC9B0"))  # VS Code teal
        self.highlighting_rules.append((r"--[\w-]+", param_format))

        # 等号高亮 (白色)
        equals_format = QTextCharFormat()
        equals_format.setForeground(QColor("#D4D4D4"))  # VS Code white
        self.highlighting_rules.append((r"=", equals_format))

        # 路径高亮 (橙色)
        path_format = QTextCharFormat()
        path_format.setForeground(QColor("#CE9178"))  # VS Code orange
        self.highlighting_rules.append((r'"[^"]*"', path_format))

    def highlightBlock(self, text: str) -> None:
        """高亮文本块

        Args:
            text: 要高亮的文本
        """
        import re

        for pattern, fmt in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class CommandPage(QWidget):
    """命令页面

    展示生成的完整 Nuitka 命令,支持复制到剪贴板。
    配置变更时自动更新显示的命令。
    """

    def __init__(self, parent=None):
        """初始化命令页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()

        # 默认值 (用于生成预览命令)
        self._default_entry_file = ""
        self._default_output_dir = ""
        self._default_output_filename = ""
        self._default_icon_path = ""

        # 初始化界面
        self._init_ui()

        # 生成初始命令
        self._update_command_display()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 50, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("生成的命令")
        layout.addWidget(title)

        # 说明
        desc = BodyLabel("以下是根据当前配置生成的 Nuitka 编译命令")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 命令显示卡片
        layout.addWidget(self._create_command_card())

        layout.addStretch()

    def _create_command_card(self) -> CardWidget:
        """创建命令显示卡片

        Returns:
            CardWidget: 命令显示卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # 标题栏
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.CODE)
        title = StrongBodyLabel("Nuitka 命令")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 复制按钮
        self.copy_btn = PrimaryPushButton("复制命令")
        self.copy_btn.setFixedWidth(120)
        self.copy_btn.clicked.connect(self._copy_command)
        title_layout.addWidget(self.copy_btn)

        card_layout.addLayout(title_layout)

        # 命令显示区域
        self.command_display = PlainTextEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        self.command_display.setFixedHeight(200)

        # 设置等宽字体
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.command_display.setFont(font)

        # 设置深色背景样式
        self.command_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                padding: 10px;
            }
            QPlainTextEdit:disabled {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
        """)

        # 添加语法高亮
        self.highlighter = CommandSyntaxHighlighter(self.command_display.document())

        card_layout.addWidget(self.command_display)

        # 命令统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = BodyLabel("参数数量: 0")
        self.stats_label.setStyleSheet("color: #888; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        # 示例说明
        example_label = BodyLabel("💡 提示: 这是预览命令,实际执行时会使用真实的文件路径")
        example_label.setStyleSheet("color: #888; font-size: 12px;")
        stats_layout.addWidget(example_label)

        card_layout.addLayout(stats_layout)

        return card

    def _copy_command(self) -> None:
        """复制命令到剪贴板"""
        command = self.command_display.toPlainText()

        if not command:
            InfoBar.warning(
                title="无法复制",
                content="没有可复制的命令",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(command)

        InfoBar.success(
            title="复制成功",
            content="命令已复制到剪贴板",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )

    def _update_command_display(self) -> None:
        """更新命令显示"""
        # 使用默认值或占位符生成预览命令
        entry_file = self._default_entry_file or "main.py"
        output_dir = self._default_output_dir or "./dist"
        output_filename = self._default_output_filename or "app.exe"
        icon_path = self._default_icon_path or None

        try:
            command = self.config.to_command()

            # 显示命令
            self.command_display.setPlainText(command)

            # 更新统计信息
            param_count = command.count("--")
            self.stats_label.setText(f"参数数量: {param_count}")

        except Exception as e:
            self.command_display.setPlainText(f"# 命令生成失败: {e}")
            self.stats_label.setText("参数数量: 0")

    @Slot(str, str, str, object)
    def update_build_config(self, entry_file: str, output_dir: str,
                           output_filename: str, icon_path: str | None = None) -> None:
        """更新构建配置

        当基础页面的配置变更时调用,用于更新命令预览。

        Args:
            entry_file: 入口文件路径
            output_dir: 输出目录
            output_filename: 输出文件名
            icon_path: 图标路径
        """
        self._default_entry_file = entry_file
        self._default_output_dir = output_dir
        self._default_output_filename = output_filename
        self._default_icon_path = icon_path

        # 重新生成命令
        self._update_command_display()

    @Slot()
    def refresh_command(self) -> None:
        """刷新命令显示

        当其他配置变更时调用。
        """
        # 重新加载配置
        self.config.reload()

        # 更新显示
        self._update_command_display()

    def get_current_command(self) -> str:
        """获取当前显示的命令

        Returns:
            str: 当前命令
        """
        return self.command_display.toPlainText()
