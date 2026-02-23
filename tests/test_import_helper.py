"""
测试导入辅助模块 - 脚本架构版
支持 scripts/lib/ 目录的模块导入
"""

import sys
from pathlib import Path


def setup_scripts_lib_import():
    """
    设置 scripts/lib 目录到 sys.path
    
    在测试文件开头调用：
        import test_import_helper
        from config import ConfigManager  # 直接导入 lib 下的模块
    """
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # scripts/lib 目录路径
    scripts_lib_dir = project_root / "skill-installer" / "scripts" / "lib"
    
    # 添加到 sys.path（如果不存在）
    if str(scripts_lib_dir) not in sys.path:
        sys.path.insert(0, str(scripts_lib_dir))


# 自动执行（当本模块被导入时）
setup_scripts_lib_import()
