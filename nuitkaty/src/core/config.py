"""
配置管理模块

使用 OmegaConf 提供单例模式的配置管理，支持配置加载、重载、更新和命令行生成。
"""
import os
import shutil
import time
from pathlib import Path
from typing import Any, Optional
from functools import wraps
from omegaconf import OmegaConf, DictConfig, ListConfig
from threading import RLock


def synchronized(method):
    """同步装饰器，确保线程安全

    从方法的第一个参数（self）获取 _lock 属性。
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


class ConfigMeta(type):
    """配置类的元类，实现单例模式"""
    _instances = {}
    _lock = RLock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class Config(metaclass=ConfigMeta):
    """配置管理类（单例模式）

    使用 OmegaConf 管理 config.yml 文件，提供配置加载、重载、更新和命令行生成功能。
    """

    # 目前已支持的参数白名单（只处理这些参数，忽略其他参数）
    SUPPORTED_KEYS = {
        # 编译参数
        'jobs',
        # 模式选择
        'standalone', 'onefile',
        # 编译选项
        'remove-output', 'show-progress', 'show-memory', 'quiet',
        # 优化选项
        'lto',
        # Windows 控制台选项
        'windows-console-mode', 'windows-icon-from-ico', 'windows-uac-admin', 'windows-uac-uiaccess',
        # 下载选项
        'assume-yes-for-downloads',
        # 编译器选项
        'clang', 'mingw64', 'low-memory',
        # 输出参数
        'output-filename', 'output-folder-name', 'output-dir',
        # 缓存参数
        'clean-cache',
        # 版本信息
        'company-name', 'product-name', 'file-version', 'product-version', 'file-description', 'copyright', 'trademarks',
        # 插件
        'enabled-plugins', 'disabled-plugins', 'embedded-files',
    }

    # 不需要映射的特殊键名（列表类型或需要特殊处理）
    SPECIAL_KEYS = {
        'enabled-plugins', 'disabled-plugins', 'embedded-files'
    }

    def __init__(self):
        """初始化配置管理器"""
        if getattr(self, '_initialized', False):
            return

        self._initialized = True
        self._config: Optional[DictConfig] = None
        self._lock = RLock()
        self._config_path = self._get_config_path()
        self._deleted = False

        # 运行时参数（不保存到配置文件，避免重新加载后丢失）
        self._entry_file = ""
        self._output_dir = ""
        self._output_filename = ""
        self._icon_path = ""

        # 自动初始化配置：检测文件是否存在，不存在则创建，存在则加载
        self._auto_initialize()

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        config_dir = Path(user_profile) / ".nuitkaty"
        return config_dir / "config.yml"

    def _auto_initialize(self) -> None:
        """自动初始化配置

        检测配置文件是否存在：
        - 若不存在，则创建默认配置后加载
        - 若存在，则直接加载
        """
        # 确保配置目录存在
        self._ensure_config_dir()

        # 检查配置文件是否存在
        if not self._config_path.exists():
            # 创建默认配置（从项目配置复制）
            self._create_default_config()

        # 加载配置文件
        self.load()

    @staticmethod
    def _get_project_config_path() -> Optional[Path]:
        """获取项目配置文件路径（nuitkaty/config/config.yml）

        Returns:
            Optional[Path]: 项目配置文件路径，如果不存在则返回 None
        """
        # 当前文件: nuitkaty/src/core/config.py
        # 向上三级到项目根目录: nuitkaty/
        project_root = Path(__file__).parent.parent.parent
        project_config = project_root / "config" / "config.yml"

        if project_config.exists():
            return project_config
        return None

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        config_dir = self._config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)

    @synchronized
    def load(self) -> DictConfig:
        """加载配置文件

        Returns:
            DictConfig: 加载的配置对象

        Raises:
            RuntimeError: 配置文件不存在或加载失败
        """
        try:
            self._config = OmegaConf.load(self._config_path)
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")

        return self._config

    @synchronized
    def reload(self) -> DictConfig:
        """重新加载配置文件

        Returns:
            DictConfig: 重新加载的配置对象
        """
        try:
            self._config = OmegaConf.load(self._config_path)
            return self._config
        except Exception as e:
            raise RuntimeError(f"重新加载配置文件失败: {e}")

    @synchronized
    def update(self, **kwargs) -> None:
        """更新配置值并保存到文件

        Args:
            **kwargs: 要更新的配置键值对，支持点号分割的嵌套路径
                     例如: nuitka_jobs=8（会更新 nuitka.jobs）

        Example:
            config.update(**{"nuitka.jobs": 8})
            config.update(**{"python.interpreter_path": "path/to/python"})
        """
        if self._config is None:
            self.load()

        # 更新配置
        for key, value in kwargs.items():
            OmegaConf.update(self._config, key, value)

        # 处理 standalone 和 onefile 的互斥逻辑
        standalone_key = None
        onefile_key = None

        # 检查是否更新了 standalone 或 onefile
        for key in kwargs:
            if 'standalone' in key:
                standalone_key = key
            elif 'onefile' in key:
                onefile_key = key

        # 互斥过滤机制
        if standalone_key and kwargs.get(standalone_key) is True:
            # 设置 standalone=True 时，强制 onefile=False
            if onefile_key:
                OmegaConf.update(self._config, onefile_key, False)
            elif OmegaConf.select(self._config, 'nuitka.onefile'):
                OmegaConf.update(self._config, 'nuitka.onefile', False)

        if onefile_key and kwargs.get(onefile_key) is True:
            # 设置 onefile=True 时，强制 standalone=False
            if standalone_key:
                OmegaConf.update(self._config, standalone_key, False)
            elif OmegaConf.select(self._config, 'nuitka.standalone'):
                OmegaConf.update(self._config, 'nuitka.standalone', False)

        # 保存到文件
        self._save()

    @synchronized
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套路径，如 "nuitka.jobs"
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        if self._config is None:
            if self._deleted:
                # 已删除，返回默认值
                return default
            else:
                self.load()

        try:
            return OmegaConf.select(self._config, key, default=default)
        except Exception:
            return default

    @synchronized
    def set(self, key: str, value: Any) -> None:
        """设置配置值（不保存到文件）

        Args:
            key: 配置键，支持点号分隔的嵌套路径
            value: 配置值
        """
        self.update(**{key: value})

    @synchronized
    def temp(self, **kwargs) -> None:
        """临时更新配置值（仅修改内存，不保存到文件）

        与 update() 方法类似，但不会将修改持久化到配置文件。
        适用于临时修改配置或批量修改后再统一保存的场景。

        Args:
            **kwargs: 要更新的配置键值对，支持点号分割的嵌套路径
                     例如: nuitka_jobs=8（会更新 nuitka.jobs）

        Example:
            # 临时修改配置（不保存到文件）
            config.temp(**{"nuitka.jobs": 8})

            # 批量临时修改后，如需保存可再调用 update()
            config.temp(**{"nuitka.jobs": 8, "nuitka.quiet": True})
            # 如果确定要保存，再调用:
            # config.update(**{"nuitka.jobs": 8, "nuitka.quiet": True})
        """
        if self._config is None:
            self.load()

        # 更新运行时参数（只修改类属性，不修改配置文件）
        for key, value in kwargs.items():
            if key == "nuitka.entry-file":
                self._entry_file = value
            elif key == "nuitka.output-dir":
                self._output_dir = value
            elif key == "nuitka.output-filename":
                self._output_filename = value
            elif key == "nuitka.windows-icon-from-ico":
                self._icon_path = value
            # 其他参数忽略，只处理运行时参数

    def to_command(self) -> str:
        """将配置转换为 Nuitka 命令行

        Returns:
            str: 完整的 Nuitka 命令行字符串
        """
        if self._config is None:
            self.load()

        python = self._config.get("python", "").get("path", "")
        # 基础命令
        parts = [python, "-m", "nuitka"]
        # Nuitka 选项（直接遍历配置项，键名直接对应命令行参数）
        nuitka = self._config.get("nuitka", {})

        # output-dir（从类属性读取，只在值不为空时添加）
        if self._output_dir:
            parts.append(f'--output-dir={self._quote_path(self._output_dir)}')

        # output-filename（从类属性读取，只在值不为空时添加）
        if self._output_filename:
            output_filename = self._output_filename
            if not output_filename.endswith('.exe'):
                output_filename += '.exe'
            parts.append(f'--output-filename={self._quote_path(output_filename)}')

        # windows-icon-from-ico（从类属性读取，只在值不为空时添加）
        if self._icon_path:
            parts.append(f'--windows-icon-from-ico={self._quote_path(self._icon_path)}')


        if not nuitka:
            nuitka = {}

        for key, value in nuitka.items():
            # 跳过特殊处理的键名
            if key in self.SPECIAL_KEYS:
                continue

            # 跳过空列表和空字典（包括 OmegaConf 类型）
            if isinstance(value, (list, ListConfig, dict, DictConfig)):
                if not value:  # 空列表或空字典
                    continue
                # 列表类型参数需要特殊处理（添加多个参数）
                if isinstance(value, (list, ListConfig)):
                    for item in value:
                        if item is not None and item != '':
                            parts.append(f"--{key}={item}")
                continue

            if value is None or value in ["auto","none", "", 0, False,"False","false"]:
                continue


            # 无值参数：布尔类型，true 时添加参数
            if isinstance(value, bool):
                if value:
                    parts.append(f"--{key}")
            # 有值参数：所有字符串都用引号包裹
            elif isinstance(value, str):
                parts.append(f'--{key}={self._quote_path(value)}')
            # 数值类型：直接转换为字符串
            else:
                parts.append(f"--{key}={value}")

        # 插件
        enabled_plugins = nuitka.get("enabled-plugins", [])
        if enabled_plugins:
            for plugin in enabled_plugins:
                parts.append(f"--enable-plugin={plugin}")

        disabled_plugins = nuitka.get("disabled-plugins", [])
        if disabled_plugins:
            for plugin in disabled_plugins:
                parts.append(f"--disable-plugin={plugin}")

        # 嵌入文件
        embedded_files = nuitka.get("embedded-files", [])
        if embedded_files:
            for file_info in embedded_files:
                # 支持字典格式
                if isinstance(file_info, dict):
                    source = file_info.get('source-path', '')
                    dest = file_info.get('destination-path', '')
                    if source and dest:
                        parts.append(f"--include-data-files={self._quote_path(source)}={dest}")

        # 添加入口文件路径（从类属性读取，命令的最后一个参数）
        if self._entry_file:
            parts.append(self._quote_path(self._entry_file))

        return " ".join(parts)
    @staticmethod
    def _quote_path(path: str) -> str:
        """处理参数值：规范化路径并处理特殊字符

        注意：此方法不再添加引号，引号由调用者统一添加

        Args:
            path: 文件路径或参数值

        Returns:
            str: 处理后的值
        """
        # 规范化路径分隔符
        normalized_path = path.replace('\\', '/')

        # 对于包含特殊字符（如引号）的字符串，进行转义
        # Windows 命令行中，双引号需要转义为 \"
        if '"' in normalized_path:
            normalized_path = normalized_path.replace('"', '\\"')

        return normalized_path

    def _create_default_config(self) -> None:
        """创建默认配置文件

        优先从项目目录 nuitkaty/config/config.yml 复制配置，
        如果不存在则创建内置的默认配置。
        """
        config_file = self._config_path

        # 确保目标目录存在
        self._ensure_config_dir()

        # 尝试从项目配置目录复制
        project_config = self._get_project_config_path()
        if project_config and project_config.exists():
            try:
                # 先删除旧文件（如果存在）
                if config_file.exists():
                    config_file.unlink()

                # 复制文件
                shutil.copy2(project_config, config_file)

                # 等待文件系统完成写入（解决 Windows 延迟问题）
                time.sleep(0.1)

                # 验证文件是否真的被创建
                if not config_file.exists():
                    raise RuntimeError("配置文件复制后未找到文件")
            except Exception as e:
                raise RuntimeError(f"复制项目配置文件失败: {e}")



    def _save(self) -> None:
        """保存配置到文件"""
        config_file = self._config_path
        # OmegaConf.save 需要字符串路径，确保转换为字符串
        OmegaConf.save(self._config, str(config_file))

    @synchronized
    def delete(self) -> bool:
        """删除用户配置文件

        Returns:
            bool: 是否成功删除

        Raises:
            RuntimeError: 删除配置文件失败
        """
        # 删除用户配置文件
        if self._config_path.exists():
            try:
                self._config_path.unlink()
            except Exception as e:
                raise RuntimeError(f"删除配置文件失败: {e}")

        # 清空内存中的配置
        self._config = None
        # 设置删除标记，防止自动重新加载
        self._deleted = True

        return True

    @property
    def config(self) -> DictConfig:
        """获取当前配置对象（只读）"""
        if self._config is None:
            if self._deleted:
                # 已删除，返回空配置
                return OmegaConf.create()
            else:
                self.load()
        return self._config

    @property
    def config_path(self) -> Path:
        """获取配置文件路径（只读）"""
        return self._config_path


# 创建全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例（单例）

    Returns:
        Config: 配置实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
