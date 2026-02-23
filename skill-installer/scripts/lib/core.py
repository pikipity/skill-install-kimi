"""
核心逻辑 - 安装/卸载/列表等操作

注意：本模块不包含任何 UI 交互代码（input/print）。
交互逻辑已移至 cli_ui.py，Kimi 交互通过 api.py 调用。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from config import ConfigManager, ConfigError
from path_manager import PathManager, PathManagerError
from validator import Validator, ValidationResult, ValidationStatus
from platform_utils import PlatformInfo, PlatformUtils, DeleteCommandGenerator


class InstallOption(Enum):
    """安装选项"""
    FULL = "full"
    LIGHT = "light"
    CLONE_ONLY = "clone-only"


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
    
    注意：本类不包含 UI 交互逻辑，所有交互由调用方处理。
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
    
    def install(self, skill_name: str, option: InstallOption = InstallOption.FULL) -> InstallResult:
        """
        安装 skill（直接执行，无交互确认）
        
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
        
        # 2. 执行安装（创建软连接）
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
        
        # 3. 安装后验证
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
        卸载 skill（直接执行，无交互确认）
        
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
        
        # 2. 执行卸载（删除软连接）
        success = self.paths.remove_skill_symlink(skill_name)
        
        if not success:
            return UninstallResult(
                success=False,
                skill_name=skill_name,
                deleted_symlink=symlink_path,
                message="删除软连接失败"
            )
        
        # 3. 准备删除命令
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
