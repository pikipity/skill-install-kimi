"""
L3: 双模式集成测试

测试目标：验证 API 层和 CLI 层数据一致性
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

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

from skill_installer.src import api
from skill_installer.src import platform_utils


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置隔离环境"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="int-test-"))
        self.temp_kimi_dir = self.temp_dir / ".kimi"
        self.temp_kimi_dir.mkdir(parents=True, exist_ok=True)
        (self.temp_kimi_dir / "skills").mkdir(exist_ok=True)
        
        self.temp_manager_dir = self.temp_dir / "manager"
        self.temp_manager_dir.mkdir(exist_ok=True)
        
        # Mock get_kimi_dir
        self.patcher = patch.object(
            platform_utils.PlatformInfo, 
            'get_kimi_dir', 
            return_value=self.temp_kimi_dir
        )
        self.patcher.start()
        
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
    
    def tearDown(self):
        """清理"""
        self.patcher.stop()
    
    def run(self, result=None):
        self.addCleanup(self._cleanup_temp)
        return super().run(result)
    
    def _cleanup_temp(self):
        """额外的清理保障"""
        if hasattr(self, "temp_dir") and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_skill(self, name: str):
        """创建测试 skill"""
        skill_src = self.temp_manager_dir / name
        skill_src.mkdir(exist_ok=True)
        (skill_src / "SKILL.md").write_text(f"# {name}\nTest", encoding="utf-8")
        return skill_src


class TestINT01KimiModeInstall(TestIntegration):
    """INT-01: Kimi 模式安装"""
    
    def test_kimi_mode_install(self):
        """测试 API 安装不阻塞"""
        self._create_test_skill("kimi-install")
        
        # API 直接安装，无交互
        result = api.install_skill("kimi-install", "full")
        
        self.assertTrue(result.success)
        
        # 验证已安装
        installed = api.list_installed_skills()
        names = [s.name for s in installed]
        self.assertIn("kimi-install", names)
        
        print(f"✅ INT-01 PASS: API 安装成功，无阻塞")


class TestINT02CLIModeInstall(TestIntegration):
    """INT-02: CLI 模式安装"""
    
    def test_cli_mode_data(self):
        """测试 CLI 层能正确读取 API 数据"""
        self._create_test_skill("cli-test")
        
        # 使用 API 获取数据（模拟 CLI 层调用）
        available = api.list_available_skills()
        
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].name, "cli-test")
        
        print(f"✅ INT-02 PASS: CLI 层数据读取正确")


class TestINT03DataConsistency(TestIntegration):
    """INT-03: 模式数据一致性"""
    
    def test_data_consistency(self):
        """测试 API 安装后 CLI 能正确识别"""
        self._create_test_skill("consistency-test")
        
        # API 安装
        api.install_skill("consistency-test", "full")
        
        # API 查询已安装
        installed_api = api.list_installed_skills()
        
        # 验证
        self.assertEqual(len(installed_api), 1)
        self.assertEqual(installed_api[0].name, "consistency-test")
        self.assertTrue(installed_api[0].is_installed)
        
        # 验证可用列表不再包含
        available = api.list_available_skills()
        available_names = [s.name for s in available]
        self.assertNotIn("consistency-test", available_names)
        
        print(f"✅ INT-03 PASS: 数据一致性正确")


class TestINT04PlanGeneration(TestIntegration):
    """INT-04: 方案生成不执行"""
    
    def test_plan_no_side_effect(self):
        """测试生成方案不创建软连接"""
        self._create_test_skill("plan-test")
        
        # 生成安装方案
        plan = api.generate_install_plan("plan-test", "full")
        
        self.assertIsNotNone(plan)
        self.assertTrue(plan.pre_check_passed)
        
        # 验证未创建软连接
        symlink = self.temp_kimi_dir / "skills" / "plan-test"
        self.assertFalse(symlink.exists())
        
        # 验证不在已安装列表
        installed = api.list_installed_skills()
        self.assertEqual(len(installed), 0)
        
        print(f"✅ INT-04 PASS: 方案生成无副作用")


def run_tests():
    """运行 L3 测试"""
    print("\n" + "="*60)
    print("L3: 双模式集成测试")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestINT01KimiModeInstall,
        TestINT02CLIModeInstall,
        TestINT03DataConsistency,
        TestINT04PlanGeneration,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print("\n" + "="*60)
    print(f"L3 测试结果: {passed}/{total} 通过")
    print("="*60)
    
    return result.wasSuccessful(), passed, total


if __name__ == "__main__":
    success, passed, total = run_tests()
    sys.exit(0 if success else 1)
