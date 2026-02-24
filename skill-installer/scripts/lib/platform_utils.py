"""
跨平台工具函数 - 处理不同操作系统间的差异
"""

import platform
import subprocess
import ctypes
import os
import shutil
from pathlib import Path
from typing import Union, Optional


class PlatformInfo:
    """跨平台信息获取"""
    
    _instance = None
    _system = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def get_system() -> str:
        """
        返回标准化平台名称
        Returns: 'macos' | 'linux' | 'windows'
        """
        if PlatformInfo._system is None:
            system = platform.system().lower()
            if system == "darwin":
                PlatformInfo._system = "macos"
            else:
                PlatformInfo._system = system  # 'linux' 或 'windows'
        return PlatformInfo._system
    
    @staticmethod
    def is_windows() -> bool:
        """是否为 Windows 系统"""
        return PlatformInfo.get_system() == "windows"
    
    @staticmethod
    def is_macos() -> bool:
        """是否为 macOS 系统"""
        return PlatformInfo.get_system() == "macos"
    
    @staticmethod
    def is_linux() -> bool:
        """是否为 Linux 系统"""
        return PlatformInfo.get_system() == "linux"
    
    @staticmethod
    def is_unix_like() -> bool:
        """是否为类 Unix 系统（macOS 或 Linux）"""
        return PlatformInfo.is_macos() or PlatformInfo.is_linux()
    
    @staticmethod
    def get_home_dir() -> Path:
        """获取用户家目录"""
        return Path.home()
    
    @staticmethod
    def get_kimi_dir() -> Path:
        """获取 Kimi 配置目录"""
        return PlatformInfo.get_home_dir() / ".kimi"
    
    @staticmethod
    def get_skills_dir() -> Path:
        """获取 Kimi skills 目录"""
        return PlatformInfo.get_kimi_dir() / "skills"
    
    @staticmethod
    def get_shell() -> str:
        """获取当前 shell 类型（用于显示命令）"""
        if PlatformInfo.is_windows():
            return "powershell"
        
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return "zsh"
        elif "bash" in shell:
            return "bash"
        return "sh"


