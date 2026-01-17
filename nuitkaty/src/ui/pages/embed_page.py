"""
嵌入页面模块

数据文件和资源嵌入页面,支持添加文件和目录到打包中。
"""
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem
from qfluentwidgets import (
    CardWidget,
    PushButton,
    PrimaryPushButton,
    LineEdit,
    ComboBox,
    CheckBox,
    ScrollArea,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    FluentIcon,
    IconWidget,
    MessageBox,
)

from nuitkaty.src.core.config import get_config
from nuitkaty.src.models.embedded_files import EmbeddedFile, FileType


class EmbedPage(QWidget):
    """文件嵌入页面

    支持添加文件和目录到打包中,自定义目标路径。
    """

    # 配置变更信号
    config_changed = Signal()

    def __init__(self, parent=None):
        """初始化嵌入页面

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 核心组件
        self.config = get_config()

        # 嵌入文件列表
        self.embedded_files = []

        # 初始化界面
        self._init_ui()
        self._load_files()

    def _init_ui(self) -> None:
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 50, 20)
        layout.setSpacing(20)

        # 标题
        title = SubtitleLabel("数据文件嵌入")
        layout.addWidget(title)

        # 说明
        desc = BodyLabel(
            "将数据文件、资源目录等嵌入到打包后的 EXE 中。"
            "支持单个文件、整个目录或按模式匹配文件。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.add_file_btn = PrimaryPushButton("添加文件")
        self.add_file_btn.clicked.connect(self._add_file)

        self.add_dir_btn = PushButton("添加目录")
        self.add_dir_btn.clicked.connect(self._add_directory)

        self.remove_btn = PushButton("移除选中")
        self.remove_btn.clicked.connect(self._remove_selected)

        self.clear_btn = PushButton("清空")
        self.clear_btn.clicked.connect(self._clear_all)

        button_layout.addWidget(self.add_file_btn)
        button_layout.addWidget(self.add_dir_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 文件列表卡片
        layout.addWidget(self._create_file_list_card())

    def _create_file_list_card(self) -> CardWidget:
        """创建文件列表卡片

        Returns:
            CardWidget: 文件列表卡片
        """
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)

        # 标题行
        title_layout = QHBoxLayout()
        icon = IconWidget(FluentIcon.FOLDER)
        title = StrongBodyLabel("已添加的文件")
        count_label = BodyLabel("共 0 项")
        self.count_label_ref = count_label

        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(count_label)
        card_layout.addLayout(title_layout)

        # 文件列表
        self.file_list = QListWidget()
        # 移除固定最小高度，允许窗口自由调整大小
        card_layout.addWidget(self.file_list)

        return card

    def _load_files(self) -> None:
        """从配置加载嵌入文件"""
        self.embedded_files = []
        embedded_files = self.config.get("nuitka.embedded-files", [])
        for item in embedded_files:
            if isinstance(item, dict):
                # 假设 dict 包含 source-path 和 destination-path
                self.embedded_files.append(EmbeddedFile(
                    source_path=item.get("source-path", ""),
                    destination_path=item.get("destination-path", ""),
                    file_type=FileType.FILE,
                    recursive=False
                ))
            elif isinstance(item, EmbeddedFile):
                self.embedded_files.append(item)

        self._refresh_list()

    def _refresh_list(self) -> None:
        """刷新文件列表显示"""
        self.file_list.clear()

        for file in self.embedded_files:
            item = QListWidgetItem()

            # 图标
            if file.file_type == FileType.DIRECTORY:
                icon_str = FluentIcon.FOLDER
            elif file.file_type == FileType.PATTERN:
                icon_str = FluentIcon.SEARCH
            else:
                icon_str = FluentIcon.DOCUMENT

            # 显示文本
            if file.file_type == FileType.DIRECTORY:
                text = f"[目录] {file.source_path} -> {file.destination_path}"
            elif file.file_type == FileType.PATTERN:
                text = f"[模式] {file.source_path} -> {file.destination_path}"
            else:
                text = f"[文件] {file.source_path} -> {file.destination_path}"

            if file.recursive:
                text += " (递归)"

            item.setText(text)
            item.setData(Qt.ItemDataRole.UserRole, file)
            self.file_list.addItem(item)

        # 更新计数
        self.count_label_ref.setText(f"共 {len(self.embedded_files)} 项")

    def _add_file(self) -> None:
        """添加文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要嵌入的文件",
            "",
            "所有文件 (*.*)"
        )

        if not file_path:
            return

        # 显示编辑对话框
        self._show_edit_dialog(file_path, FileType.FILE)

    def _add_directory(self) -> None:
        """添加目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择要嵌入的目录",
            ""
        )

        if not dir_path:
            return

        # 显示编辑对话框
        self._show_edit_dialog(dir_path, FileType.DIRECTORY)

    def _show_edit_dialog(self, source_path: str, file_type: FileType) -> None:
        """显示嵌入文件编辑对话框

        Args:
            source_path: 源路径
            file_type: 文件类型
        """
        # 创建对话框
        dialog = EmbedEditDialog(source_path, file_type, self)

        if dialog.exec():
            # 获取编辑结果
            embedded_file = dialog.get_embedded_file()
            self.embedded_files.append(embedded_file)
            self._refresh_list()
            self._save_files()
            self.config_changed.emit()

    def _remove_selected(self) -> None:
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            file = item.data(Qt.ItemDataRole.UserRole)
            if file in self.embedded_files:
                self.embedded_files.remove(file)

        self._refresh_list()
        self._save_files()
        self.config_changed.emit()

    def _clear_all(self) -> None:
        """清空所有文件"""
        if not self.embedded_files:
            return

        # 确认对话框
        box = MessageBox("确认清空", "确定要清空所有嵌入文件吗?", self)
        if box.exec():
            self.embedded_files.clear()
            self._refresh_list()
            self._save_files()
            self.config_changed.emit()

    def _save_files(self) -> None:
        """保存嵌入文件到配置"""
        # 转换为字典列表，使用 config.yml 中期望的格式
        files_data = []
        for file in self.embedded_files:
            files_data.append({
                "source-path": file.source_path,
                "destination-path": file.destination_path,
            })

        self.config.update(**{"nuitka.embedded-files": files_data})

    def get_embedded_files(self) -> list:
        """获取嵌入文件列表

        Returns:
            list: 嵌入文件列表
        """
        return self.embedded_files


class EmbedEditDialog(MessageBox):
    """嵌入文件编辑对话框"""

    def __init__(self, source_path: str, file_type: FileType, parent=None):
        """初始化对话框

        Args:
            source_path: 源路径
            file_type: 文件类型
            parent: 父窗口
        """
        super().__init__("编辑嵌入选项", "", parent)
        self.source_path = source_path
        self.file_type = file_type
        self.recursive = False

        self._init_ui()

    def _init_ui(self) -> None:
        """初始化界面"""
        # 创建内容区域
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)

        # 源路径
        source_layout = QHBoxLayout()
        source_label = BodyLabel("源路径:")
        source_label.setFixedWidth(80)
        source_edit = LineEdit()
        source_edit.setText(self.source_path)
        source_edit.setReadOnly(True)

        source_layout.addWidget(source_label)
        source_layout.addWidget(source_edit)
        layout.addLayout(source_layout)

        # 目标路径
        dest_layout = QHBoxLayout()
        dest_label = BodyLabel("目标路径:")
        dest_label.setFixedWidth(80)

        # 自动生成默认目标路径
        if self.file_type == FileType.DIRECTORY:
            default_dest = os.path.basename(self.source_path)
        else:
            default_dest = os.path.basename(self.source_path)

        self.dest_edit = LineEdit()
        self.dest_edit.setPlaceholderText("例如: data/ 或 resources/")
        self.dest_edit.setText(default_dest)

        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_edit)
        layout.addLayout(dest_layout)

        # 递归选项 (仅目录)
        if self.file_type == FileType.DIRECTORY:
            recursive_layout = QHBoxLayout()
            self.recursive_check = CheckBox("递归包含子目录")
            recursive_layout.addWidget(self.recursive_check)
            recursive_layout.addStretch()
            layout.addLayout(recursive_layout)

        # 提示
        hint = BodyLabel(
            "目标路径是 EXE 运行时访问该资源的路径。\n"
            "例如: 嵌入 'data/config.json'，程序中读取路径为 'data/config.json'"
        )
        hint.setStyleSheet("color: #888; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 设置对话框内容
        self.contentLayout.addWidget(content)

        # 调整按钮
        self.cancelButton.setText("取消")
        self.yesButton.setText("确定")

    def get_embedded_file(self) -> EmbeddedFile:
        """获取编辑后的嵌入文件对象

        Returns:
            EmbeddedFile: 嵌入文件对象
        """
        dest_path = self.dest_edit.text().strip()
        if not dest_path.endswith("/"):
            dest_path += "/"

        # 提取文件名
        if self.file_type == FileType.FILE:
            filename = os.path.basename(self.source_path)
            dest_path = dest_path + filename

        return EmbeddedFile(
            source_path=self.source_path,
            destination_path=dest_path,
            file_type=self.file_type,
            recursive=getattr(self, "recursive_check", None) and self.recursive_check.isChecked()
        )
