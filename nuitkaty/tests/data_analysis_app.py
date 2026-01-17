"""
数据分析应用程序主入口

这是一个用于测试 Nuitka 打包插件功能的主程序。
使用 numpy、pandas、matplotlib 进行数据分析。
"""
import sys
import os

# 添加测试目录到路径
test_dir = os.path.dirname(__file__)
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

# 导入测试模块并运行
from test_data_analysis import main

if __name__ == "__main__":
    sys.exit(main())
