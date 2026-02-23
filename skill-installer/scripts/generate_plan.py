#!/usr/bin/env python3
"""
生成安装/卸载方案

用法:
    python generate_plan.py --skill <name> --action <install|uninstall> [--option <full|light|clone>]

参数:
    --skill: skill 名称
    --action: install 或 uninstall
    --option: 安装选项（仅 action=install 时有效）

输出(JSON):
    安装方案:
    {
        "action": "install",
        "skill_name": "skill-pdf",
        "source_path": "C:\\Users\\...\\skill-pdf",
        "symlink_path": "C:\\Users\\...\\.kimi\\skills\\skill-pdf",
        "relative_path": "../../...",
        "option": "full",
        "requires_admin": false,
        "windows_manual_command": null,
        "pre_check_passed": true,
        "pre_check_errors": []
    }
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import ConfigManager
from platform_utils import PlatformInfo, PlatformUtils


def generate_install_plan(skill_name, option, config, paths):
    """生成安装方案"""
    from core import InstallOption
    from platform_utils import PlatformUtils
    
    # 【关键】在管理目录下递归查找 skill（支持嵌套结构）
    source_path = paths.find_skill_source(skill_name)
    if source_path is None:
        # 未找到，使用默认路径用于错误提示
        source_path = paths.get_skill_source_path(skill_name)
    
    symlink_path = paths.get_skill_symlink_path(skill_name)
    
    # 检查是否需要管理员权限（Windows）
    platform = PlatformInfo.get_system()
    requires_admin = platform == "windows" and not PlatformUtils.is_admin()
    
    # 生成 Windows 手动命令
    windows_manual_command = None
    if requires_admin:
        windows_manual_command = {
            "powershell": f'New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\\.kimi\\skills\\{skill_name}" -Target "{source_path}"',
            "cmd": f'mklink /D %USERPROFILE%\\.kimi\\skills\\{skill_name} {source_path}'
        }
    
    # 预检查
    errors = []
    if not source_path.exists():
        errors.append(f"Skill 源目录不存在: {source_path}")
    
    # 计算相对路径（使用实际找到的源路径）
    relative_path = PlatformUtils.calculate_relative_path(source_path, symlink_path.parent)
    
    return {
        "action": "install",
        "skill_name": skill_name,
        "source_path": str(source_path),
        "symlink_path": str(symlink_path),
        "relative_path": relative_path,
        "option": option,
        "requires_admin": requires_admin,
        "windows_manual_command": windows_manual_command,
        "pre_check_passed": len(errors) == 0,
        "pre_check_errors": errors
    }


def generate_uninstall_plan(skill_name, config, paths):
    """生成卸载方案"""
    symlink_path = paths.get_skill_symlink_path(skill_name)
    
    # 关键：从软连接解析实际源路径（支持任意嵌套结构）
    try:
        source_path = symlink_path.resolve()
    except Exception:
        # 备用：使用默认路径
        source_path = paths.get_skill_source_path(skill_name)
    
    # 生成各平台的删除命令
    delete_commands = {
        "macos": f"rm -rf '{symlink_path}'",
        "linux": f"rm -rf '{symlink_path}'",
        "windows": f'Remove-Item -Recurse -Force "{symlink_path}"'
    }
    
    # 预检查：验证软连接存在且是有效 skill
    errors = []
    if not symlink_path.exists():
        errors.append(f"Skill 未安装: {skill_name}")
    elif not (source_path / "SKILL.md").exists():
        errors.append(f"无效的 skill 目录: {skill_name}")
    
    return {
        "action": "uninstall",
        "skill_name": skill_name,
        "source_path": str(source_path),
        "symlink_path": str(symlink_path),
        "delete_commands": delete_commands,
        "pre_check_passed": len(errors) == 0,
        "pre_check_errors": errors
    }


def main():
    parser = argparse.ArgumentParser(description='生成安装/卸载方案')
    parser.add_argument('--skill', required=True, help='skill 名称')
    parser.add_argument('--action', required=True, choices=['install', 'uninstall'], help='操作类型')
    parser.add_argument('--option', default='full', choices=['full', 'light', 'clone'], help='安装选项')
    args = parser.parse_args()
    
    skill_dir = Path(__file__).parent.parent
    config = ConfigManager(skill_dir)
    
    if not config.is_configured:
        print(json.dumps({"error": "未配置"}, indent=2, ensure_ascii=False))
        return 1
    
    try:
        from path_manager import PathManager
        
        paths = PathManager(config.get_manager_dir())
        
        if args.action == 'install':
            plan = generate_install_plan(args.skill, args.option, config, paths)
        else:
            plan = generate_uninstall_plan(args.skill, config, paths)
        
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0 if plan.get('pre_check_passed', False) else 1
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
