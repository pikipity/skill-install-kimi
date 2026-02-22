"""
L2: CLI 层功能测试（简化版）

测试目标：验证 cli_ui.py 的核心交互组件正常工作
测试方法：直接测试 UI 组件，不测试完整 CLI 流程
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from io import StringIO

# 添加测试辅助
tests_dir = Path(__file__).parent
project_dir = tests_dir.parent
skill_installer_src = project_dir / 'skill-installer' / 'src'

# 创建 skill_installer 包命名空间
if 'skill_installer' not in sys.modules:
    import types
    skill_installer_mod = types.ModuleType('skill_installer')
    skill_installer_mod.__path__ = [str(skill_installer_src.parent)]
    sys.modules['skill_installer'] = skill_installer_mod
    
    skill_installer_src_mod = types.ModuleType('skill_installer.src')
    skill_installer_src_mod.__path__ = [str(skill_installer_src)]
    sys.modules['skill_installer.src'] = skill_installer_src_mod

# 添加 src 到路径
if str(skill_installer_src) not in sys.path:
    sys.path.insert(0, str(skill_installer_src))

from skill_installer.src import cli_ui
from skill_installer.src import api


class TestConsoleUI(unittest.TestCase):
    """测试 ConsoleUI 基础功能"""
    
    def test_prompt_with_choices(self):
        """CLI-01: 提示用户输入（带选项）"""
        # 模拟输入（input 会接收 prompt 参数）
        inputs = iter(["A"])
        
        ui = cli_ui.ConsoleUI(
            input_func=lambda prompt="": next(inputs),
            output_func=lambda x: None  # 不需要捕获输出
        )
        
        result = ui.prompt("请选择", choices=["A", "B", "C"])
        
        self.assertEqual(result, "A")
        print(f"✅ CLI-01 PASS: prompt 正确返回 {result}")
    
    def test_confirm_yes(self):
        """CLI-02: 确认操作（是）"""
        inputs = iter(["Y"])
        output = StringIO()
        
        ui = cli_ui.ConsoleUI(
            input_func=lambda prompt="": next(inputs),
            output_func=lambda x: output.write(str(x) + "\n")
        )
        
        result = ui.confirm("确认执行？", default=True)
        
        self.assertTrue(result)
        print(f"✅ CLI-02 PASS: confirm 正确返回 {result}")
    
    def test_confirm_no(self):
        """CLI-03: 确认操作（否）"""
        inputs = iter(["N"])
        output = StringIO()
        
        ui = cli_ui.ConsoleUI(
            input_func=lambda prompt="": next(inputs),
            output_func=lambda x: output.write(str(x) + "\n")
        )
        
        result = ui.confirm("确认执行？", default=True)
        
        self.assertFalse(result)
        print(f"✅ CLI-03 PASS: confirm 正确返回 {result}")
    
    def test_print_header(self):
        """CLI-04: 打印标题"""
        output = StringIO()
        
        ui = cli_ui.ConsoleUI(output_func=lambda x: output.write(str(x) + "\n"))
        
        ui.print_header("测试标题")
        
        output_str = output.getvalue()
        self.assertIn("测试标题", output_str)
        self.assertIn("═", output_str)
        print(f"✅ CLI-04 PASS: print_header 输出正确")
    
    def test_print_table(self):
        """CLI-05: 打印表格"""
        output = StringIO()
        
        ui = cli_ui.ConsoleUI(output_func=lambda x: output.write(str(x) + "\n"))
        
        headers = ["名称", "状态"]
        rows = [["skill-1", "✅"], ["skill-2", "⏳"]]
        
        ui.print_table(headers, rows)
        
        output_str = output.getvalue()
        self.assertIn("名称", output_str)
        self.assertIn("skill-1", output_str)
        print(f"✅ CLI-05 PASS: print_table 输出正确")


class TestInstallUI(unittest.TestCase):
    """测试 InstallUI"""
    
    def test_display_install_plan(self):
        """CLI-06: 显示安装方案"""
        output = StringIO()
        
        console_ui = cli_ui.ConsoleUI(output_func=lambda x: output.write(str(x) + "\n"))
        install_ui = cli_ui.InstallUI(console_ui)
        
        # 创建模拟方案
        plan = api.InstallPlan(
            skill_name="test-skill",
            source_path="/manager/test-skill",
            symlink_path="~/.kimi/skills/test-skill",
            relative_path="../../manager/test-skill",
            option="full",
            pre_check_passed=True,
            pre_check_errors=[]
        )
        
        install_ui.display_install_plan(plan)
        
        output_str = output.getvalue()
        self.assertIn("test-skill", output_str)
        self.assertIn("安装方案", output_str)
        print(f"✅ CLI-06 PASS: display_install_plan 输出正确")


class TestUninstallUI(unittest.TestCase):
    """测试 UninstallUI"""
    
    def test_display_uninstall_plan(self):
        """CLI-07: 显示卸载方案"""
        output = StringIO()
        
        console_ui = cli_ui.ConsoleUI(output_func=lambda x: output.write(str(x) + "\n"))
        uninstall_ui = cli_ui.UninstallUI(console_ui)
        
        # 创建模拟方案
        plan = api.UninstallPlan(
            skill_name="test-skill",
            source_path="/manager/test-skill",
            symlink_path="~/.kimi/skills/test-skill",
            delete_commands={},
            pre_check_passed=True,
            pre_check_errors=[]
        )
        
        uninstall_ui.display_uninstall_plan(plan)
        
        output_str = output.getvalue()
        self.assertIn("test-skill", output_str)
        self.assertIn("卸载方案", output_str)
        print(f"✅ CLI-07 PASS: display_uninstall_plan 输出正确")


def run_tests():
    """运行所有 L2 测试"""
    print("\n" + "="*60)
    print("L2: CLI 层功能测试")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestConsoleUI,
        TestInstallUI,
        TestUninstallUI,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print("\n" + "="*60)
    print(f"L2 测试结果: {passed}/{total} 通过")
    print("="*60)
    
    return result.wasSuccessful(), passed, total


if __name__ == "__main__":
    success, passed, total = run_tests()
    sys.exit(0 if success else 1)
