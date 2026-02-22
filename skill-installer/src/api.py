"""
Kimi 交互式 API

提供纯函数接口，无 input/print，返回结构化数据。
Kimi 可以直接调用这些函数来控制交互流程。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from .config import ConfigManager, ConfigError, ConfigValidationError
from .core import SkillInstaller, InstallOption, InstallResult, UninstallResult
from .path_manager import PathManager, PathManagerError
from .validator import Validator, ValidationResult
from .platform_utils import PlatformInfo, PlatformUtils


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class SetupStatus:
    """配置状态"""
    configured: bool
    manager_dir: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SkillInfo:
    """Skill 信息"""
    name: str
    source_path: str
    is_installed: bool
    symlink_path: Optional[str] = None
    symlink_valid: bool = False
    source_valid: bool = False


@dataclass
class InstallPlan:
    """安装方案（用于展示给用户）"""
    skill_name: str
    source_path: str
    symlink_path: str
    relative_path: str
    option: str  # "full", "light", "clone-only"
    estimated_size: Optional[int] = None
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    # 预检查状态
    pre_check_passed: bool = True
    pre_check_errors: List[str] = field(default_factory=list)


@dataclass
class UninstallPlan:
    """卸载方案（用于展示给用户）"""
    skill_name: str
    source_path: str
    symlink_path: str
    delete_commands: Dict[str, Any] = field(default_factory=dict)
    
    # 预检查状态
    pre_check_passed: bool = True
    pre_check_errors: List[str] = field(default_factory=list)


# ============================================================================
# 配置管理 API
# ============================================================================

def validate_setup() -> SetupStatus:
    """
    检查配置状态
    
    Returns:
        SetupStatus: 配置状态信息
    """
    config = ConfigManager()
    
    if not config.is_configured:
        return SetupStatus(configured=False)
    
    try:
        manager_dir = config.get_manager_dir()
        return SetupStatus(
            configured=True,
            manager_dir=str(manager_dir),
            error=None
        )
    except ConfigError as e:
        return SetupStatus(
            configured=False,
            error=str(e)
        )


def initialize_config(manager_dir: str) -> tuple[bool, str]:
    """
    初始化配置
    
    Args:
        manager_dir: 管理目录的绝对路径
    
    Returns:
        (是否成功, 错误信息)
    """
    config = ConfigManager()
    
    try:
        path = Path(manager_dir).expanduser().resolve()
        config.set_manager_dir(path)
        return True, ""
    except ConfigValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"初始化配置失败: {e}"


def reset_config() -> bool:
    """
    重置配置（删除配置文件）
    
    Returns:
        是否成功
    """
    try:
        config = ConfigManager()
        config.reset()
        return True
    except Exception:
        return False


def get_config_info() -> Dict[str, Any]:
    """
    获取配置信息摘要
    
    Returns:
        配置信息字典
    """
    config = ConfigManager()
    return config.get_config_info()


# ============================================================================
# Skill 查询 API
# ============================================================================

def list_available_skills() -> List[SkillInfo]:
    """
    列出可安装的 skills（管理目录下存在但未安装）
    
    Returns:
        SkillInfo 列表
    """
    config = ConfigManager()
    if not config.is_configured:
        return []
    
    try:
        paths = PathManager(config.get_manager_dir())
        installer = SkillInstaller(config, paths)
        
        available = paths.get_available_skills()
        result = []
        
        for name in available:
            info = paths.get_install_info(name)
            result.append(SkillInfo(
                name=name,
                source_path=str(info['source_path']),
                is_installed=False,
                source_valid=info.get('source_valid', False)
            ))
        
        return result
    except Exception:
        return []


def list_installed_skills() -> List[SkillInfo]:
    """
    列出已安装的 skills
    
    Returns:
        SkillInfo 列表
    """
    config = ConfigManager()
    if not config.is_configured:
        return []
    
    try:
        paths = PathManager(config.get_manager_dir())
        
        installed = paths.get_installed_skills()
        result = []
        
        for name in installed:
            info = paths.get_install_info(name)
            result.append(SkillInfo(
                name=name,
                source_path=str(info['source_path']),
                is_installed=True,
                symlink_path=str(info['symlink_path']),
                symlink_valid=info.get('symlink_valid', False),
                source_valid=info.get('source_valid', False)
            ))
        
        return result
    except Exception:
        return []


def get_skill_info(skill_name: str) -> Optional[SkillInfo]:
    """
    获取 skill 详细信息
    
    Args:
        skill_name: skill 名称
    
    Returns:
        SkillInfo，不存在则返回 None
    """
    config = ConfigManager()
    if not config.is_configured:
        return None
    
    try:
        paths = PathManager(config.get_manager_dir())
        
        source_path = paths.get_skill_source_path(skill_name)
        if not source_path.exists():
            return None
        
        info = paths.get_install_info(skill_name)
        
        return SkillInfo(
            name=skill_name,
            source_path=str(info['source_path']),
            is_installed=info.get('is_installed', False),
            symlink_path=str(info['symlink_path']) if info.get('symlink_path') else None,
            symlink_valid=info.get('symlink_valid', False),
            source_valid=info.get('source_valid', False)
        )
    except Exception:
        return None


def get_skill_detail(skill_name: str) -> Optional[Dict[str, Any]]:
    """
    获取 skill 完整详情（包含 SKILL.md 预览）
    
    Args:
        skill_name: skill 名称
    
    Returns:
        skill 信息字典，不存在则返回 None
    """
    config = ConfigManager()
    if not config.is_configured:
        return None
    
    try:
        paths = PathManager(config.get_manager_dir())
        
        source_path = paths.get_skill_source_path(skill_name)
        if not source_path.exists():
            return None
        
        info = paths.get_install_info(skill_name)
        
        # 读取 SKILL.md 内容摘要
        skill_md = source_path / "SKILL.md"
        skill_md_preview = None
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding='utf-8', errors='ignore')
                # 提取前 800 字符作为摘要
                skill_md_preview = content[:800] + "..." if len(content) > 800 else content
            except Exception:
                pass
        
        return {
            'name': skill_name,
            'source_path': str(info['source_path']),
            'source_valid': info.get('source_valid', False),
            'is_installed': info.get('is_installed', False),
            'symlink_path': str(info['symlink_path']) if info.get('symlink_path') else None,
            'symlink_valid': info.get('symlink_valid', False),
            'symlink_target': info.get('symlink_target'),
            'relative_path': info.get('relative_path'),
            'skill_md_preview': skill_md_preview
        }
    except Exception:
        return None


# ============================================================================
# 安装/卸载方案生成 API（用于展示给用户确认）
# ============================================================================

def generate_install_plan(skill_name: str, option: str = "full") -> Optional[InstallPlan]:
    """
    生成安装方案（不执行安装，仅生成方案供展示）
    
    Args:
        skill_name: skill 名称
        option: 安装选项 ("full", "light", "clone-only")
    
    Returns:
        InstallPlan，如果配置未初始化则返回 None
    """
    config = ConfigManager()
    if not config.is_configured:
        return None
    
    try:
        paths = PathManager(config.get_manager_dir())
        
        source_path = paths.get_skill_source_path(skill_name)
        symlink_path = paths.get_skill_symlink_path(skill_name)
        
        # 预检查
        pre_checks = Validator.run_pre_install_checks(source_path, symlink_path)
        pre_check_passed = not Validator.has_errors(pre_checks)
        pre_check_errors = [e.message for e in Validator.get_errors(pre_checks)]
        
        relative_path = paths.calculate_relative_symlink(skill_name)
        
        return InstallPlan(
            skill_name=skill_name,
            source_path=str(source_path),
            symlink_path=str(symlink_path),
            relative_path=relative_path,
            option=option,
            pre_check_passed=pre_check_passed,
            pre_check_errors=pre_check_errors
        )
    except Exception:
        return None


def generate_uninstall_plan(skill_name: str) -> Optional[UninstallPlan]:
    """
    生成卸载方案（不执行卸载，仅生成方案供展示）
    
    Args:
        skill_name: skill 名称
    
    Returns:
        UninstallPlan，如果配置未初始化则返回 None
    """
    config = ConfigManager()
    if not config.is_configured:
        return None
    
    try:
        paths = PathManager(config.get_manager_dir())
        
        source_path = paths.get_skill_source_path(skill_name)
        symlink_path = paths.get_skill_symlink_path(skill_name)
        
        # 预检查
        pre_checks = Validator.run_pre_uninstall_checks(symlink_path)
        pre_check_passed = not Validator.has_errors(pre_checks)
        pre_check_errors = [e.message for e in Validator.get_errors(pre_checks)]
        
        delete_cmds = paths.get_delete_commands(skill_name)
        
        return UninstallPlan(
            skill_name=skill_name,
            source_path=str(source_path),
            symlink_path=str(symlink_path),
            delete_commands=delete_cmds,
            pre_check_passed=pre_check_passed,
            pre_check_errors=pre_check_errors
        )
    except Exception:
        return None


# ============================================================================
# 安装/卸载执行 API
# ============================================================================

def install_skill(skill_name: str, option: str = "full", 
                  skip_confirm: bool = False) -> InstallResult:
    """
    安装 skill
    
    Args:
        skill_name: skill 名称
        option: 安装选项 ("full", "light", "clone-only")
        skip_confirm: 是否跳过确认（直接执行）
    
    Returns:
        InstallResult
    """
    config = ConfigManager()
    if not config.is_configured:
        return InstallResult(
            success=False,
            skill_name=skill_name,
            symlink_path=Path(),
            message="配置未初始化"
        )
    
    try:
        paths = PathManager(config.get_manager_dir())
        installer = SkillInstaller(config, paths)
        
        # 映射选项
        option_map = {
            "full": InstallOption.FULL,
            "light": InstallOption.LIGHT,
            "clone-only": InstallOption.CLONE_ONLY
        }
        install_opt = option_map.get(option, InstallOption.FULL)
        
        # 执行安装（不通过 UI，直接执行）
        return installer.install(skill_name, install_opt)
    
    except Exception as e:
        return InstallResult(
            success=False,
            skill_name=skill_name,
            symlink_path=Path(),
            message=f"安装失败: {e}"
        )


def uninstall_skill(skill_name: str, skip_confirm: bool = False) -> UninstallResult:
    """
    卸载 skill
    
    Args:
        skill_name: skill 名称
        skip_confirm: 是否跳过确认（直接执行）
    
    Returns:
        UninstallResult
    """
    config = ConfigManager()
    if not config.is_configured:
        return UninstallResult(
            success=False,
            skill_name=skill_name,
            deleted_symlink=Path(),
            message="配置未初始化"
        )
    
    try:
        paths = PathManager(config.get_manager_dir())
        installer = SkillInstaller(config, paths)
        
        # 执行卸载（不通过 UI，直接执行）
        return installer.uninstall(skill_name)
    
    except Exception as e:
        return UninstallResult(
            success=False,
            skill_name=skill_name,
            deleted_symlink=Path(),
            message=f"卸载失败: {e}"
        )


# ============================================================================
# 系统检查 API
# ============================================================================

def check_windows_permission() -> Optional[str]:
    """
    检查 Windows 权限状态
    
    Returns:
        如果是 Windows 且无管理员权限，返回提示信息；否则返回 None
    """
    if not PlatformInfo.is_windows():
        return None
    
    if PlatformUtils.is_admin():
        return None
    
    return (
        "Windows 创建软连接需要管理员权限。\n"
        "请以管理员身份重新运行，或手动创建软连接。"
    )


def get_manual_symlink_command(skill_name: str) -> Optional[Dict[str, str]]:
    """
    获取手动创建软连接的命令
    
    Args:
        skill_name: skill 名称
    
    Returns:
        包含 powershell 和 cmd 命令的字典，如果配置未初始化则返回 None
    """
    config = ConfigManager()
    if not config.is_configured:
        return None
    
    try:
        paths = PathManager(config.get_manager_dir())
        source = paths.get_skill_source_path(skill_name)
        target = paths.get_skill_symlink_path(skill_name)
        
        return {
            'powershell': f'New-Item -ItemType SymbolicLink -Path "{target}" -Target "{source}"',
            'cmd': f'mklink /D "{target}" "{source}"',
            'source': str(source),
            'target': str(target)
        }
    except Exception:
        return None
