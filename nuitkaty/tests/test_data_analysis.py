"""
数据分析插件测试程序

用于测试 Nuitka 打包时 numpy、pandas、matplotlib 插件的功能。
这个程序执行完整的数据分析流程，验证所有插件是否正常工作。
"""
import sys
import os
from datetime import datetime

# 测试结果收集
test_results = []


def log_test(name: str, passed: bool, message: str = ""):
    """记录测试结果"""
    status = "[PASS]" if passed else "[FAIL]"
    result = f"{status} - {name}"
    if message:
        result += f": {message}"
    test_results.append((name, passed, message))
    print(result)


def test_numpy():
    """测试 NumPy 插件功能"""
    print("\n" + "="*50)
    print("测试 NumPy 插件")
    print("="*50)

    try:
        import numpy as np

        # 测试1: 基本数组操作
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.sum() == 15, "数组求和失败"
        log_test("NumPy 数组求和", True)

        # 测试2: 矩阵运算
        matrix1 = np.array([[1, 2], [3, 4]])
        matrix2 = np.array([[5, 6], [7, 8]])
        result = np.dot(matrix1, matrix2)
        expected = np.array([[19, 22], [43, 50]])
        assert np.array_equal(result, expected), "矩阵运算失败"
        log_test("NumPy 矩阵运算", True)

        # 测试3: 统计函数
        data = np.random.randn(1000)
        mean = np.mean(data)
        std = np.std(data)
        assert -1 < mean < 1, f"均值异常: {mean}"
        assert 0.5 < std < 1.5, f"标准差异常: {std}"
        log_test("NumPy 统计函数", True, f"均值={mean:.3f}, 标准差={std:.3f}")

        # 测试4: 数组切片和索引
        arr = np.arange(20).reshape(4, 5)
        slice_result = arr[1:3, 2:4]
        assert slice_result.shape == (2, 2), "数组切片失败"
        log_test("NumPy 数组切片", True)

        # 测试5: 广播机制
        a = np.array([[1, 2, 3], [4, 5, 6]])
        b = np.array([10, 20, 30])
        result = a + b
        expected = np.array([[11, 22, 33], [14, 25, 36]])
        assert np.array_equal(result, expected), "广播机制失败"
        log_test("NumPy 广播机制", True)

        return True

    except Exception as e:
        log_test("NumPy 插件", False, str(e))
        return False


def test_pandas():
    """测试 Pandas 插件功能"""
    print("\n" + "="*50)
    print("测试 Pandas 插件")
    print("="*50)

    try:
        import pandas as pd
        import numpy as np

        # 测试1: DataFrame 创建
        data = {
            'name': ['Alice', 'Bob', 'Charlie', 'David'],
            'age': [25, 30, 35, 28],
            'salary': [50000, 60000, 70000, 55000]
        }
        df = pd.DataFrame(data)
        assert len(df) == 4, "DataFrame 创建失败"
        assert list(df.columns) == ['name', 'age', 'salary'], "列名不正确"
        log_test("Pandas DataFrame 创建", True)

        # 测试2: 数据筛选
        filtered = df[df['age'] > 28]
        assert len(filtered) == 2, "数据筛选失败"
        log_test("Pandas 数据筛选", True)

        # 测试3: 数据聚合
        grouped = df.groupby('age')['salary'].mean()
        assert len(grouped) == 4, "数据聚合失败"
        log_test("Pandas 数据聚合", True)

        # 测试4: 时间序列处理
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        ts = pd.Series(np.random.randn(10), index=dates)
        assert len(ts) == 10, "时间序列创建失败"
        log_test("Pandas 时间序列", True)

        # 测试5: 数据合并
        df2 = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie', 'David'],
            'department': ['IT', 'HR', 'Finance', 'IT']
        })
        merged = pd.merge(df, df2, on='name')
        assert len(merged) == 4, "数据合并失败"
        assert 'department' in merged.columns, "合并后缺少部门列"
        log_test("Pandas 数据合并", True)

        # 测试6: 数据读取和写入
        from io import StringIO
        csv_data = StringIO("name,age,salary\nAlice,25,50000\nBob,30,60000")
        df_read = pd.read_csv(csv_data)
        assert len(df_read) == 2, "CSV 读取失败"
        log_test("Pandas CSV 读取", True)

        # 测试7: 数据统计
        stats = df.describe()
        assert 'age' in stats.columns, "统计信息失败"
        log_test("Pandas 数据统计", True)

        return True

    except Exception as e:
        log_test("Pandas 插件", False, str(e))
        return False