class PlatformUtils:
    """跨平台工具方法"""
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> str:
        """规范化路径（展开 ~，统一分隔符）"""
        expanded = os.path.expanduser(str(path))
        normalized = os.path.normpath(expanded)
        return normalized
    
    @staticmethod
    def to_posix_path(path: Union[str, Path]) -> str:
        """转换为使用 / 分隔符的路径（用于显示）"""
        return str(path).replace(os.sep, "/")
    
    @staticmethod
    def calculate_relative_path(from_path: Path, to_path: Path) -> str:
        """
        计算相对路径（跨平台统一使用 / 分隔符）
        Windows 跨驱动器时返回绝对路径
        
        Args:
            from_path: 源路径（软连接指向的目标）
            to_path: 目标路径（软连接所在位置）
        
        Returns:
            相对路径字符串（使用 / 分隔符），跨驱动器时返回绝对路径
        """
        # 确保都是绝对路径
        from_abs = Path(from_path).resolve()
        to_abs = Path(to_path).resolve()
        
        # Windows 跨驱动器场景需要特殊处理
        if PlatformInfo.is_windows():
            # 检查是否同驱动器（盘符）
            if from_abs.drive != to_abs.drive:
                # 跨驱动器：返回绝对路径（软连接支持绝对路径）
                return PlatformUtils.to_posix_path(from_abs)
        
        # 同驱动器或非 Windows：计算相对路径
        rel = os.path.relpath(from_abs, to_abs.parent)
        # 统一使用 / 分隔符便于显示
        return PlatformUtils.to_posix_path(rel)
    
    @staticmethod
    def is_admin() -> bool:
        """检测当前是否具有管理员/Root 权限"""
        if PlatformInfo.is_windows():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception:
                return False
        else:
            # Unix-like 系统检查 uid
            return os.geteuid() == 0
    
    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """确保目录存在，不存在则创建"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def remove_dir(path: Path, ignore_errors: bool = False) -> bool:
        """删除目录及其内容"""
        try:
            if path.exists():
                shutil.rmtree(path, ignore_errors=ignore_errors)
            return True
        except Exception:
            if not ignore_errors:
                raise
            return False


class SymlinkManager:
    """软连接管理器 - 处理跨平台软连接创建/删除"""
    
    @staticmethod
    def create_symlink(source: Union[str, Path], target: Union[str, Path]) -> None:
        """
        创建软连接（跨平台）
        
        Args:
            source: 源路径（真实文件/目录）
            target: 目标路径（软连接位置）
        
        Raises:
            PermissionError: Windows 下无管理员权限
            FileExistsError: 目标已存在
            OSError: 其他系统错误
        """
        source = Path(source).resolve()
        target = Path(target)
        
        # 确保源存在
        if not source.exists():
            raise FileNotFoundError(f"源路径不存在: {source}")
        
        # 确保目标父目录存在
        PlatformUtils.ensure_dir(target.parent)
        
        # 如果目标已存在，先删除
        if target.exists() or target.is_symlink():
            SymlinkManager.remove_symlink(target)
        
        if PlatformInfo.is_windows():
            SymlinkManager._create_symlink_windows(source, target)
        else:
            SymlinkManager._create_symlink_unix(source, target)
    
    @staticmethod
    def _create_symlink_unix(source: Path, target: Path) -> None:
        """Unix-like 系统创建软连接"""
        target.symlink_to(source, target_is_directory=source.is_dir())
    
    @staticmethod
    def _create_symlink_windows(source: Path, target: Path) -> None:
        """
        Windows 创建目录联接/符号链接
        注意：需要管理员权限
        """
        source_str = str(source)
        target_str = str(target)
        
        # 判断是文件还是目录
        is_dir = source.is_dir()
        
        try:
            # 尝试使用 ctypes 创建（Python 3.8+ 的 os.symlink 在 Windows 上也需要管理员权限）
            # 使用 mklink 命令
            if is_dir:
                cmd = ["cmd", "/c", "mklink", "/D", target_str, source_str]
            else:
                cmd = ["cmd", "/c", "mklink", target_str, source_str]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.lower() if e.stderr else ""
            if "拒绝访问" in (e.stderr or "") or "access denied" in error_msg:
                raise PermissionError(
                    f"Windows 创建软连接需要管理员权限。\n"
                    f"请以管理员身份重新运行，或手动执行：\n"
                    f"  cmd /c mklink {'/D ' if is_dir else ''}\"{target_str}\" \"{source_str}\""
                )
            raise OSError(f"创建软连接失败: {e.stderr or e.stdout}")
        except FileNotFoundError:
            # cmd 不存在（极少见）
            raise OSError("无法找到 cmd.exe，请检查系统环境")
    
    @staticmethod
    def remove_symlink(path: Union[str, Path]) -> bool:
        """
        删除软连接（不删除指向的目标）
        
        Returns:
            是否成功删除
        """
        path = Path(path)
        
        if not path.exists() and not path.is_symlink():
            return False
        
        try:
            if path.is_dir() and not path.is_symlink():
                # 是真实目录，使用 rmdir
                shutil.rmtree(path)
            else:
                # 是文件或软连接，直接删除
                path.unlink()
            return True
        except Exception:
            return False
    
    @staticmethod
    def is_symlink(path: Union[str, Path]) -> bool:
        """检查路径是否为软连接"""
        return Path(path).is_symlink()
    
    @staticmethod
    def read_symlink(path: Union[str, Path]) -> Optional[Path]:
        """读取软连接指向的目标"""
        path = Path(path)
        if path.is_symlink():
            return Path(os.readlink(path))
        return None
    
    @staticmethod
    def verify_symlink(path: Union[str, Path]) -> bool:
        """
        验证软连接是否可读（指向的目标存在）
        
        Returns:
            软连接是否有效
        """
        path = Path(path)
        if not path.is_symlink():
            return False
        
        try:
            target = path.resolve()
            return target.exists()
        except Exception:
            return False


class DeleteCommandGenerator:
    """删除命令生成器 - 生成当前平台的删除命令"""
    
    @staticmethod
    def get_delete_command(path: Union[str, Path], item_type: str = "auto") -> str:
        """
        获取当前平台的删除命令（用于显示给用户）
        
        Args:
            path: 要删除的路径
            item_type: 'file' | 'dir' | 'auto'
        
        Returns:
            适用于当前平台的删除命令字符串
        """
        path = Path(path)
        path_str = str(path)
        
        # 自动判断类型
        if item_type == "auto":
            if path.is_dir() and not path.is_file():
                item_type = "dir"
            else:
                item_type = "file"
        
        system = PlatformInfo.get_system()
        
        if system == "windows":
            # Windows PowerShell 格式
            path_str = path_str.replace("/", "\\")
            if item_type == "dir":
                return f'Remove-Item -Recurse -Force "{path_str}"'
            else:
                return f'Remove-Item -Force "{path_str}"'
        else:
            # macOS / Linux
            if item_type == "dir":
                return f"rm -rf '{path_str}'"
            else:
                return f"rm -f '{path_str}'"
    
    @staticmethod
    def get_rmdir_command(path: Union[str, Path]) -> str:
        """获取删除目录的命令"""
        return DeleteCommandGenerator.get_delete_command(path, "dir")
    
    @staticmethod
    def get_rmfile_command(path: Union[str, Path]) -> str:
        """获取删除文件的命令"""
        return DeleteCommandGenerator.get_delete_command(path, "file")


# 便捷函数

def get_platform() -> str:
    """获取当前平台名称"""
    return PlatformInfo.get_system()

def is_windows() -> bool:
    """是否为 Windows"""
    return PlatformInfo.is_windows()

def is_macos() -> bool:
    """是否为 macOS"""
    return PlatformInfo.is_macos()

def is_linux() -> bool:
    """是否为 Linux"""
    return PlatformInfo.is_linux()

def is_admin() -> bool:
    """是否有管理员权限"""
    return PlatformUtils.is_admin()

def create_symlink(source: Union[str, Path], target: Union[str, Path]) -> None:
    """创建软连接"""
    SymlinkManager.create_symlink(source, target)

def remove_symlink(path: Union[str, Path]) -> bool:
    """删除软连接"""
    return SymlinkManager.remove_symlink(path)

def verify_symlink(path: Union[str, Path]) -> bool:
    """验证软连接"""
    return SymlinkManager.verify_symlink(path)

def get_delete_command(path: Union[str, Path], item_type: str = "auto") -> str:
    """获取删除命令"""
    return DeleteCommandGenerator.get_delete_command(path, item_type)
