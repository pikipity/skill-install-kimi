#!/usr/bin/env python3
"""
检查 skill-installer 配置状态

用法:
    python check_config.py

输出(JSON):
    {
        "configured": bool,
        "manager_dir": str | null,
        "platform": "macos" | "linux" | "windows",
        "is_admin": bool,
        "error": str | null
    }
"""

import json
import sys
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import ConfigManager
from platform_utils import PlatformInfo, PlatformUtils


def main():
    """主函数"""
    # 获取配置管理器
    skill_dir = Path(__file__).parent.parent
    config_manager = ConfigManager(skill_dir)
    
    # 获取平台信息
    platform_name = PlatformInfo.get_system()
    is_admin = PlatformUtils.is_admin()
    
    # 检查配置状态
    result = {
        "configured": config_manager.is_configured,
        "manager_dir": str(config_manager.get_manager_dir()) if config_manager.is_configured else None,
        "platform": platform_name,
        "is_admin": is_admin,
        "error": None
    }
    
    # 如果已配置但无效，添加错误信息
    if config_manager.is_configured:
        try:
            config = config_manager.load()
            if not config:
                result["configured"] = False
                result["error"] = "配置文件无效"
        except Exception as e:
            result["configured"] = False
            result["error"] = str(e)
    else:
        result["error"] = "配置文件不存在，需要初始化"
    
    # 输出 JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 返回退出码
    return 0 if result["configured"] else 1


if __name__ == "__main__":
    sys.exit(main())