def test_matplotlib():
    """测试 Matplotlib 插件功能"""
    print("\n" + "="*50)
    print("测试 Matplotlib 插件")
    print("="*50)

    try:
        import matplotlib
        matplotlib.use('Agg')  # 使用非交互式后端
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import numpy as np

        # 配置中文字体（避免警告）
        # 尝试使用常见的中文字体
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
        available_fonts = [f.name for f in fm.fontManager.ttflist]

        for font_name in chinese_fonts:
            if font_name in available_fonts:
                plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                break

        # 测试1: 基本折线图
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure(figsize=(8, 6))
        plt.plot(x, y)
        plt.title('正弦波')
        plt.xlabel('x')
        plt.ylabel('sin(x)')
        plt.grid(True)
        log_test("Matplotlib 折线图", True)

        # 测试2: 散点图
        plt.figure(figsize=(8, 6))
        x = np.random.randn(100)
        y = np.random.randn(100)
        plt.scatter(x, y, alpha=0.5)
        plt.title('随机散点图')
        plt.xlabel('X')
        plt.ylabel('Y')
        log_test("Matplotlib 散点图", True)

        # 测试3: 柱状图
        plt.figure(figsize=(8, 6))
        categories = ['A', 'B', 'C', 'D']
        values = [20, 35, 30, 35]
        plt.bar(categories, values)
        plt.title('分类数据')
        plt.xlabel('类别')
        plt.ylabel('值')
        log_test("Matplotlib 柱状图", True)

        # 测试4: 直方图
        plt.figure(figsize=(8, 6))
        data = np.random.randn(1000)
        plt.hist(data, bins=30, alpha=0.7)
        plt.title('正态分布直方图')
        plt.xlabel('值')
        plt.ylabel('频次')
        log_test("Matplotlib 直方图", True)

        # 测试5: 饼图
        plt.figure(figsize=(8, 6))
        labels = ['A', 'B', 'C', 'D']
        sizes = [15, 30, 45, 10]
        plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        plt.title('数据分布')
        log_test("Matplotlib 饼图", True)

        # 测试6: 子图
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        x = np.linspace(0, 10, 100)
        axes[0, 0].plot(x, np.sin(x))
        axes[0, 0].set_title('正弦波')
        axes[0, 1].plot(x, np.cos(x))
        axes[0, 1].set_title('余弦波')
        axes[1, 0].plot(x, np.tan(x))
        axes[1, 0].set_title('正切波')
        axes[1, 1].plot(x, np.exp(-x/5))
        axes[1, 1].set_title('指数衰减')
        plt.tight_layout()
        log_test("Matplotlib 子图", True)

        # 测试7: 保存图片
        test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
        os.makedirs(test_output_dir, exist_ok=True)

        test_file = os.path.join(test_output_dir, 'test_plot.png')
        plt.figure(figsize=(8, 6))
        plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
        plt.title('测试图片')
        plt.savefig(test_file)
        plt.close()

        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            log_test("Matplotlib 保存图片", True, f"文件大小: {file_size} 字节")
            os.remove(test_file)  # 清理测试文件
        else:
            log_test("Matplotlib 保存图片", False, "文件未创建")

        return True

    except Exception as e:
        log_test("Matplotlib 插件", False, str(e))
        return False


def test_integration():
    """测试三个插件的集成使用"""
    print("\n" + "="*50)
    print("测试插件集成")
    print("="*50)

    try:
        import numpy as np
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm

        # 配置中文字体（避免警告）
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
        available_fonts = [f.name for f in fm.fontManager.ttflist]

        for font_name in chinese_fonts:
            if font_name in available_fonts:
                plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                break

        # 生成模拟数据
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        sales = np.random.randint(100, 1000, size=30)
        costs = sales * np.random.uniform(0.6, 0.8, size=30)

        # 创建 DataFrame
        df = pd.DataFrame({
            'date': dates,
            'sales': sales,
            'costs': costs,
            'profit': sales - costs
        })

        # 数据分析
        total_sales = df['sales'].sum()
        total_profit = df['profit'].sum()
        avg_profit_margin = (df['profit'] / df['sales']).mean() * 100

        log_test("集成测试 - 数据分析", True,
                f"总销售额: {total_sales}, 总利润: {total_profit:.2f}, 平均利润率: {avg_profit_margin:.2f}%")

        # 创建可视化
        test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
        os.makedirs(test_output_dir, exist_ok=True)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # 销售趋势图
        axes[0].plot(df['date'], df['sales'], label='销售额', marker='o')
        axes[0].plot(df['date'], df['costs'], label='成本', marker='s')
        axes[0].set_title('销售趋势分析')
        axes[0].set_ylabel('金额')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 利润图
        axes[1].bar(df['date'], df['profit'], color='green', alpha=0.7)
        axes[1].set_title('每日利润')
        axes[1].set_ylabel('利润')
        axes[1].set_xlabel('日期')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图片
        test_file = os.path.join(test_output_dir, 'integration_test.png')
        plt.savefig(test_file)
        plt.close()

        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            log_test("集成测试 - 可视化", True, f"图表已保存: {file_size} 字节")
            os.remove(test_file)
        else:
            log_test("集成测试 - 可视化", False, "图表未创建")

        return True

    except Exception as e:
        log_test("插件集成", False, str(e))
        return False


def print_summary():
    """打印测试摘要"""
    print("\n" + "="*50)
    print("测试摘要")
    print("="*50)

    total = len(test_results)
    passed = sum(1 for _, p, _ in test_results if p)
    failed = total - passed

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {(passed/total*100):.1f}%")

    if failed > 0:
        print("\nFailed tests:")
        for name, passed, message in test_results:
            if not passed:
                print(f"  [X] {name}: {message}")

    print("\n" + "="*50)

    # 返回退出码
    return 0 if failed == 0 else 1


def main():
    """主函数"""
    print("="*50)
    print("数据分析插件测试程序")
    print("="*50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")

    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("\n警告: 需要 Python 3.8 或更高版本")

    # 运行所有测试
    test_numpy()
    test_pandas()
    test_matplotlib()
    test_integration()

    # 打印摘要并返回
    exit_code = print_summary()

    # 清理测试输出目录
    test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    if os.path.exists(test_output_dir):
        try:
            os.rmdir(test_output_dir)
        except:
            pass

    # 等待用户输入，避免窗口闪退
    # 检测是否在冻结的打包环境中运行
    if getattr(sys, 'frozen', False):
        # 打包后的环境，不等待输入（因为没有控制台）
        print("\n程序将在 3 秒后自动退出...")
        import time
        time.sleep(3)
    else:
        # 正常 Python 环境，等待用户输入
        print("\n按任意键退出...")
        input()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
