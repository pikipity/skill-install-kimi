"""
测试导入辅助模块 - 方案 D
动态创建 skill_installer 包，无需符号链接
"""

import sys
import types
import importlib.util
from pathlib import Path


def setup_skill_installer_import():
    """
    设置 skill_installer 包的导入路径
    
    在测试文件开头调用：
        import test_import_helper
        from skill_installer.src.config import ConfigManager
    """
    # 如果已经设置过，直接返回
    if "skill_installer" in sys.modules:
        return
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # skill-installer 目录路径
    skill_installer_dir = project_root / "skill-installer"
    src_dir = skill_installer_dir / "src"
    
    # 创建 skill_installer 包
    skill_installer_pkg = types.ModuleType("skill_installer")
    skill_installer_pkg.__path__ = [str(skill_installer_dir)]
    skill_installer_pkg.__package__ = "skill_installer"
    sys.modules["skill_installer"] = skill_installer_pkg
    
    # 创建 skill_installer.src 包
    skill_installer_src_pkg = types.ModuleType("skill_installer.src")
    skill_installer_src_pkg.__path__ = [str(src_dir)]
    skill_installer_src_pkg.__package__ = "skill_installer.src"
    sys.modules["skill_installer.src"] = skill_installer_src_pkg
    
    # 加载 src/__init__.py（如果存在）
    init_file = src_dir / "__init__.py"
    if init_file.exists():
        spec = importlib.util.spec_from_file_location(
            "skill_installer.src", init_file
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["skill_installer.src"] = module
            spec.loader.exec_module(module)
    
    # 添加 src 到 sys.path（用于直接从 src 导入，方便测试内部模块）
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


# 自动执行（当本模块被导入时）
setup_skill_installer_import()
