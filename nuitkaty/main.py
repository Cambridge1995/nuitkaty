"""
Nuitka Python 打包工具 - 主程序入口

该应用提供一个图形化界面,使用 Nuitka 将 Python 程序打包为 Windows EXE 可执行文件。
"""
import sys
import os

# 将项目根目录添加到 sys.path,支持绝对导入
# main.py 位于 nuitkaty/nuitkaty/，需要使用 nuitkaty/ 作为根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from nuitkaty.src.ui.main_window import MainWindow


def main():
    """应用主入口函数"""

    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName("Nuitkaty")
    app.setApplicationDisplayName("Nuitka Python 打包工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Nuitkaty")

    # 清除可能保存的窗口几何信息，确保使用config中的尺寸
    from PySide6.QtCore import QSettings
    settings = QSettings("Nuitkaty", "Nuitkaty")
    settings.remove("geometry")
    settings.remove("windowState")
    settings.sync()

    # 设置默认主题 (稍后会从配置加载)
    setTheme(Theme.AUTO)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
