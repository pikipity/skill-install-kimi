"""
配置管理测试 - L1 代码测试（脚本架构版）
测试 scripts/check_config.py 和 init_config.py
"""

import unittest
import subprocess
import json
import tempfile
import shutil
import sys
from pathlib import Path


class TestScriptsConfig(unittest.TestCase):
    """测试脚本配置功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "skill-installer" / "scripts"
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
    
    def run_script(self, script_name, args=None, cwd=None):
        """运行脚本并返回结果"""
        script_path = self.scripts_dir / script_name
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        # 使用临时目录作为工作目录（隔离）
        if cwd is None:
            cwd = self.tmp_dir
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd)
        )
        
        # 尝试解析 JSON
        try:
            output = json.loads(result.stdout) if result.stdout else {}
        except json.JSONDecodeError:
            output = {"raw": result.stdout, "stderr": result.stderr}
        
        return result.returncode, output, result.stderr
    
    def test_check_config_not_configured(self):
        """测试未配置状态"""
        code, output, stderr = self.run_script("check_config.py")
        
        self.assertFalse(output.get("configured", True))
        self.assertIn("platform", output)
        self.assertIn("is_admin", output)
    
    def test_init_config_success(self):
        """测试初始化配置成功"""
        manager_dir = self.tmp_dir / "manager"
        manager_dir.mkdir()
        
        code, output, stderr = self.run_script(
            "init_config.py",
            ["--dir", str(manager_dir)]
        )
        
        self.assertTrue(output.get("success", False))
        self.assertEqual(output.get("manager_dir"), str(manager_dir))
    
    def test_init_config_invalid_path(self):
        """测试无效路径"""
        code, output, stderr = self.run_script(
            "init_config.py",
            ["--dir", "C:\\不存在的路径\\12345"]
        )
        
        self.assertFalse(output.get("success", True))
        self.assertIn("error", output)
    
    def test_full_config_flow(self):
        """测试完整配置流程（简化版）"""
        import shutil
        
        # 使用真实项目目录进行测试
        manager_dir = self.tmp_dir / "manager"
        manager_dir.mkdir()
        
        # 步骤1: 初始化配置
        code, output, _ = self.run_script(
            "init_config.py",
            ["--dir", str(manager_dir)]
        )
        self.assertTrue(output.get("success"), f"初始化失败: {output}")
        
        # 步骤2: 验证配置文件已创建
        config_file = self.project_root / "skill-installer" / "data" / "config.json"
        self.assertTrue(config_file.exists(), "配置文件未创建")
        
        # 清理：删除测试配置
        if config_file.exists():
            config_file.unlink()
        data_dir = config_file.parent
        if data_dir.exists():
            data_dir.rmdir()


if __name__ == "__main__":
    unittest.main(verbosity=2)
