"""
L5: 异常处理测试

测试目标：验证各种错误场景的优雅处理
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


class TestExceptionSetup(unittest.TestCase):
    """异常测试设置"""
    
    def setUp(self):
        """设置隔离环境"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="err-test-"))
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


class TestERR01UninitializedAPI(TestExceptionSetup):
    """ERR-01: 配置未初始化调用 API"""
    
    def test_list_without_config(self):
        """测试未配置时调用 list API"""
        # 不初始化配置，直接调用
        result = api.list_available_skills()
        
        # 应返回空列表，不抛异常
        self.assertEqual(result, [])
        print(f"✅ ERR-01 PASS: 未配置时返回空列表，无异常")
    
    def test_install_without_config(self):
        """测试未配置时调用 install API"""
        result = api.install_skill("test", "full")
        
        # 应返回失败结果，不抛异常
        self.assertFalse(result.success)
        self.assertIn("管理目录", result.message)  # 未配置时会提示管理目录问题
        print(f"✅ ERR-01 CHECK: 未配置时 install 返回失败")


class TestERR02InstallNotExist(TestExceptionSetup):
    """ERR-02: 安装不存在 skill"""
    
    def test_install_nonexistent_skill(self):
        """测试安装不存在的 skill"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 尝试安装不存在的 skill
        result = api.install_skill("not-exists-xyz", "full")
        
        # 应返回失败，带清晰错误信息
        self.assertFalse(result.success)
        self.assertIn("不存在", result.message)
        print(f"✅ ERR-02 PASS: 错误信息清晰: {result.message}")


class TestERR03DuplicateInstall(TestExceptionSetup):
    """ERR-03: 重复安装"""
    
    def test_duplicate_install(self):
        """测试重复安装同一 skill"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建并安装 skill
        self._create_test_skill("dup-test")
        result1 = api.install_skill("dup-test", "full")
        self.assertTrue(result1.success)
        
        # 再次安装同一 skill
        result2 = api.install_skill("dup-test", "full")
        
        # 应返回失败（软连接已存在）
        self.assertFalse(result2.success)
        print(f"✅ ERR-03 PASS: 重复安装被阻止")


class TestERR04UninstallNotInstalled(TestExceptionSetup):
    """ERR-04: 卸载未安装 skill"""
    
    def test_uninstall_not_installed(self):
        """测试卸载未安装的 skill"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 尝试卸载未安装的 skill
        result = api.uninstall_skill("never-installed")
        
        # 应返回失败
        self.assertFalse(result.success)
        print(f"✅ ERR-04 PASS: 卸载未安装 skill 返回失败")


def run_tests():
    """运行 L5 测试"""
    print("\n" + "="*60)
    print("L5: 异常处理测试")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestERR01UninitializedAPI,
        TestERR02InstallNotExist,
        TestERR03DuplicateInstall,
        TestERR04UninstallNotInstalled,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print("\n" + "="*60)
    print(f"L5 测试结果: {passed}/{total} 通过")
    print("="*60)
    
    return result.wasSuccessful(), passed, total


if __name__ == "__main__":
    success, passed, total = run_tests()
    sys.exit(0 if success else 1)
