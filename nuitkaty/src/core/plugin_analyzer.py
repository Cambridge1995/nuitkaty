"""
插件分析器模块

通过静态分析 Python 代码,检测需要的 Nuitka 插件。
"""
import ast
import os


class PluginAnalyzer:
    """插件分析器

    使用 AST 解析 Python 文件,检测导入的模块并映射到 Nuitka 插件。
    """

    # 导入到插件的映射（仅限 Nuitka 官方支持的插件）
    # 官方插件列表: https://nuitka.net/doc/user-manual.html#plugin-list
    # 注意: numpy 已被 Nuitka 自动处理，不再需要插件
    IMPORT_TO_PLUGIN = {
        # Qt 相关
        "PyQt5": "qt-plugins",
        "PyQt6": "qt-plugins",
        "PySide2": "qt-plugins",
        "PySide6": "qt-plugins",
        # Pillow (PIL)
        "PIL": "pillow",
        "PIL.Image": "pillow",
        "PIL.ImageQt": "pillow",
        # Tkinter
        "tkinter": "tk-inter",
        # Pygame
        "pygame": "pygame",
    }

    @classmethod
    def analyze_entry_file(cls, entry_file: str) -> dict:
        """分析入口文件,检测需要的插件

        Args:
            entry_file: 入口 Python 文件路径

        Returns:
            dict: 分析结果
                {
                    "required_plugins": list[str],  # 必需的插件
                    "optional_plugins": list[str],  # 可选的插件
                    "imports": list[str],            # 所有导入
                }
        """
        if not os.path.exists(entry_file):
            return {
                "required_plugins": [],
                "optional_plugins": [],
                "imports": [],
            }

        # 解析导入
        imports = cls._parse_imports(entry_file)

        # 映射到插件
        plugin_mapping = cls._map_imports_to_plugins(imports)

        return {
            "required_plugins": plugin_mapping.get("required", []),
            "optional_plugins": plugin_mapping.get("optional", []),
            "imports": list(imports),
        }

    @classmethod
    def _parse_imports(cls, file_path: str) -> set[str]:
        """解析 Python 文件的所有导入

        支持递归分析本地模块导入。

        Args:
            file_path: 文件路径

        Returns:
            set[str]: 导入模块集合
        """
        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)
            imports.update(cls._extract_imports_from_ast(tree))

            # 递归分析本地模块
            directory = os.path.dirname(file_path)
            for imp in list(imports):
                local_imports = cls._analyze_local_import(imp, directory)
                imports.update(local_imports)

        except (SyntaxError, UnicodeDecodeError, OSError) as e:
            # 无法解析文件,返回空集合
            pass

        return imports

    @classmethod
    def _extract_imports_from_ast(cls, tree: ast.AST) -> set[str]:
        """从 AST 中提取导入的模块

        Args:
            tree: AST 树

        Returns:
            set[str]: 导入模块集合
        """
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        return imports

    @classmethod
    def _analyze_local_import(cls, imp: str, base_dir: str) -> set[str]:
        """分析本地模块的导入

        如果导入的是本地模块文件,递归分析其导入。

        Args:
            imp: 导入模块名
            base_dir: 基础目录

        Returns:
            set[str]: 本地模块的导入集合
        """
        imports = set()

        # 检查是否为本地模块
        local_file = os.path.join(base_dir, f"{imp}.py")
        if os.path.exists(local_file):
            imports.update(cls._parse_imports(local_file))

        return imports

    @classmethod
    def _map_imports_to_plugins(cls, imports: set[str]) -> dict:
        """将导入映射到插件

        Args:
            imports: 导入模块集合

        Returns:
            dict: {required: list[str], optional: list[str]}
        """
        required_plugins = set()
        optional_plugins = set()

        for imp in imports:
            # 精确匹配
            if imp in cls.IMPORT_TO_PLUGIN:
                required_plugins.add(cls.IMPORT_TO_PLUGIN[imp])

            # 前缀匹配 (例如 PySide6.QtWidgets 匹配 PySide6)
            for key, plugin in cls.IMPORT_TO_PLUGIN.items():
                if imp.startswith(f"{key}."):
                    required_plugins.add(plugin)

        # 去重并排序
        return {
            "required": sorted(list(required_plugins)),
            "optional": sorted(list(optional_plugins)),
        }

    @classmethod
    def get_available_plugins(cls) -> list[str]:
        """获取所有可用的 Nuitka 插件列表

        Returns:
            list[str]: 插件名称列表
        """
        return sorted(set(cls.IMPORT_TO_PLUGIN.values()))
