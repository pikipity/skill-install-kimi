"""
路径管理器 - 计算相对路径，创建/删除软连接
"""

from pathlib import Path
from typing import Optional, Union, List

from platform_utils import (
    PlatformInfo, 
    PlatformUtils, 
    SymlinkManager,
    DeleteCommandGenerator
)


class PathManagerError(Exception):
    """路径管理错误"""
    pass


class PathManager:
    """
    路径管理器
    
    负责：
    - 计算 skill 的源路径和目标软连接路径
    - 创建和管理软连接
    - 检查 skill 是否已安装
    """
    
    def __init__(self, manager_dir: Union[str, Path]):
        """
        初始化路径管理器
        
        Args:
            manager_dir: 管理目录（所有 skill 仓库的父目录）
        """
        self.manager_dir = Path(manager_dir).resolve()
        self.kimi_skills_dir = PlatformInfo.get_skills_dir()
        
        # 确保 Kimi skills 目录存在
        PlatformUtils.ensure_dir(self.kimi_skills_dir)
    
    def find_skill_source(self, skill_name: str) -> Optional[Path]:
        """
        在管理目录下递归查找 skill 源目录
        支持扁平结构和嵌套结构
        
        Args:
            skill_name: skill 名称
            
        Returns:
            skill 源路径，未找到返回 None
        """
        # 先尝试扁平结构
        flat_path = self.manager_dir / skill_name
        if (flat_path / "SKILL.md").exists():
            return flat_path
        
        # 递归查找嵌套结构
        try:
            for item in self.manager_dir.rglob("*"):
                if item.is_dir() and item.name == skill_name:
                    if (item / "SKILL.md").exists():
                        return item
        except Exception:
            pass
        
        return None
    
    def get_skill_source_path(self, skill_name: str) -> Path:
        """
        获取 skill 的源路径（原始仓库位置）
        
        Args:
            skill_name: skill 名称
        
        Returns:
            源目录路径
        """
        return self.manager_dir / skill_name
    
    def get_skill_symlink_path(self, skill_name: str) -> Path:
        """
        获取 skill 的软连接路径（~/.kimi/skills/{skill_name}）
        
        Args:
            skill_name: skill 名称
        
        Returns:
            软连接路径
        """
        return self.kimi_skills_dir / skill_name
    
    def calculate_relative_symlink(self, skill_name: str) -> str:
        """
        计算从软连接位置到源目录的相对路径
        
        例如：
        - 源：/Users/{username}/projects/skill-install-project/skill-installer
        - 软连接位置：~/.kimi/skills/skill-installer
        - 结果：../../projects/skill-install-project/skill-installer
        
        Args:
            skill_name: skill 名称
        
        Returns:
            相对路径（使用 / 分隔符）
        """
        source = self.get_skill_source_path(skill_name)
        symlink = self.get_skill_symlink_path(skill_name)
        
        return PlatformUtils.calculate_relative_path(source, symlink)
    
    def is_skill_installed(self, skill_name: str) -> bool:
        """
        检查 skill 是否已安装（软连接/目录联接是否存在且有效）
        
        Args:
            skill_name: skill 名称
        
        Returns:
            是否已安装
        """
        symlink_path = self.get_skill_symlink_path(skill_name)
        
        if not symlink_path.exists():
            return False
        
        # 检查是否为链接（软连接或目录联接）
        try:
            target = symlink_path.resolve()
            # 如果解析后的路径与原始路径不同，说明是链接
            if target == symlink_path:
                return False
            
            # 验证目标是有效 skill 目录（有 SKILL.md 即可，不检查位置）
            return (target / "SKILL.md").exists()
        except Exception:
            return False
    
    def get_installed_skills(self) -> List[str]:
        """
        获取已安装的 skill 列表
        
        Returns:
            skill 名称列表
        """
        installed = []
        
        if not self.kimi_skills_dir.exists():
            return installed
        
        for item in self.kimi_skills_dir.iterdir():
            try:
                # 尝试解析（软连接或目录联接都能解析）
                target = item.resolve()
                
                # 是链接且指向有效 skill 目录（有 SKILL.md）
                if target != item and (target / "SKILL.md").exists():
                    installed.append(item.name)
                    
            except Exception:
                pass
        
        return installed
    
    def get_available_skills(self) -> List[str]:
        """
        获取可安装的 skill 列表（管理目录下存在但未安装的）
        
        Returns:
            skill 名称列表
        """
        available = []
        installed = set(self.get_installed_skills())
        
        if not self.manager_dir.exists():
            return available
        
        for item in self.manager_dir.iterdir():
            if item.is_dir() and item.name not in installed:
                # 检查是否为有效的 skill（包含 SKILL.md）
                if (item / "SKILL.md").exists():
                    available.append(item.name)
        
        return sorted(available)
    
    def validate_skill_source(self, skill_name: str) -> tuple[bool, str]:
        """
        验证 skill 源目录是否有效
        
        Args:
            skill_name: skill 名称
        
        Returns:
            (是否有效, 错误信息)
        """
        source_path = self.get_skill_source_path(skill_name)
        
        if not source_path.exists():
            return False, f"Skill 源目录不存在: {source_path}"
        
        if not source_path.is_dir():
            return False, f"Skill 源路径不是目录: {source_path}"
        
        # 检查是否包含 SKILL.md
        skill_md = source_path / "SKILL.md"
        if not skill_md.exists():
            return False, f"Skill 源目录缺少 SKILL.md: {source_path}"
        
        return True, ""
    
    def create_skill_symlink(self, skill_name: str, source_path: Path = None) -> None:
        """
        创建 skill 的软连接
        
        Args:
            skill_name: skill 名称
            source_path: 可选，指定源路径（支持嵌套结构）
        
        Raises:
            PathManagerError: 创建失败
        """
        # 【关键】使用传入的源路径或查找嵌套结构
        if source_path is None:
            source_path = self.find_skill_source(skill_name)
        if source_path is None:
            source_path = self.get_skill_source_path(skill_name)
        
        target = self.get_skill_symlink_path(skill_name)
        
        # 验证源存在
        if not source_path.exists():
            raise PathManagerError(f"Skill 源目录不存在: {source_path}")
        if not (source_path / "SKILL.md").exists():
            raise PathManagerError(f"无效的 skill 目录（缺少 SKILL.md）: {source_path}")
        
        # 检查是否已安装
        if self.is_skill_installed(skill_name):
            raise PathManagerError(f"Skill '{skill_name}' 已安装")
        
        try:
            SymlinkManager.create_symlink(source, target)
        except PermissionError as e:
            raise PathManagerError(f"权限不足: {e}")
        except Exception as e:
            raise PathManagerError(f"创建软连接失败: {e}")
    
    def remove_skill_symlink(self, skill_name: str) -> bool:
        """
        删除 skill 的软连接
        
        Args:
            skill_name: skill 名称
        
        Returns:
            是否成功删除
        """
        target = self.get_skill_symlink_path(skill_name)
        
        if not target.exists() and not target.is_symlink():
            return False
        
        return SymlinkManager.remove_symlink(target)
    
    def verify_skill_symlink(self, skill_name: str) -> bool:
        """
        验证 skill 的软连接是否有效
        
        Args:
            skill_name: skill 名称
        
        Returns:
            软连接是否有效
        """
        symlink_path = self.get_skill_symlink_path(skill_name)
        return SymlinkManager.verify_symlink(symlink_path)
    
    def get_symlink_target(self, skill_name: str) -> Optional[Path]:
        """
        获取软连接指向的目标
        
        Args:
            skill_name: skill 名称
        
        Returns:
            目标路径，如果不存在则返回 None
        """
        symlink_path = self.get_skill_symlink_path(skill_name)
        return SymlinkManager.read_symlink(symlink_path)
    
    def get_install_info(self, skill_name: str) -> dict:
        """
        获取 skill 安装信息
        
        Args:
            skill_name: skill 名称
        
        Returns:
            包含安装信息的字典
        """
        source = self.get_skill_source_path(skill_name)
        symlink = self.get_skill_symlink_path(skill_name)
        relative_path = self.calculate_relative_symlink(skill_name)
        
        info = {
            'name': skill_name,
            'source_path': source,
            'symlink_path': symlink,
            'relative_path': relative_path,
            'is_installed': self.is_skill_installed(skill_name),
            'source_exists': source.exists(),
            'source_valid': False,
        }
        
        if source.exists():
            valid, error = self.validate_skill_source(skill_name)
            info['source_valid'] = valid
            if not valid:
                info['source_error'] = error
        
        if info['is_installed']:
            info['symlink_valid'] = self.verify_skill_symlink(skill_name)
            target = self.get_symlink_target(skill_name)
            if target:
                info['symlink_target'] = target
        
        return info
    
    def get_delete_commands(self, skill_name: str) -> dict:
        """
        获取删除 skill 相关文件的命令（用于卸载时显示）
        
        Args:
            skill_name: skill 名称
        
        Returns:
            包含各平台删除命令的字典
        """
        source = self.get_skill_source_path(skill_name)
        symlink = self.get_skill_symlink_path(skill_name)
        
        return {
            'symlink': {
                'path': symlink,
                'command': DeleteCommandGenerator.get_rmdir_command(symlink),
            },
            'source': {
                'path': source,
                'command': DeleteCommandGenerator.get_rmdir_command(source),
            }
        }
