#!/usr/bin/env python3
"""
执行 skill 安装

用法:
    python install.py --skill <name> [--option <full|light|clone>]

参数:
    --skill: skill 名称
    --option: 安装选项（默认 full）

输出(JSON):
    成功:
    {
        "success": true,
        "skill_name": "skill-pdf",
        "source_path": "C:\\Users\\...\\skill-pdf",
        "symlink_path": "C:\\Users\\...\\.kimi\\skills\\skill-pdf",
        "message": "安装成功"
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
from core import SkillInstaller, InstallOption


def main():
    parser = argparse.ArgumentParser(description='安装 skill')
    parser.add_argument('--skill', required=True, help='skill 名称')
    parser.add_argument('--option', default='full', choices=['full', 'light', 'clone'], help='安装选项')
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
        
        # 转换选项
        option_map = {
            'full': InstallOption.FULL,
            'light': InstallOption.LIGHT,
            'clone': InstallOption.CLONE_ONLY
        }
        option = option_map.get(args.option, InstallOption.FULL)
        
        # 执行安装
        result = installer.install(args.skill, option)
        
        # 【关键】递归查找 skill 源目录（支持嵌套结构）
        source_path = paths.find_skill_source(args.skill)
        if source_path is None:
            source_path = paths.get_skill_source_path(args.skill)
        
        output = {
            "success": result.success,
            "skill_name": args.skill,
            "source_path": str(source_path),
            "symlink_path": str(result.symlink_path) if result.symlink_path else None,
            "message": result.message if result.message else ("安装成功" if result.success else "安装失败")
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
