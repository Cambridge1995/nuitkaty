"""
路径检测器

自动检测Python解释器、pip镜像源和GCC编译器。
从Windows注册表查找Python安装,测试镜像源速度,检测可用的编译器。
"""
import os
import winreg
import subprocess
import time
from typing import List, Dict, Optional, Tuple


class PathDetector:
    """路径检测器

    提供自动检测功能:
    - Python解释器: 从Windows注册表和常见安装路径检测
    - pip镜像源: 测试多个镜像源速度并排序
    - GCC编译器: 检测MSVC和MinGW64
    """

    # 默认pip镜像源列表 (字典格式)
    DEFAULT_PIP_MIRRORS: List[Dict[str, str]] = [
        {"name": "PyPI官方", "url": "https://pypi.org/simple"},
        {"name": "清华大学", "url": "https://pypi.tuna.tsinghua.edu.cn/simple"},
        {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple/"},
        {"name": "中国科技大学", "url": "https://pypi.mirrors.ustc.edu.cn/simple"},
        {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple"},
        {"name": "腾讯云", "url": "https://mirrors.cloud.tencent.com/pypi/simple"}
    ]

    # 旧版格式的镜像源列表 (保留用于向后兼容)
    PIP_MIRRORS = [
        ("PyPI官方", "https://pypi.org/simple"),
        ("清华大学", "https://pypi.tuna.tsinghua.edu.cn/simple"),
        ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"),
        ("中国科技大学", "https://pypi.mirrors.ustc.edu.cn/simple"),
        ("华为云", "https://repo.huaweicloud.org/repository/pypi/simple"),
        ("腾讯云", "https://mirrors.cloud.tencent.com/pypi/simple")
    ]

    def detect_python_interpreters(self) -> List[Dict[str, str]]:
        """检测系统中已安装的Python解释器

        从Windows注册表和常见安装路径查找Python。

        Returns:
            List[Dict[str, str]]: Python解释器列表,每个包含name和path字段
        """
        pythons = []

        # 1. 从注册表检测
        pythons.extend(self._detect_from_registry())

        # 2. 从常见安装路径检测
        pythons.extend(self._detect_from_common_paths())

        # 3. 去重并验证
        unique_pythons = self._deduplicate_pythons(pythons)

        return unique_pythons

    def _detect_from_registry(self) -> List[Dict[str, str]]:
        """从Windows注册表检测Python

        Returns:
            List[Dict[str, str]]: Python解释器列表
        """
        pythons = []
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Python\PythonCore"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Python\PythonCore"),
            (winreg.HKEY_CURRENT_USER, r"Software\Wow6432Node\Python\PythonCore"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Python\PythonCore")
        ]

        for root_key, sub_key_path in registry_paths:
            try:
                with winreg.OpenKey(root_key, sub_key_path) as key:
                    # 遍历所有版本
                    i = 0
                    while True:
                        try:
                            version = winreg.EnumKey(key, i)
                            i += 1

                            # 获取安装路径
                            try:
                                install_path_key = winreg.OpenKey(key, f"{version}\\InstallPath")
                                install_path, _ = winreg.QueryValueEx(install_path_key, "")
                                winreg.CloseKey(install_path_key)

                                # 构建Python可执行文件路径
                                python_exe = os.path.join(install_path, "python.exe")
                                if os.path.exists(python_exe):
                                    pythons.append({
                                        "name": f"Python {version}",
                                        "path": python_exe
                                    })
                            except (OSError, FileNotFoundError):
                                continue

                        except OSError:
                            break

            except (OSError, FileNotFoundError):
                continue

        return pythons

    def _detect_from_common_paths(self) -> List[Dict[str, str]]:
        """从常见安装路径检测Python

        Returns:
            List[Dict[str, str]]: Python解释器列表
        """
        pythons = []

        # Windows常见Python安装路径
        common_paths = [
            os.path.expanduser(r"~\AppData\Local\Programs\Python"),
            os.path.expanduser(r"~\AppData\Roaming\Python"),
            r"C:\Python",
            r"C:\Python39",
            r"C:\Python310",
            r"C:\Python311",
            r"C:\Python312"
        ]

        for base_path in common_paths:
            if not os.path.exists(base_path):
                continue

            try:
                # 遍历子目录(版本号)
                for item in os.listdir(base_path):
                    python_exe = os.path.join(base_path, item, "python.exe")
                    if os.path.exists(python_exe):
                        # 尝试获取版本
                        try:
                            result = subprocess.run(
                                [python_exe, "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            version = result.stdout.strip().replace("Python ", "")
                            name = f"Python {version}"
                        except Exception:
                            name = f"Python ({item})"

                        pythons.append({
                            "name": name,
                            "path": python_exe
                        })
            except (PermissionError, OSError):
                continue

        return pythons

    def _deduplicate_pythons(self, pythons: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """去除重复的Python解释器

        Args:
            pythons: Python解释器列表

        Returns:
            List[Dict[str, str]]: 去重后的列表
        """
        seen = set()
        unique = []

        for python in pythons:
            path_lower = python["path"].lower()
            if path_lower not in seen:
                seen.add(path_lower)
                unique.append(python)

        return unique

    def detect_pip_mirrors(
        self, timeout: int = 5, config: Optional["Configuration"] = None
    ) -> List[Dict[str, any]]:
        """测试pip镜像源速度并排序

        Args:
            timeout: 每个测试的超时时间(秒)
            config: 可选的配置对象，用于从配置加载镜像源列表

        Returns:
            List[Dict]: 镜像源列表,按速度排序,包含name, url, time字段
        """
        results = []

        # 确定要测试的镜像源列表
        mirror_list: List[Tuple[str, str]] = []

        if config and config.pip.mirrors:
            # 从配置加载镜像源
            for mirror in config.pip.mirrors:
                mirror_list.append((mirror.name, mirror.url))
        else:
            # 使用默认镜像源列表 (降级逻辑)
            for mirror in self.DEFAULT_PIP_MIRRORS:
                mirror_list.append((mirror.name, mirror.url))

        for name, url in mirror_list:
            start_time = time.time()

            try:
                # 使用ping测试速度
                # 从URL提取主机名
                host = url.replace("https://", "").replace("http://", "").split("/")[0]

                # Windows使用ping命令
                process = subprocess.Popen(
                    ["ping", "-n", "2", "-w", str(timeout * 1000), host],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, _ = process.communicate(timeout=timeout + 2)

                elapsed = time.time() - start_time

                if process.returncode == 0:
                    # 从ping输出提取平均时间
                    output = stdout.decode('gbk', errors='ignore')
                    avg_time = self._extract_ping_time(output)

                    results.append({
                        "name": name,
                        "url": url,
                        "time": avg_time or elapsed * 1000  # 转换为毫秒
                    })
                else:
                    # 无法ping通,标记为超时
                    results.append({
                        "name": name,
                        "url": url,
                        "time": -1  # -1表示不可用
                    })

            except subprocess.TimeoutExpired:
                results.append({
                    "name": name,
                    "url": url,
                    "time": -1
                })
            except Exception:
                results.append({
                    "name": name,
                    "url": url,
                    "time": -1
                })

        # 按时间排序,可用的在前,不可用的在后
        results.sort(key=lambda x: (x["time"] == -1, x["time"]))

        return results

    def _extract_ping_time(self, ping_output: str) -> Optional[int]:
        """从ping输出提取平均时间

        Args:
            ping_output: ping命令的输出

        Returns:
            Optional[int]: 平均时间(毫秒),提取失败返回None
        """
        try:
            # 中文Windows: "平均 = 10ms"
            # 英文Windows: "Average = 10ms"
            for line in ping_output.split('\n'):
                if '平均' in line or 'Average' in line:
                    # 提取数字
                    import re
                    match = re.search(r'(\d+)\s*ms', line, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
        except Exception:
            pass

        return None

    def detect_gcc(self) -> List[Dict[str, any]]:
        """检测系统中可用的C编译器

        检测MSVC和MinGW64编译器。

        Returns:
            List[Dict]: 编译器列表,每个包含type, name, path字段
        """
        compilers = []

        # 1. 检测MSVC
        msvc_compilers = self._detect_msvc()
        compilers.extend(msvc_compilers)

        # 2. 检测MinGW64
        mingw_compilers = self._detect_mingw64()
        compilers.extend(mingw_compilers)

        return compilers

    def _detect_msvc(self) -> List[Dict[str, any]]:
        """检测MSVC编译器

        使用 vswhere 工具检测 Visual Studio 安装。

        Returns:
            List[Dict]: MSVC编译器列表
        """
        compilers = []

        # 优先使用 vswhere 工具检测 Visual Studio 安装
        vswhere_paths = [
            r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe",
            r"%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe"
        ]

        vswhere_exe = None
        for path in vswhere_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                vswhere_exe = expanded_path
                break

        if vswhere_exe:
            try:
                # 使用 vswhere 查找所有安装了 VC Tools 的 Visual Studio
                cmd = [
                    vswhere_exe,
                    "-latest", "-products", "*",
                    "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                    "-property", "installationPath",
                    "-property", "displayName",
                    "-format", "json"
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout:
                    import json
                    try:
                        installations = json.loads(result.stdout)
                        for install in installations:
                            install_path = install.get("installationPath")
                            display_name = install.get("displayName", "Visual Studio")

                            if install_path:
                                # 查找 MSVC 工具版本
                                msvc_path = os.path.join(install_path, "VC", "Tools", "MSVC")
                                if os.path.exists(msvc_path):
                                    try:
                                        for version in os.listdir(msvc_path):
                                            bin_path = os.path.join(msvc_path, version, "bin", "Hostx64", "x64")
                                            cl_exe = os.path.join(bin_path, "cl.exe")
                                            if os.path.exists(cl_exe):
                                                compilers.append({
                                                    "type": "msvc",
                                                    "name": f"{display_name} (MSVC {version})",
                                                    "path": bin_path
                                                })
                                                break  # 只取第一个找到的版本
                                    except (PermissionError, OSError):
                                        continue
                    except json.JSONDecodeError:
                        pass
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # 如果 vswhere 没有找到，尝试传统方法
        if not compilers:
            compilers.extend(self._detect_msvc_legacy())

        return compilers

    def _detect_msvc_legacy(self) -> List[Dict[str, any]]:
        """使用传统方法检测MSVC编译器（备用方案）

        Returns:
            List[Dict]: MSVC编译器列表
        """
        compilers = []

        # Visual Studio常见安装路径
        vs_paths = [
            os.path.expandvars(r"%ProgramFiles%\Microsoft Visual Studio"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio"),
            os.path.expandvars(r"D:\Microsoft Visual Studio"),  # 添加 D 盘路径
        ]

        for vs_base_path in vs_paths:
            if not os.path.exists(vs_base_path):
                continue

            try:
                for version_dir in os.listdir(vs_base_path):
                    version_path = os.path.join(vs_base_path, version_dir)
                    if not os.path.isdir(version_path):
                        continue

                    # 查找 edition 或 BuildTools
                    for edition in os.listdir(version_path):
                        # 查找cl.exe
                        cl_path = os.path.join(version_path, edition, "VC", "Tools", "MSVC")
                        if os.path.exists(cl_path):
                            for ver in os.listdir(cl_path):
                                bin_path = os.path.join(cl_path, ver, "bin", "Hostx64", "x64")
                                cl_exe = os.path.join(bin_path, "cl.exe")
                                if os.path.exists(cl_exe):
                                    compilers.append({
                                        "type": "msvc",
                                        "name": f"MSVC {edition} {ver}",
                                        "path": bin_path
                                    })
            except (PermissionError, OSError):
                continue

        return compilers

    def _detect_mingw64(self) -> List[Dict[str, any]]:
        """检测MinGW64编译器

        Returns:
            List[Dict]: MinGW64编译器列表
        """
        compilers = []

        # MinGW64常见安装路径
        mingw_paths = [
            r"C:\msys64\mingw64\bin",
            r"C:\mingw64\bin",
            r"C:\TDM-GCC-64\bin",
            r"C:\MinGW\bin",
            os.path.expanduser(r"~\AppData\Local\Programs\mingw64\bin")
        ]

        for mingw_path in mingw_paths:
            gcc_exe = os.path.join(mingw_path, "gcc.exe")
            if os.path.exists(gcc_exe):
                # 尝试获取版本
                try:
                    result = subprocess.run(
                        [gcc_exe, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    first_line = result.stdout.split('\n')[0]
                    compilers.append({
                        "type": "mingw64",
                        "name": f"MinGW64 ({first_line.strip()})",
                        "path": mingw_path
                    })
                except Exception:
                    compilers.append({
                        "type": "mingw64",
                        "name": "MinGW64",
                        "path": mingw_path
                    })

        # 从PATH检测
        try:
            result = subprocess.run(
                ["where", "gcc.exe"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                gcc_path = result.stdout.strip().split('\n')[0]
                gcc_dir = os.path.dirname(gcc_path)
                if "mingw" in gcc_dir.lower():
                    compilers.append({
                        "type": "mingw64",
                        "name": "MinGW64 (PATH)",
                        "path": gcc_dir
                    })
        except Exception:
            pass

        return compilers

    def find_fastest_mirror(self) -> Optional[str]:
        """查找最快的pip镜像源

        Returns:
            Optional[str]: 最快镜像源的URL,如果没有可用的返回None
        """
        mirrors = self.detect_pip_mirrors()

        if mirrors and mirrors[0]["time"] != -1:
            return mirrors[0]["url"]

        return None

    def find_best_python(self) -> Optional[str]:
        """查找最佳Python解释器(推荐版本)

        优先选择Python 3.11+

        Returns:
            Optional[str]: Python解释器路径,未找到返回None
        """
        pythons = self.detect_python_interpreters()

        # 优先选择Python 3.11+
        for python in pythons:
            version_str = python["name"].replace("Python ", "").split()[0]
            try:
                version_parts = version_str.split(".")
                if len(version_parts) >= 2:
                    major, minor = int(version_parts[0]), int(version_parts[1])
                    if major == 3 and minor >= 11:
                        return python["path"]
            except (ValueError, IndexError):
                continue

        # 如果没有3.11+,返回第一个可用的
        if pythons:
            return pythons[0]["path"]

        return None
