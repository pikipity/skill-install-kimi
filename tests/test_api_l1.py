"""
L1: API 层单元测试

测试目标：验证 api.py 的所有纯函数接口正确工作
测试环境：使用临时目录隔离，不影响真实 ~/.kimi/
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

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
from skill_installer.src import config as config_module
from skill_installer.src import platform_utils


class TestSetup(unittest.TestCase):
    """测试环境设置"""
    
    def setUp(self):
        """每个测试前创建隔离环境"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="api-test-"))
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
        
        # 清理可能存在的配置
        self._cleanup_config()
    
    def tearDown(self):
        """每个测试后清理"""
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
    
    def _cleanup_config(self):
        """清理配置文件"""
        # 查找并删除测试目录下的 config.json
        for config_file in self.temp_dir.rglob("config.json"):
            try:
                config_file.unlink()
            except:
                pass
    
    def _create_test_skill(self, name: str, installed: bool = False):
        """创建测试用的 skill"""
        skill_src = self.temp_manager_dir / name
        skill_src.mkdir(exist_ok=True)
        (skill_src / "SKILL.md").write_text(f"# {name}\nTest skill", encoding="utf-8")
        
        if installed:
            # 创建软连接
            symlink = self.temp_kimi_dir / "skills" / name
            if not symlink.exists():
                # 使用相对路径或绝对路径创建
                try:
                    symlink.symlink_to(skill_src)
                except OSError:
                    # Windows 可能需要特殊处理
                    import subprocess
                    subprocess.run(["ln", "-s", str(skill_src), str(symlink)], check=False)
        
        return skill_src


class TestAPI01ValidateSetupNotConfigured(TestSetup):
    """API-01: validate_setup() 未配置状态"""
    
    def test_validate_setup_not_configured(self):
        """测试未配置时返回 configured=False"""
        status = api.validate_setup()
        
        self.assertFalse(status.configured)
        self.assertIsNone(status.manager_dir)
        self.assertIsNone(status.error)
        print(f"✅ API-01 PASS: configured={status.configured}")


class TestAPI02ValidateSetupConfigured(TestSetup):
    """API-02: validate_setup() 已配置状态"""
    
    def test_validate_setup_configured(self):
        """测试已配置时返回正确信息"""
        # 先初始化配置
        success, error = api.initialize_config(str(self.temp_manager_dir))
        self.assertTrue(success, f"初始化失败: {error}")
        
        # 测试验证
        status = api.validate_setup()
        
        self.assertTrue(status.configured)
        self.assertEqual(str(Path(status.manager_dir).resolve()), str(self.temp_manager_dir.resolve()))
        self.assertIsNone(status.error)
        print(f"✅ API-02 PASS: configured={status.configured}, dir={status.manager_dir}")


class TestAPI03InitializeConfigSuccess(TestSetup):
    """API-03: initialize_config() 成功"""
    
    def test_initialize_config_success(self):
        """测试配置初始化成功"""
        success, error = api.initialize_config(str(self.temp_manager_dir))
        
        self.assertTrue(success)
        self.assertEqual(error, "")
        
        # 验证配置文件已创建
        status = api.validate_setup()
        self.assertTrue(status.configured)
        print(f"✅ API-03 PASS: 配置初始化成功")


class TestAPI04InitializeConfigFailure(TestSetup):
    """API-04: initialize_config() 失败"""
    
    def test_initialize_config_invalid_path(self):
        """测试无效路径返回错误"""
        success, error = api.initialize_config("/不存在的路径/12345")
        
        self.assertFalse(success)
        self.assertIn("不存在", error)
        print(f"✅ API-04 PASS: 错误信息={error}")


class TestAPI05ListAvailableSkills(TestSetup):
    """API-05: list_available_skills()"""
    
    def test_list_available_skills(self):
        """测试列出可安装 skills"""
        # 创建测试 skill
        self._create_test_skill("test-skill-1")
        self._create_test_skill("test-skill-2")
        
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 测试
        skills = api.list_available_skills()
        
        self.assertEqual(len(skills), 2)
        skill_names = [s.name for s in skills]
        self.assertIn("test-skill-1", skill_names)
        self.assertIn("test-skill-2", skill_names)
        print(f"✅ API-05 PASS: 找到 {len(skills)} 个可安装 skills")


class TestAPI06ListInstalledSkills(TestSetup):
    """API-06: list_installed_skills()"""
    
    def test_list_installed_skills(self):
        """测试列出已安装 skills"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建并安装测试 skill
        self._create_test_skill("installed-skill", installed=True)
        
        # 测试
        skills = api.list_installed_skills()
        
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "installed-skill")
        self.assertTrue(skills[0].is_installed)
        print(f"✅ API-06 PASS: 找到 {len(skills)} 个已安装 skills")


class TestAPI07GenerateInstallPlan(TestSetup):
    """API-07: generate_install_plan()"""
    
    def test_generate_install_plan(self):
        """测试生成安装方案"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建测试 skill
        self._create_test_skill("plan-skill")
        
        # 生成方案
        plan = api.generate_install_plan("plan-skill", "full")
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.skill_name, "plan-skill")
        self.assertEqual(plan.option, "full")
        self.assertTrue(plan.pre_check_passed)
        self.assertIn("plan-skill", plan.source_path)
        print(f"✅ API-07 PASS: 方案生成成功，选项={plan.option}")


