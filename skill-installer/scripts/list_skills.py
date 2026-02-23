#!/usr/bin/env python3
"""
列出 skills

用法:
    python list_skills.py [--installed | --available]

参数:
    --installed: 只列出已安装的 skills
    --available: 只列出可安装的 skills（默认）

输出(JSON):
    {
        "skills": [
            {
                "name": "skill-pdf",
                "source_path": "C:\\Users\\...\\skill-pdf",
                "is_installed": true,
                "symlink_path": "C:\\Users\\...\\.kimi\\skills\\skill-pdf",
                "symlink_valid": true,
                "source_valid": true
            }
        ],
        "count": 1
    }
"""

import argparse
import json
import sys
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import ConfigManager


def get_skill_info(config, paths, name, is_installed):
    """获取单个 skill 的信息"""
    info = paths.get_install_info(name)
    result = {
        "name": name,
        "source_path": str(info['source_path']),
        "is_installed": is_installed,
        "source_valid": info.get('source_valid', False)
    }
    
    if is_installed:
        result["symlink_path"] = str(info['symlink_path']) if info.get('symlink_path') else None
        result["symlink_valid"] = info.get('symlink_valid', False)
    else:
        result["symlink_path"] = None
        result["symlink_valid"] = False
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='列出 skills')
    parser.add_argument('--installed', action='store_true', help='只列出已安装的 skills')
    parser.add_argument('--available', action='store_true', help='只列出可安装的 skills')
    args = parser.parse_args()
    
    # 获取配置
    skill_dir = Path(__file__).parent.parent
    config = ConfigManager(skill_dir)
    
    if not config.is_configured:
        result = {
            "skills": [],
            "count": 0,
            "error": "未配置"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    
    try:
        # 添加 path_manager 到路径
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from path_manager import PathManager
        
        paths = PathManager(config.get_manager_dir())
        skills = []
        
        # 根据参数决定列出哪些 skills
        if args.installed:
            # 只列出已安装的
            names = paths.get_installed_skills()
            for name in names:
                skills.append(get_skill_info(config, paths, name, True))
        elif args.available:
            # 只列出可安装的
            names = paths.get_available_skills()
            for name in names:
                skills.append(get_skill_info(config, paths, name, False))
        else:
            # 默认列出所有
            installed_names = set(paths.get_installed_skills())
            available_names = set(paths.get_available_skills())
            all_names = installed_names | available_names
            
            for name in all_names:
                is_installed = name in installed_names
                skills.append(get_skill_info(config, paths, name, is_installed))
        
        result = {
            "skills": skills,
            "count": len(skills)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
        
    except Exception as e:
        result = {
            "skills": [],
            "count": 0,
            "error": str(e)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
