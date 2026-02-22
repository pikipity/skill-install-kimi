"""
核心逻辑 - 安装/卸载/列表等操作
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from enum import Enum

from .config import ConfigManager, ConfigError
from .path_manager import PathManager, PathManagerError
from .validator import Validator, ValidationResult, ValidationStatus
from .platform_utils import PlatformInfo, DeleteCommandGenerator


class InstallOption(Enum):
    """安装选项"""
    FULL = "full"
    LIGHT = "light"
    CLONE_ONLY = "clone-only"


@dataclass
class InstallPlan:
    """安装方案"""
    skill_name: str
    source_path: Path
    symlink_path: Path
    relative_path: str
    option: InstallOption
    estimated_size: Optional[int] = None
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    def format_display(self) -> str:
        """格式化显示安装方案"""
        lines = [
            "",
            "═══════════════════════════════════════════════════════",
            f"📦 安装方案：{self.skill_name}",
            "═══════════════════════════════════════════════════════",
            "",
            "【安装位置】",
            f"  原始仓库：{self.source_path}",
            f"  软连接：  {self.symlink_path}",
            f"         → {self.relative_path}",
        ]
        
        if self.estimated_size:
            size_mb = self.estimated_size / (1024 * 1024)
            lines.extend([
                "",
                f"【预估大小】{size_mb:.1f} MB"
            ])
        
        if self.dependencies:
            lines.extend([
                "",
                "【依赖清单】",
            ])
            for i, dep in enumerate(self.dependencies, 1):
                lines.append(f"  {i}. {dep.get('name', '未知')}")
                if 'description' in dep:
                    lines.append(f"     作用：{dep['description']}")
                if 'size' in dep:
                    size_str = f"{dep['size'] / (1024*1024):.1f} MB" if dep['size'] > 1024*1024 else f"{dep['size'] / 1024:.1f} KB"
                    lines.append(f"     大小：{size_str}")
        
        lines.extend([
            "",
            "【选项】",
            "  [A] 完全安装",
            "  [B] 轻量安装",
            "  [C] 仅克隆",
            "  [D] 取消安装",
            "",
        ])
        
        return "\n".join(lines)


@dataclass
class UninstallPlan:
    """卸载方案"""
    skill_name: str
    source_path: Path
    symlink_path: Path
    delete_commands: Dict[str, Any]
    
    def format_display(self) -> str:
        """格式化显示卸载方案"""
        platform = PlatformInfo.get_system()
        
        lines = [
            "",
            "═══════════════════════════════════════════════════════",
            f"🗑️ 卸载方案：{self.skill_name}",
            "═══════════════════════════════════════════════════════",
            "",
            "【将执行的操作】",
            f"  ✅ 删除软连接：{self.symlink_path}",
            "",
            "【将保留的内容】（手动删除命令）",
            "",
            f"  1. Skill 原始仓库",
            f"     位置：{self.source_path}",
            f"     删除命令：",
        ]
        
        # 添加各平台的删除命令
        if 'source' in self.delete_commands:
            cmd = self.delete_commands['source']['command']
            lines.append(f"       {platform}: {cmd}")
        
        lines.extend([
            "",
            "═══════════════════════════════════════════════════════",
            "",
            "是否确认删除软连接？ [Y/n]：",
        ])
        
        return "\n".join(lines)


@dataclass
class InstallResult:
    """安装结果"""
    success: bool
    skill_name: str
    symlink_path: Path
    message: str
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    def format_display(self) -> str:
        """格式化显示结果"""
        if self.success:
            return f"\n✅ 安装成功：{self.skill_name}\n   软连接：{self.symlink_path}"
        else:
            return f"\n❌ 安装失败：{self.message}"


@dataclass
class UninstallResult:
    """卸载结果"""
    success: bool
    skill_name: str
    deleted_symlink: Path
    preserved_paths: List[Path] = field(default_factory=list)
    delete_commands: Dict[str, str] = field(default_factory=dict)
    message: str = ""
    
    def format_display(self) -> str:
        """格式化显示结果"""
        lines = [""]
        
        if self.success:
            lines.append(f"✅ 已删除软连接：{self.deleted_symlink}")
        else:
            lines.append(f"❌ 卸载失败：{self.message}")
            return "\n".join(lines)
        
        if self.preserved_paths:
            lines.extend([
                "",
                "以下路径已保留（如需删除，请手动执行）：",
            ])
            for path in self.preserved_paths:
                lines.append(f"  - {path}")
        
        if self.delete_commands:
            lines.extend([
                "",
                "删除命令：",
            ])
            for name, cmd in self.delete_commands.items():
                lines.append(f"  {name}: {cmd}")
        
        return "\n".join(lines)


class SkillInstaller:
    """
    Skill 安装器
    
    核心功能：
    - 安装 skill（创建软连接）
    - 卸载 skill（删除软连接，保留源仓库）
    - 列出已安装/可安装的 skill
    """
    
    def __init__(self, config: ConfigManager, paths: PathManager):
        """
        初始化安装器
        
        Args:
            config: 配置管理器
            paths: 路径管理器
        """
        self.config = config
        self.paths = paths
        self.ui: Optional[Any] = None  # 用户交互接口，由调用方设置
    
    def set_ui(self, ui: Any) -> None:
        """设置用户交互接口"""
        self.ui = ui
    
    def _confirm(self, prompt: str, default: bool = True) -> bool:
        """确认操作"""
        if self.ui:
            return self.ui.confirm(prompt, default=default)
        # 无 UI 时默认允许
        return default
    
    def install(self, skill_name: str, option: InstallOption = InstallOption.FULL) -> InstallResult:
        """
        安装 skill
        
        Args:
            skill_name: skill 名称
            option: 安装选项
        
        Returns:
            安装结果
        """
        source_path = self.paths.get_skill_source_path(skill_name)
        symlink_path = self.paths.get_skill_symlink_path(skill_name)
        
        # 1. 安装前检查
        pre_checks = Validator.run_pre_install_checks(source_path, symlink_path)
        
        if Validator.has_errors(pre_checks):
            errors = Validator.get_errors(pre_checks)
            return InstallResult(
                success=False,
                skill_name=skill_name,
                symlink_path=symlink_path,
                message=f"安装前检查失败：{errors[0].message}",
                validation_results=pre_checks
            )
        
        # 2. 显示安装方案并确认
        if self.ui:
            relative_path = self.paths.calculate_relative_symlink(skill_name)
            
            plan = InstallPlan(
                skill_name=skill_name,
                source_path=source_path,
                symlink_path=symlink_path,
                relative_path=relative_path,
                option=option
            )
            
            self.ui.print(plan.format_display())
            
            choice = self.ui.prompt("请选择", choices=["A", "B", "C", "D"])
            
            if choice == "D":
                return InstallResult(
                    success=False,
                    skill_name=skill_name,
                    symlink_path=symlink_path,
                    message="用户取消安装"
                )
            
            option_map = {"A": InstallOption.FULL, "B": InstallOption.LIGHT, "C": InstallOption.CLONE_ONLY}
            option = option_map.get(choice, InstallOption.FULL)
            
            # 二次确认
            if not self._confirm("是否确认执行安装？", default=True):
                return InstallResult(
                    success=False,
                    skill_name=skill_name,
                    symlink_path=symlink_path,
                    message="用户取消安装"
                )
        
        # 3. 执行安装（创建软连接）
        try:
            self.paths.create_skill_symlink(skill_name)
        except PathManagerError as e:
            return InstallResult(
                success=False,
                skill_name=skill_name,
                symlink_path=symlink_path,
                message=f"创建软连接失败：{e}"
            )
        except PermissionError as e:
            return InstallResult(
                success=False,
                skill_name=skill_name,
                symlink_path=symlink_path,
                message=f"权限不足：{e}"
            )
        
        # 4. 安装后验证
        post_checks = Validator.run_post_install_checks(symlink_path, skill_name)
        
        if Validator.has_errors(post_checks):
            errors = Validator.get_errors(post_checks)
            # 尝试回滚
            self.paths.remove_skill_symlink(skill_name)
            return InstallResult(
                success=False,
                skill_name=skill_name,
                symlink_path=symlink_path,
                message=f"安装验证失败，已回滚：{errors[0].message}",
                validation_results=post_checks
            )
        
        return InstallResult(
            success=True,
            skill_name=skill_name,
            symlink_path=symlink_path,
            message="安装成功",
            validation_results=post_checks
        )
    
    def uninstall(self, skill_name: str) -> UninstallResult:
        """
        卸载 skill
        
        Args:
            skill_name: skill 名称
        
        Returns:
            卸载结果
        """
        source_path = self.paths.get_skill_source_path(skill_name)
        symlink_path = self.paths.get_skill_symlink_path(skill_name)
        
        # 1. 卸载前检查
        pre_checks = Validator.run_pre_uninstall_checks(symlink_path)
        
        if Validator.has_errors(pre_checks):
            errors = Validator.get_errors(pre_checks)
            return UninstallResult(
                success=False,
                skill_name=skill_name,
                deleted_symlink=symlink_path,
                message=errors[0].message
            )
        
        # 2. 显示卸载方案并确认
        if self.ui:
            delete_cmds = self.paths.get_delete_commands(skill_name)
            
            plan = UninstallPlan(
                skill_name=skill_name,
                source_path=source_path,
                symlink_path=symlink_path,
                delete_commands=delete_cmds
            )
            
            self.ui.print(plan.format_display())
            
            if not self._confirm("是否确认删除软连接？", default=True):
                return UninstallResult(
                    success=False,
                    skill_name=skill_name,
                    deleted_symlink=symlink_path,
                    message="用户取消卸载"
                )
        
        # 3. 执行卸载（删除软连接）
        success = self.paths.remove_skill_symlink(skill_name)
        
        if not success:
            return UninstallResult(
                success=False,
                skill_name=skill_name,
                deleted_symlink=symlink_path,
                message="删除软连接失败"
            )
        
        # 4. 准备删除命令
        delete_cmds = self.paths.get_delete_commands(skill_name)
        preserved_paths = [source_path] if source_path.exists() else []
        
        return UninstallResult(
            success=True,
            skill_name=skill_name,
            deleted_symlink=symlink_path,
            preserved_paths=preserved_paths,
            delete_commands={
                'source': delete_cmds.get('source', {}).get('command', '')
            },
            message="卸载成功"
        )
    
    def list_installed(self) -> List[Dict[str, Any]]:
        """
        列出已安装的 skill
        
        Returns:
            skill 信息列表
        """
        installed = self.paths.get_installed_skills()
        result = []
        
        for name in installed:
            info = self.paths.get_install_info(name)
            result.append({
                'name': name,
                'source_path': str(info['source_path']),
                'symlink_path': str(info['symlink_path']),
                'symlink_valid': info.get('symlink_valid', False),
            })
        
        return result
    
    def list_available(self) -> List[Dict[str, Any]]:
        """
        列出可安装的 skill（管理目录下存在但未安装）
        
        Returns:
            skill 信息列表
        """
        available = self.paths.get_available_skills()
        result = []
        
        for name in available:
            info = self.paths.get_install_info(name)
            result.append({
                'name': name,
                'source_path': str(info['source_path']),
                'source_valid': info.get('source_valid', False),
            })
        
        return result
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        获取 skill 详细信息
        
        Args:
            skill_name: skill 名称
        
        Returns:
            skill 信息字典，不存在则返回 None
        """
        source_path = self.paths.get_skill_source_path(skill_name)
        
        if not source_path.exists():
            return None
        
        info = self.paths.get_install_info(skill_name)
        
        # 读取 SKILL.md 内容摘要
        skill_md = source_path / "SKILL.md"
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding='utf-8', errors='ignore')
                # 提取前 500 字符作为摘要
                info['skill_md_preview'] = content[:500] + "..." if len(content) > 500 else content
            except Exception:
                info['skill_md_preview'] = None
        
        return info
    
    def check_windows_permission(self) -> Optional[str]:
        """
        检查 Windows 权限（如果需要）
        
        Returns:
            如果是 Windows 且无管理员权限，返回提示信息；否则返回 None
        """
        if not PlatformInfo.is_windows():
            return None
        
        if PlatformInfo.is_admin():
            return None
        
        return (
            "\n⚠️ Windows 权限提示\n"
            "═══════════════════════════════════════════════════════\n"
            "\n"
            "检测到 Windows 系统，创建软连接需要管理员权限。\n"
            "\n"
            "【选项】\n"
            "  [A] 退出，以管理员身份重新运行\n"
            "  [B] 获取手动创建软连接的指令\n"
            "  [C] 使用目录拷贝代替软连接（不推荐，占用双倍空间）\n"
            "  [D] 取消\n"
        )