class TestAPI08GenerateUninstallPlan(TestSetup):
    """API-08: generate_uninstall_plan()"""
    
    def test_generate_uninstall_plan(self):
        """测试生成卸载方案"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建并安装测试 skill
        self._create_test_skill("uninstall-skill", installed=True)
        
        # 生成方案
        plan = api.generate_uninstall_plan("uninstall-skill")
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.skill_name, "uninstall-skill")
        self.assertTrue(plan.pre_check_passed)
        self.assertIn("delete_commands", dir(plan))
        print(f"✅ API-08 PASS: 卸载方案生成成功")


class TestAPI09InstallSkillSuccess(TestSetup):
    """API-09: install_skill() 成功"""
    
    def test_install_skill_success(self):
        """测试安装 skill 成功"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建测试 skill
        self._create_test_skill("install-me")
        
        # 执行安装
        result = api.install_skill("install-me", "full")
        
        self.assertTrue(result.success)
        self.assertIn("install-me", result.symlink_path.name)
        
        # 验证软连接已创建
        symlink = self.temp_kimi_dir / "skills" / "install-me"
        self.assertTrue(symlink.exists() or symlink.is_symlink())
        print(f"✅ API-09 PASS: 安装成功，软连接={result.symlink_path}")


class TestAPI10InstallSkillFailure(TestSetup):
    """API-10: install_skill() 失败"""
    
    def test_install_skill_not_exists(self):
        """测试安装不存在的 skill 失败"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 尝试安装不存在的 skill
        result = api.install_skill("not-exists-skill", "full")
        
        self.assertFalse(result.success)
        self.assertIn("失败", result.message)
        print(f"✅ API-10 PASS: 安装失败处理正确，错误={result.message}")


class TestAPI11UninstallSkillSuccess(TestSetup):
    """API-11: uninstall_skill() 成功"""
    
    def test_uninstall_skill_success(self):
        """测试卸载 skill 成功"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建并安装测试 skill
        self._create_test_skill("uninstall-me", installed=True)
        
        # 执行卸载
        result = api.uninstall_skill("uninstall-me")
        
        self.assertTrue(result.success)
        
        # 验证软连接已删除
        symlink = self.temp_kimi_dir / "skills" / "uninstall-me"
        self.assertFalse(symlink.exists())
        print(f"✅ API-11 PASS: 卸载成功")


class TestAPI12GetSkillDetail(TestSetup):
    """API-12: get_skill_detail()"""
    
    def test_get_skill_detail(self):
        """测试获取 skill 详情"""
        # 初始化配置
        api.initialize_config(str(self.temp_manager_dir))
        
        # 创建测试 skill（带 SKILL.md）
        skill_dir = self._create_test_skill("detail-skill")
        (skill_dir / "SKILL.md").write_text(
            "# Detail Skill\n\nThis is a test skill for detail view.",
            encoding="utf-8"
        )
        
        # 获取详情
        detail = api.get_skill_detail("detail-skill")
        
        self.assertIsNotNone(detail)
        self.assertEqual(detail['name'], "detail-skill")
        self.assertIn("skill_md_preview", detail)
        self.assertIn("Detail Skill", detail['skill_md_preview'])
        print(f"✅ API-12 PASS: 详情获取成功，包含 SKILL.md 预览")


def run_tests():
    """运行所有 L1 测试"""
    print("\n" + "="*60)
    print("L1: API 层单元测试")
    print("="*60 + "\n")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestAPI01ValidateSetupNotConfigured,
        TestAPI02ValidateSetupConfigured,
        TestAPI03InitializeConfigSuccess,
        TestAPI04InitializeConfigFailure,
        TestAPI05ListAvailableSkills,
        TestAPI06ListInstalledSkills,
        TestAPI07GenerateInstallPlan,
        TestAPI08GenerateUninstallPlan,
        TestAPI09InstallSkillSuccess,
        TestAPI10InstallSkillFailure,
        TestAPI11UninstallSkillSuccess,
        TestAPI12GetSkillDetail,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 统计
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print("\n" + "="*60)
    print(f"L1 测试结果: {passed}/{total} 通过")
    print("="*60)
    
    return result.wasSuccessful(), passed, total


if __name__ == "__main__":
    success, passed, total = run_tests()
    sys.exit(0 if success else 1)
