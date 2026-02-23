"""
skill-installer: 标准化安装、卸载、管理 Kimi CLI Skills 的工具
"""

__version__ = "1.0.0"

# 导出 API 模块（供 Kimi 交互式调用）
try:
    from . import api
except ImportError:
    pass  # 避免循环导入问题
