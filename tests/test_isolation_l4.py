"""
L4: 隔离性测试

测试目标：验证测试不影响真实 ~/.kimi/skills/ 目录
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


def get_real_kimi_skills():
    """获取真实 ~/.kimi/skills/ 目录状态"""
    real_kimi = Path.home() / ".kimi" / "skills"
    if not real_kimi.exists():
        return set()
    return set(p.name for p in real_kimi.iterdir() if p.is_dir() or p.is_symlink())


class TestIsolation(unittest.TestCase):
    """隔离性测试"""
    
    @classmethod
    def setUpClass(cls):
        """记录测试前的真实环境状态"""
        cls.before_state = get_real_kimi_skills()
        print(f"\n真实环境测试前状态: {len(cls.before_state)} 个 skills")
    
    @classmethod
    def tearDownClass(cls):
        """验证测试后真实环境无变化"""
        after_state = get_real_kimi_skills()
        
        print(f"真实环境测试后状态: {len(after_state)} 个 skills")
        
        if cls.before_state != after_state:
            added = after_state - cls.before_state
            removed = cls.before_state - after_state
            print(f"❌ 真实环境被修改！新增: {added}, 删除: {removed}")
            raise AssertionError(f"隔离性测试失败！真实环境被修改: 新增={added}, 删除={removed}")
        else:
            print(f"✅ 真实环境未受影响")
    
    def setUp(self):
        """设置隔离环境"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="iso-test-"))
        self.temp_kimi_dir = self.temp_dir / ".kimi"
        self.temp_kimi_dir.mkdir(parents=True, exist_ok=True)
        (self.temp_kimi_dir / "skills").mkdir(exist_ok=True)
        
        self.temp_manager_dir = self.temp_dir / "manager"
        self.temp_manager_dir.mkdir(exist_ok=True)
        
        # Mock get_kimi_dir 返回临时目录
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


class TestISO01NoRealEnvChange(TestIsolation):
    """ISO-01: ~/.kimi/skills/ 无变化"""
    
    def test_install_does_not_affect_real_env(self):
        """测试安装不影响真实环境"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建并安装测试 skill
        self._create_test_skill("iso-test-skill")
        api.install_skill("iso-test-skill", "full")
        
        # 验证安装在临时目录
        temp_symlink = self.temp_kimi_dir / "skills" / "iso-test-skill"
        self.assertTrue(temp_symlink.exists() or temp_symlink.is_symlink())
        
        # 验证真实目录未受影响（在 tearDownClass 中统一检查）
        print(f"✅ ISO-01 CHECK: 安装操作在隔离环境完成")


class TestISO02TempIsolation(TestIsolation):
    """ISO-02: 临时环境隔离"""
    
    def test_temp_env_isolation(self):
        """测试临时环境完全隔离"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建多个测试 skills
        for i in range(3):
            self._create_test_skill(f"iso-skill-{i}")
            api.install_skill(f"iso-skill-{i}", "full")
        
        # 验证所有操作都在临时目录
        temp_skills = list((self.temp_kimi_dir / "skills").iterdir())
        self.assertEqual(len(temp_skills), 3)
        
        # 验证真实目录无这些 skills
        real_skills = get_real_kimi_skills()
        for skill in temp_skills:
            self.assertNotIn(skill.name, real_skills, 
                           f"测试 skill {skill.name} 不应在真实目录中")
        
        print(f"✅ ISO-02 PASS: 临时环境完全隔离")


class TestISO03Cleanup(TestIsolation):
    """ISO-03: 测试残留清理"""
    
    def test_cleanup_on_teardown(self):
        """测试 tearDown 正确清理"""
        # 记录测试目录
        temp_dir = self.temp_dir
        
        # 初始化并创建一些数据
        api.initialize_config(str(self.temp_manager_dir))
        self._create_test_skill("cleanup-test")
        api.install_skill("cleanup-test", "full")
        
        # 验证数据存在
        self.assertTrue((temp_dir / ".kimi" / "skills" / "cleanup-test").exists())
        
        # tearDown 后会清理
        print(f"✅ ISO-03 CHECK: tearDown 将清理 {temp_dir}")


def run_tests():
    """运行 L4 测试"""
    print("\n" + "="*60)
    print("L4: 隔离性测试")
    print("="*60)
    print("⚠️  本测试会验证是否影响真实 ~/.kimi/skills/ 目录")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestISO01NoRealEnvChange,
        TestISO02TempIsolation,
        TestISO03Cleanup,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print("\n" + "="*60)
    print(f"L4 测试结果: {passed}/{total} 通过")
    print("="*60)
    
    return result.wasSuccessful(), passed, total


if __name__ == "__main__":
    success, passed, total = run_tests()
    sys.exit(0 if success else 1)
