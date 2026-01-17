"""
日志面板模块

实时显示打包过程的日志输出,支持搜索、过滤和复制。
"""
import re
from datetime import datetime
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtGui import QFont, QTextDocument, QTextCursor
from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    ToolButton,
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

from nuitkaty.src.models.build_task import LogEntry


# ANSI 转义序列正则表达式
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


class LogPanel(QWidget):
    """日志面板组件

    实时显示打包输出,支持复制到剪贴板。
    """

    def __init__(self, parent=None):
        """初始化日志面板

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 日志条目列表
        self.log_entries = []

        # 初始化界面
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 日志显示卡片
        layout.addWidget(self._create_log_card())

    def _create_log_card(self) -> CardWidget:
        """创建日志显示卡片

        Returns:
            CardWidget: 日志显示卡片
        """
        card = CardWidget()
        # 确保卡片填充整个面板（无边距以避免透明区域）
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)

        # 设置卡片为圆角并填充整个面板
        card.setObjectName("logCard")
        card.setStyleSheet("""
            #logCard {
                background-color: #F9F9F9;
                border-radius: 8px;
                border: none;
            }
        """)

        # 标题栏
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.HISTORY)
        title = StrongBodyLabel("日志信息")
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 复制按钮
        self.copy_btn = PrimaryPushButton("复制日志")
        self.copy_btn.setFixedWidth(120)
        self.copy_btn.clicked.connect(self._copy_logs)
        title_layout.addWidget(self.copy_btn)

        # 清空按钮
        self.clear_btn = PushButton("清空日志")
        self.clear_btn.setFixedWidth(120)
        self.clear_btn.clicked.connect(self._clear_logs)
        title_layout.addWidget(self.clear_btn)

        card_layout.addLayout(title_layout)

        # 日志显示区域
        self.log_display = PlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)

        # 设置等宽字体
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_display.setFont(font)

        # 设置深色背景样式
        self.log_display.setStyleSheet("""
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

        card_layout.addWidget(self.log_display)

        # 日志统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = BodyLabel("日志条数: 0")
        self.stats_label.setStyleSheet("color: #888; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        card_layout.addLayout(stats_layout)

        return card

    def append_log(self, message: str, level: str = "INFO") -> None:
        """追加日志

        Args:
            message: 日志消息
            level: 日志级别 (INFO/WARNING/ERROR/DEBUG)
        """
        # 过滤 ANSI 转义序列
        clean_message = ANSI_ESCAPE_PATTERN.sub('', message)

        # 如果过滤后为空，不记录
        if not clean_message.strip():
            return

        # 创建日志条目
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=clean_message,
            source="nuitka"
        )
        self.log_entries.append(entry)

        # 格式化日志文本
        timestamp_str = entry.timestamp.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp_str}] [{level}] {clean_message}"

        # 追加到显示区域
        current_text = self.log_display.toPlainText()
        if current_text:
            new_text = current_text + "\n" + formatted_msg
        else:
            new_text = formatted_msg
        self.log_display.setPlainText(new_text)

        # 自动滚动到底部
        self._scroll_to_bottom()

        # 更新统计信息
        self.stats_label.setText(f"日志条数: {len(self.log_entries)}")

    def append_logs_batch(self, messages: list[str], level: str = "INFO") -> None:
        """批量追加日志（高效版本）

        使用 QTextCursor 批量追加多行日志，避免频繁的 UI 更新。
        日志文件中已包含 [时间][级别] 前缀，直接显示即可。

        Args:
            messages: 日志消息列表（已包含时间戳和级别前缀）
            level: 日志级别 (已废弃，保留兼容性)
        """
        if not messages:
            return

        # 使用 QTextCursor 批量追加文本
        cursor = QTextCursor(self.log_display.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 如果不是第一条日志，添加换行
        has_content = self.log_display.toPlainText().strip()
        if has_content:
            cursor.insertText("\n")

        # 批量处理日志
        formatted_lines = []
        for message in messages:
            # 过滤 ANSI 转义序列
            clean_message = ANSI_ESCAPE_PATTERN.sub('', message)

            # 如果过滤后为空，跳过
            if not clean_message.strip():
                continue

            # 创建日志条目（解析时间戳和级别）
            entry = self._parse_log_entry(clean_message)
            self.log_entries.append(entry)

            # 直接显示原始内容（已包含时间戳和级别）
            formatted_lines.append(clean_message)

        # 一次性插入所有文本
        if formatted_lines:
            cursor.insertText("\n".join(formatted_lines))

        # 自动滚动到底部
        self._scroll_to_bottom()

        # 更新统计信息
        self.stats_label.setText(f"日志条数: {len(self.log_entries)}")

    def _scroll_to_bottom(self) -> None:
        """滚动到底部"""
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _parse_log_entry(self, message: str) -> LogEntry:
        """解析日志条目

        从包含时间戳和级别的日志行中解析信息。

        Args:
            message: 日志消息，格式如 "[2026-01-18 02:48:43] [INFO] 消息内容"

        Returns:
            LogEntry: 解析后的日志条目
        """
        # 使用正则表达式解析 [时间] [级别] 消息
        pattern = r'\[(.*?)\] \[(.*?)\] (.*)'
        match = re.match(pattern, message)

        if match:
            timestamp_str, level, content = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = datetime.now()
            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=content,
                source="nuitka"
            )
        else:
            # 如果无法解析，使用当前时间和默认级别
            return LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=message,
                source="nuitka"
            )

    def clear_logs(self) -> None:
        """清空日志 (公共方法)"""
        self._clear_logs()

    def _clear_logs(self) -> None:
        """清空日志"""
        self.log_entries.clear()
        self.log_display.clear()
        self.stats_label.setText("日志条数: 0")

    def _copy_logs(self) -> None:
        """复制日志到剪贴板"""
        logs = self.log_display.toPlainText()

        if not logs:
            InfoBar.warning(
                title="无法复制",
                content="没有可复制的日志",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(logs)

        InfoBar.success(
            title="复制成功",
            content="日志已复制到剪贴板",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )

    def get_logs(self) -> list[LogEntry]:
        """获取所有日志条目

        Returns:
            list[LogEntry]: 日志条目列表
        """
        return self.log_entries

    def save_to_file(self, file_path: str) -> bool:
        """保存日志到文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in self.log_entries:
                    timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp_str}] [{entry.level}] {entry.message}\n")
            return True
        except Exception as e:
            print(f"保存日志失败: {e}")
            return False

    def get_current_logs(self) -> str:
        """获取当前显示的日志文本

        Returns:
            str: 当前日志文本
        """
        return self.log_display.toPlainText()


class CollapsibleLogPanel(LogPanel):
    """可折叠的日志面板

    支持从右侧滑入/滑出的动画效果。
    """

    def __init__(self, parent=None):
        """初始化可折叠日志面板

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 初始状态
        self._is_visible = False
        self._animation = None
        self._target_pos = 0

        # 保存父窗口引用，用于移动时更新位置
        self._parent_widget = parent

        # 设置初始大小
        self.setFixedSize(600, 800)

        # 设置透明背景以支持圆角
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 初始时隐藏
        self.hide()


    def show_panel(self, parent_widget: QWidget) -> None:
        """显示日志面板

        向右向外展开,不遮蔽主界面。

        Args:
            parent_widget: 父窗口
        """
        self._is_visible = True
        self._parent_widget = parent_widget

        # 设置父窗口（作为顶层窗口）
        self.setParent(None)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

        # 获取主窗口内容区域的位置和大小
        parent_frame_geom = parent_widget.frameGeometry()
        parent_content_rect = parent_widget.geometry()

        # 计算内容区域相对于窗口框架的偏移
        content_offset_x = parent_content_rect.x() - parent_frame_geom.x()
        content_offset_y = parent_content_rect.y() - parent_frame_geom.y()

        # 获取窗口框架的屏幕位置（使用pos()）
        frame_pos = parent_widget.pos()

        # 计算内容区域的屏幕位置
        content_x = frame_pos.x() + content_offset_x
        content_y = frame_pos.y() + content_offset_y
        content_width = parent_content_rect.width()
        content_height = parent_content_rect.height()

        # 设置面板大小：宽度为主窗口的一半，高度与主窗口一致
        panel_width = max(400, content_width // 2)
        panel_height = content_height
        self.setFixedSize(panel_width, panel_height)

        # 目标位置：主窗口内容区域右侧边缘，Y坐标与内容区域顶部对齐
        target_x = content_x + content_width
        target_y = content_y

        # 显示面板
        self.move(target_x, target_y)
        self.show()
        self.raise_()  # 确保面板在最上层

    def hide_panel(self) -> None:
        """隐藏日志面板,向右滑出屏幕"""
        if not self._is_visible:
            return

        self._is_visible = False
        self.hide()

    def toggle_panel(self, parent_widget: QWidget) -> None:
        """切换日志面板显示状态

        Args:
            parent_widget: 父窗口
        """
        if self._is_visible:
            self.hide_panel()
        else:
            self.show_panel(parent_widget)

    def update_position(self) -> None:
        """更新日志面板位置（当主窗口移动时调用）"""
        if not self._is_visible or not self._parent_widget:
            return

        parent_widget = self._parent_widget

        # 获取主窗口内容区域的位置和大小
        parent_frame_geom = parent_widget.frameGeometry()
        parent_content_rect = parent_widget.geometry()

        # 计算内容区域相对于窗口框架的偏移
        content_offset_x = parent_content_rect.x() - parent_frame_geom.x()
        content_offset_y = parent_content_rect.y() - parent_frame_geom.y()

        # 获取窗口框架的屏幕位置（使用pos()）
        frame_pos = parent_widget.pos()

        # 计算内容区域的屏幕位置
        content_x = frame_pos.x() + content_offset_x
        content_y = frame_pos.y() + content_offset_y
        content_width = parent_content_rect.width()
        content_height = parent_content_rect.height()

        # 设置面板大小：宽度为主窗口的一半，高度与主窗口一致
        panel_width = max(400, content_width // 2)
        panel_height = content_height
        self.setFixedSize(panel_width, panel_height)

        # 目标位置：主窗口内容区域右侧边缘，Y坐标与内容区域顶部对齐
        target_x = content_x + content_width
        target_y = content_y

        # 移动面板到新位置
        self.move(target_x, target_y)
