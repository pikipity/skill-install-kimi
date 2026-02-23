#!/usr/bin/env python3
"""
初始化 skill-installer 配置

用法:
    python init_config.py --dir <管理目录路径>

参数:
    --dir: 管理目录的绝对路径

输出(JSON):
    成功:
    {
        "success": true,
        "manager_dir": "C:\\Users\\...\\skills"
    }
    
    失败:
    {
        "success": false,
        "error": "错误信息"
    }
"""

import argparse
import json
import sys
from pathlib import Path

# 添加 lib 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import ConfigManager, ConfigError


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='初始化 skill-installer 配置')
    parser.add_argument('--dir', required=True, help='管理目录的绝对路径')
    args = parser.parse_args()
    
    # 验证路径
    manager_dir = Path(args.dir).expanduser().resolve()
    
    if not manager_dir.exists():
        result = {
            "success": False,
            "error": f"目录不存在: {manager_dir}"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    
    if not manager_dir.is_absolute():
        result = {
            "success": False,
            "error": f"必须是绝对路径: {manager_dir}"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    
    try:
        # 获取配置管理器
        skill_dir = Path(__file__).parent.parent
        config_manager = ConfigManager(skill_dir)
        
        # 保存配置
        config = {
            'manager_dir': str(manager_dir),
            'first_config_time': str(Path().stat().st_mtime if Path().exists() else 0)
        }
        config_manager.save(config)
        
        result = {
            "success": True,
            "manager_dir": str(manager_dir)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
        
    except ConfigError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1
    except Exception as e:
        result = {
            "success": False,
            "error": f"初始化失败: {e}"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
