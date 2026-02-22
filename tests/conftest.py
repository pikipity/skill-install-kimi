"""
测试配置 - 确保临时目录清理
"""

import shutil
import tempfile
from pathlib import Path

# 注册全局清理函数
def cleanup_all_temp_dirs():
    """清理所有测试相关的临时目录"""
    temp_root = Path(tempfile.gettempdir())
    patterns = ['api-test-*', 'cli-test-*', 'int-test-*', 'iso-test-*', 'err-test-*']
    
    cleaned = 0
    for pattern in patterns:
        for temp_dir in temp_root.glob(pattern):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                cleaned += 1
            except:
                pass
    
    if cleaned > 0:
        print(f"\n[测试清理] 清理了 {cleaned} 个残留临时目录")

# 在测试会话结束时执行清理
import atexit
atexit.register(cleanup_all_temp_dirs)
