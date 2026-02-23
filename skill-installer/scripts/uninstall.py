#!/usr/bin/env python3
"""
执行 skill 卸载

用法:
    python uninstall.py --skill <name>

参数:
    --skill: skill 名称

输出(JSON):
    成功:
    {
        "success": true,
        "skill_name": "skill-pdf",
        "symlink_path": "C:\\Users\\...\\.kimi\\skills\\skill-pdf",
        "message": "卸载成功（仅删除软连接，原始仓库已保留）"
    }
    
    失败:
    {
        "success": false,
        "skill_name": "skill-pdf",
        "error": "错误信息"
    }
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import ConfigManager
from core import SkillInstaller


def main():
    parser = argparse.ArgumentParser(description='卸载 skill')
    parser.add_argument('--skill', required=True, help='skill 名称')
    args = parser.parse_args()
    
    skill_dir = Path(__file__).parent.parent
    config = ConfigManager(skill_dir)
    
    if not config.is_configured:
        print(json.dumps({
            "success": False,
            "skill_name": args.skill,
            "error": "未配置"
        }, indent=2, ensure_ascii=False))
        return 1
    
    try:
        from path_manager import PathManager
        
        paths = PathManager(config.get_manager_dir())
        installer = SkillInstaller(config, paths)
        
        # 执行卸载
        result = installer.uninstall(args.skill)
        
        output = {
            "success": result.success,
            "skill_name": args.skill,
            "symlink_path": str(result.deleted_symlink) if result.deleted_symlink else None,
            "message": result.message if result.message else ("卸载成功" if result.success else "卸载失败")
        }
        
        if not result.success:
            output["error"] = result.message
        
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0 if result.success else 1
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "skill_name": args.skill,
            "error": str(e)
        }, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
