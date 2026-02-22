"""
skill-installer 入口点

使用方法:
    python -m skill-installer [命令] [选项]
    
示例:
    python -m skill-installer install skill-name
    python -m skill-installer uninstall skill-name
    python -m skill-installer list
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
