"""
依赖分析与管理

分析 skill 的依赖情况，提供安装选项
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Dependency:
    """依赖项"""
    name: str
    type: str  # 'python', 'system', 'git', 'data', 'unknown'
    description: str = ""
    required: bool = True
    size: Optional[int] = None  # 字节
    install_command: Optional[str] = None
    
    def format_size(self) -> str:
        """格式化大小显示"""
        if self.size is None:
            return "未知"
        if self.size > 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"
        elif self.size > 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        elif self.size > 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size} B"


@dataclass
class InstallOption:
    """安装选项"""
    id: str  # 'full', 'light', 'clone-only'
    name: str
    description: str
    deps_to_install: List[str] = field(default_factory=list)
    skip_deps: List[str] = field(default_factory=list)
    
    def format_display(self) -> str:
        """格式化显示"""
        lines = [f"  [{self.id.upper()[0]}] {self.name}"]
        if self.description:
            lines.append(f"      {self.description}")
        return "\n".join(lines)


class DependencyAnalyzer:
    """
    依赖分析器
    
    分析 skill 目录，提取依赖信息
    """
    
    def __init__(self, skill_path: Path):
        """
        初始化分析器
        
        Args:
            skill_path: skill 目录路径
        """
        self.skill_path = Path(skill_path)
        self._dependencies: Optional[List[Dependency]] = None
        self._total_size: Optional[int] = None
    
    def analyze(self) -> List[Dependency]:
        """
        分析 skill 依赖
        
        Returns:
            依赖列表
        """
        if self._dependencies is not None:
            return self._dependencies
        
        dependencies = []
        
        # 1. 检查 Python 依赖
        dependencies.extend(self._analyze_python_deps())
        
        # 2. 检查系统依赖
        dependencies.extend(self._analyze_system_deps())
        
        # 3. 检查 Git 依赖
        dependencies.extend(self._analyze_git_deps())
        
        # 4. 检查数据文件
        dependencies.extend(self._analyze_data_deps())
        
        self._dependencies = dependencies
        return dependencies
    
    def _analyze_python_deps(self) -> List[Dependency]:
        """分析 Python 依赖"""
        deps = []
        
        # 检查 requirements.txt
        req_file = self.skill_path / "requirements.txt"
        if req_file.exists():
            size = self._calculate_file_size(req_file)
            deps.append(Dependency(
                name="Python 依赖包",
                type="python",
                description=f"通过 requirements.txt 安装 ({self._count_lines(req_file)} 个包)",
                required=True,
                size=size,
                install_command=f"pip install -r {req_file}"
            ))
        
        # 检查 pyproject.toml
        pyproject = self.skill_path / "pyproject.toml"
        if pyproject.exists():
            deps.append(Dependency(
                name="Python 项目依赖",
                type="python",
                description="通过 pyproject.toml 定义",
                required=True,
                install_command=f"pip install -e {self.skill_path}"
            ))
        
        # 检查 setup.py
        setup_py = self.skill_path / "setup.py"
        if setup_py.exists():
            deps.append(Dependency(
                name="Python 包",
                type="python",
                description="通过 setup.py 安装",
                required=False,
                install_command=f"pip install -e {self.skill_path}"
            ))
        
        return deps
    
    def _analyze_system_deps(self) -> List[Dependency]:
        """分析系统依赖"""
        deps = []
        
        # 检查 DEPS.md 或类似的依赖说明文件
        for filename in ["DEPS.md", "DEPENDENCIES.md", "SYSTEM_DEPS.md"]:
            dep_file = self.skill_path / filename
            if dep_file.exists():
                deps.append(Dependency(
                    name="系统依赖",
                    type="system",
                    description=f"详见 {filename}",
                    required=True
                ))
                break
        
        return deps
    
    def _analyze_git_deps(self) -> List[Dependency]:
        """分析 Git 依赖"""
        deps = []
        
        # 检查 .gitmodules
        gitmodules = self.skill_path / ".gitmodules"
        if gitmodules.exists():
            submodule_count = self._count_lines(gitmodules, pattern="path =")
            deps.append(Dependency(
                name="Git 子模块",
                type="git",
                description=f"{submodule_count} 个子模块",
                required=True,
                install_command="git submodule update --init --recursive"
            ))
        
        # 检查是否为 git 仓库
        git_dir = self.skill_path / ".git"
        if git_dir.exists():
            deps.append(Dependency(
                name="Git 仓库",
                type="git",
                description="可更新到最新版本",
                required=False,
                install_command=f"cd {self.skill_path} && git pull"
            ))
        
        return deps
    
    def _analyze_data_deps(self) -> List[Dependency]:
        """分析数据文件依赖"""
        deps = []
        
        # 检查 data 目录
        data_dir = self.skill_path / "data"
        if data_dir.exists() and data_dir.is_dir():
            size = self._calculate_dir_size(data_dir)
            deps.append(Dependency(
                name="数据文件",
                type="data",
                description="运行时数据目录",
                required=False,
                size=size
            ))
        
        # 检查 models 目录
        models_dir = self.skill_path / "models"
        if models_dir.exists() and models_dir.is_dir():
            size = self._calculate_dir_size(models_dir)
            deps.append(Dependency(
                name="模型文件",
                type="data",
                description="机器学习模型",
                required=False,
                size=size
            ))
        
        return deps
    
    def get_install_options(self) -> List[InstallOption]:
        """
        获取安装选项
        
        Returns:
            安装选项列表
        """
        deps = self.analyze()
        
        # 完全安装：所有依赖
        full_deps = [d.name for d in deps if d.required]
        
        # 轻量安装：仅必需依赖，排除大型数据文件
        light_skip = [d.name for d in deps if d.type == 'data' and not d.required]
        
        return [
            InstallOption(
                id="full",
                name="完全安装",
                description="安装所有依赖（推荐）",
                deps_to_install=full_deps
            ),
            InstallOption(
                id="light",
                name="轻量安装",
                description="仅安装必要依赖，跳过大型数据文件",
                deps_to_install=[d.name for d in deps if d.required and d.type != 'data'],
                skip_deps=light_skip
            ),
            InstallOption(
                id="clone-only",
                name="仅克隆",
                description="仅创建软连接，不安装任何依赖",
                deps_to_install=[],
                skip_deps=[d.name for d in deps]
            )
        ]
    
    def calculate_total_size(self) -> int:
        """
        计算 skill 总大小（字节）
        
        Returns:
            总大小
        """
        if self._total_size is not None:
            return self._total_size
        
        self._total_size = self._calculate_dir_size(self.skill_path)
        return self._total_size
    
    def format_total_size(self) -> str:
        """格式化总大小显示"""
        size = self.calculate_total_size()
        if size > 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
        elif size > 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size} B"
    
    def _calculate_dir_size(self, path: Path) -> int:
        """计算目录大小"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir() and not entry.is_symlink():
                    total += self._calculate_dir_size(Path(entry.path))
        except (PermissionError, OSError):
            pass
        return total
    
    def _calculate_file_size(self, path: Path) -> int:
        """计算文件大小"""
        try:
            return path.stat().st_size
        except (PermissionError, OSError):
            return 0
    
    def _count_lines(self, path: Path, pattern: Optional[str] = None) -> int:
        """计算文件行数，或匹配某模式的行数"""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            if pattern:
                return sum(1 for line in content.split('\n') if pattern in line)
            return len(content.split('\n'))
        except Exception:
            return 0


# 便捷函数

def analyze_skill_dependencies(skill_path: Path) -> DependencyAnalyzer:
    """创建依赖分析器"""
    return DependencyAnalyzer(skill_path)
