"""
安装验证器 - 安装前后的各种验证
"""

from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum

from platform_utils import PlatformInfo


class ValidationStatus(Enum):
    """验证状态"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """验证结果"""
    status: ValidationStatus
    message: str
    suggestion: Optional[str] = None
    
    @property
    def is_ok(self) -> bool:
        return self.status == ValidationStatus.OK
    
    @property
    def is_warning(self) -> bool:
        return self.status == ValidationStatus.WARNING
    
    @property
    def is_error(self) -> bool:
        return self.status == ValidationStatus.ERROR


class Validator:
    """安装验证器"""
    
    @staticmethod
    def validate_source_exists(skill_path: Path) -> ValidationResult:
        """
        验证 skill 源目录是否存在
        
        Args:
            skill_path: skill 源目录路径
        
        Returns:
            验证结果
        """
        if not skill_path.exists():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Skill 源目录不存在: {skill_path}",
                suggestion="请检查 skill 名称是否正确，或先克隆仓库"
            )
        
        if not skill_path.is_dir():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Skill 源路径不是目录: {skill_path}",
                suggestion="请确认路径指向的是一个目录"
            )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message=f"Skill 源目录存在: {skill_path}"
        )
    
    @staticmethod
    def validate_skill_structure(skill_path: Path) -> ValidationResult:
        """
        验证 skill 目录结构是否有效（包含 SKILL.md）
        
        Args:
            skill_path: skill 源目录路径
        
        Returns:
            验证结果
        """
        skill_md = skill_path / "SKILL.md"
        
        if not skill_md.exists():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"缺少 SKILL.md 文件: {skill_path / 'SKILL.md'}",
                suggestion="有效的 skill 必须包含 SKILL.md 文件"
            )
        
        if not skill_md.is_file():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"SKILL.md 不是文件: {skill_md}",
                suggestion="请检查 SKILL.md 是否为普通文件"
            )
        
        # 检查 SKILL.md 是否可读
        try:
            content = skill_md.read_text(encoding='utf-8')
            if not content.strip():
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message=f"SKILL.md 文件为空: {skill_md}",
                    suggestion="建议填写 skill 的使用说明"
                )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"无法读取 SKILL.md: {e}",
                suggestion="请检查文件权限"
            )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message=f"SKILL.md 验证通过"
        )
    
    @staticmethod
    def validate_not_already_installed(symlink_path: Path) -> ValidationResult:
        """
        验证 skill 是否已安装
        
        Args:
            symlink_path: 软连接路径
        
        Returns:
            验证结果
        """
        if symlink_path.exists() or symlink_path.is_symlink():
            if symlink_path.is_symlink():
                try:
                    target = symlink_path.resolve()
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message=f"Skill 已安装，指向: {target}",
                        suggestion="如需重新安装，请先卸载"
                    )
                except Exception:
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message=f"Skill 软连接存在但可能已损坏: {symlink_path}",
                        suggestion="建议删除后重新安装"
                    )
            else:
                return ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"目标位置存在非软连接文件/目录: {symlink_path}",
                    suggestion="请手动检查并删除该路径"
                )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message="目标位置可用"
        )
    
    @staticmethod
    def validate_symlink_readable(symlink_path: Path) -> ValidationResult:
        """
        验证软连接是否可读（指向的目标存在）
        
        Args:
            symlink_path: 软连接路径
        
        Returns:
            验证结果
        """
        if not symlink_path.is_symlink():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"不是软连接: {symlink_path}",
                suggestion="安装可能未成功"
            )
        
        try:
            target = symlink_path.resolve()
            if target.exists():
                return ValidationResult(
                    status=ValidationStatus.OK,
                    message=f"软连接可读，指向: {target}"
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"软连接指向的目标不存在: {target}",
                    suggestion="原始仓库可能已被移动或删除"
                )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"无法解析软连接: {e}",
                suggestion="软连接可能已损坏"
            )
    
    @staticmethod
    def validate_skill_detected_by_kimi(skill_name: str) -> ValidationResult:
        """
        验证 Kimi CLI 是否能检测到该 skill
        
        注意：这是一个启发式验证，实际检测需要运行 Kimi CLI
        
        Args:
            skill_name: skill 名称
        
        Returns:
            验证结果
        """
        skills_dir = PlatformInfo.get_skills_dir()
        skill_link = skills_dir / skill_name
        
        if not skill_link.exists() and not skill_link.is_symlink():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Skill 软连接不存在: {skill_link}",
                suggestion="安装可能未完成"
            )
        
        if skill_link.is_symlink():
            try:
                target = skill_link.resolve()
                skill_md = target / "SKILL.md"
                if skill_md.exists():
                    return ValidationResult(
                        status=ValidationStatus.OK,
                        message=f"Skill 结构正确，Kimi CLI 应该可以检测到"
                    )
                else:
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message=f"Skill 软连接存在，但目标缺少 SKILL.md",
                        suggestion="Kimi CLI 可能无法识别该 skill"
                    )
            except Exception as e:
                return ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"无法验证 skill: {e}",
                    suggestion="请检查软连接是否有效"
                )
        
        return ValidationResult(
            status=ValidationStatus.WARNING,
            message=f"目标位置存在非软连接: {skill_link}",
            suggestion="可能影响 Kimi CLI 的 skill 检测"
        )
    
    @staticmethod
    def validate_uninstall_target(symlink_path: Path) -> ValidationResult:
        """
        验证卸载目标
        
        Args:
            symlink_path: 软连接路径
        
        Returns:
            验证结果
        """
        if not symlink_path.exists() and not symlink_path.is_symlink():
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Skill 未安装（软连接不存在）: {symlink_path}",
                suggestion="无需卸载"
            )
        
        if not symlink_path.is_symlink():
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"目标位置不是软连接: {symlink_path}",
                suggestion="将删除该路径，请确认这不是重要文件"
            )
        
        return ValidationResult(
            status=ValidationStatus.OK,
            message="可以安全删除软连接"
        )
    
    @staticmethod
    def run_pre_install_checks(skill_path: Path, symlink_path: Path) -> List[ValidationResult]:
        """
        运行安装前检查
        
        Args:
            skill_path: skill 源目录
            symlink_path: 软连接目标路径
        
        Returns:
            验证结果列表
        """
        results = []
        
        # 1. 检查源目录
        results.append(Validator.validate_source_exists(skill_path))
        
        # 2. 检查结构
        if results[0].is_ok:
            results.append(Validator.validate_skill_structure(skill_path))
        
        # 3. 检查是否已安装
        results.append(Validator.validate_not_already_installed(symlink_path))
        
        return results
    
    @staticmethod
    def run_post_install_checks(symlink_path: Path, skill_name: str) -> List[ValidationResult]:
        """
        运行安装后检查
        
        Args:
            symlink_path: 软连接路径
            skill_name: skill 名称
        
        Returns:
            验证结果列表
        """
        results = []
        
        # 1. 检查软连接可读
        results.append(Validator.validate_symlink_readable(symlink_path))
        
        # 2. 检查 Kimi CLI 可检测
        if results[0].is_ok:
            results.append(Validator.validate_skill_detected_by_kimi(skill_name))
        
        return results
    
    @staticmethod
    def run_pre_uninstall_checks(symlink_path: Path) -> List[ValidationResult]:
        """
        运行卸载前检查
        
        Args:
            symlink_path: 软连接路径
        
        Returns:
            验证结果列表
        """
        results = []
        
        results.append(Validator.validate_uninstall_target(symlink_path))
        
        return results
    
    @staticmethod
    def has_errors(results: List[ValidationResult]) -> bool:
        """检查结果列表中是否有错误"""
        return any(r.is_error for r in results)
    
    @staticmethod
    def has_warnings(results: List[ValidationResult]) -> bool:
        """检查结果列表中是否有警告"""
        return any(r.is_warning for r in results)
    
    @staticmethod
    def get_errors(results: List[ValidationResult]) -> List[ValidationResult]:
        """获取所有错误结果"""
        return [r for r in results if r.is_error]
    
    @staticmethod
    def get_warnings(results: List[ValidationResult]) -> List[ValidationResult]:
        """获取所有警告结果"""
        return [r for r in results if r.is_warning]
