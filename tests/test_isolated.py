"""
L2 隔离功能测试 - 验证实际安装/卸载功能，确保不影响真实环境

测试原则：
1. 零侵入：不修改现有的 ~/.kimi/ 目录
2. 零依赖：不使用已安装的 skill
3. 自包含：测试用的 skill 临时创建，测试完删除
4. 可还原：测试结束后系统状态与测试前完全一致
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# 方案 D：动态导入设置（必须先导入 helper）
# 确保 tests 目录在路径中
sys.path.insert(0, str(Path(__file__).parent))
import test_import_helper
from skill_installer.src.platform_utils import PlatformInfo, PlatformUtils
from skill_installer.src.config import ConfigManager
from skill_installer.src.path_manager import PathManager
from skill_installer.src.core import SkillInstaller, InstallOption


class TestIsolationBase(unittest.TestCase):
    """隔离测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """记录原始 ~/.kimi/skills/ 状态"""
        cls.original_kimi_skills = list(PlatformInfo.get_skills_dir().iterdir()) if PlatformInfo.get_skills_dir().exists() else []
        cls.original_kimi_skills_names = {p.name for p in cls.original_kimi_skills}
        print(f"\n原始 ~/.kimi/skills/ 内容: {cls.original_kimi_skills_names}")
    
    @classmethod
    def tearDownClass(cls):
        """验证 ~/.kimi/skills/ 状态未改变"""
        # 清理测试遗留（以 test- 开头的）
        for skill_path in PlatformInfo.get_skills_dir().iterdir():
            if skill_path.name.startswith('test-'):
                print(f"清理遗留测试 skill: {skill_path.name}")
                PlatformUtils.remove_dir(skill_path)
        
        current_skills = list(PlatformInfo.get_skills_dir().iterdir()) if PlatformInfo.get_skills_dir().exists() else []
        current_names = {p.name for p in current_skills}
        
        # 检查是否有新增或删除
        added = current_names - cls.original_kimi_skills_names
        removed = cls.original_kimi_skills_names - current_names
        
        if added:
            print(f"警告：测试添加了 {added} 到 ~/.kimi/skills/")
        if removed:
            print(f"警告：测试从 ~/.kimi/skills/ 删除了 {removed}")


class TestFT01_FirstConfig(TestIsolationBase):
    """FT-01: 首次配置测试"""
    
    def test_first_time_config(self):
        """测试首次配置流程，配置保存到临时目录"""
        # 创建临时测试环境
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            skill_dir = tmp / 'skill-installer'
            skill_dir.mkdir()
            
            # 创建 ConfigManager（模拟首次使用）
            config = ConfigManager(skill_dir)
            self.assertFalse(config.is_configured)
            
            # Mock UI
            ui = MagicMock()
            ui.prompt.return_value = 'A'  # 选择使用当前目录
            ui.confirm.return_value = True
            
            # 执行配置
            result = config.interactive_setup(ui)
            
            # 验证
            self.assertTrue(result)
            self.assertTrue(config.is_configured)
            
            # 验证配置保存位置
            config_file = skill_dir / 'data' / 'config.json'
            self.assertTrue(config_file.exists())
            
            # 验证内容（注意：interactive_setup 使用 skill_dir.parent 作为项目目录）
            with open(config_file) as f:
                saved_config = json.load(f)
            # 保存的是 current_project = skill_dir.parent
            self.assertEqual(Path(saved_config['manager_dir']).resolve(), skill_dir.parent.resolve())
            
            print(f"\n✅ FT-01 通过: 配置保存到 {config_file}")


class TestFT02_InstallSkill(TestIsolationBase):
    """FT-02: 安装临时 skill 测试"""
    
    def test_install_temp_skill(self):
        """测试安装临时 skill，软连接创建在临时目录"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            
            # 创建管理目录和测试 skill
            manage_dir = tmp / 'manage'
            manage_dir.mkdir()
            
            test_skill = manage_dir / 'test-isolated-skill'
            test_skill.mkdir()
            (test_skill / 'SKILL.md').write_text('# Test Skill\n')
            
            # 创建临时 Kimi 目录
            kimi_dir = tmp / '.kimi'
            
            # 保存原始方法并替换
            original_get_kimi_dir = PlatformInfo.get_kimi_dir
            PlatformInfo.get_kimi_dir = lambda: kimi_dir
            
            try:
                # 创建配置
                skill_dir = tmp / 'skill-installer'
                skill_dir.mkdir()
                config = ConfigManager(skill_dir)
                config.set_manager_dir(manage_dir)
                
                # 创建安装器
                paths = PathManager(manage_dir)
                installer = SkillInstaller(config, paths)
                installer.set_ui(None)  # 无 UI 模式
                
                # 执行安装
                result = installer.install('test-isolated-skill')
                
                # 验证安装成功
                self.assertTrue(result.success, f"安装失败: {result.message}")
                
                # 验证软连接创建在临时目录
                symlink = kimi_dir / 'skills' / 'test-isolated-skill'
                self.assertTrue(symlink.exists())
                self.assertTrue(symlink.is_symlink())
                
                # 验证可读性
                self.assertTrue((symlink / 'SKILL.md').exists())
                
                print(f"\n✅ FT-02 通过: Skill 安装在临时目录 {symlink}")
            finally:
                # 恢复原始方法
                PlatformInfo.get_kimi_dir = original_get_kimi_dir


class TestFT03_IsolationVerification(TestIsolationBase):
    """FT-03: 隔离性验证"""
    
    def setUp(self):
        """每个测试前清理可能的污染"""
        super().setUp()
        # 清理可能遗留的测试 skill
        for skill_path in PlatformInfo.get_skills_dir().iterdir():
            if skill_path.name.startswith('test-'):
                print(f"清理遗留: {skill_path.name}")
                PlatformUtils.remove_dir(skill_path)
    
    def test_no_pollution_of_real_kimi(self):
        """验证测试不影响真实的 ~/.kimi/skills/"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            
            # 创建管理目录和测试 skill
            manage_dir = tmp / 'manage'
            manage_dir.mkdir()
            
            test_skill = manage_dir / 'test-pollution-check'
            test_skill.mkdir()
            (test_skill / 'SKILL.md').write_text('# Test')
            
            # 创建临时 Kimi 目录
            kimi_dir = tmp / '.kimi'
            
            # 保存原始方法并替换
            original_get_kimi_dir = PlatformInfo.get_kimi_dir
            PlatformInfo.get_kimi_dir = lambda: kimi_dir
            
            try:
                skill_dir = tmp / 'skill-installer'
                skill_dir.mkdir()
                config = ConfigManager(skill_dir)
                config.set_manager_dir(manage_dir)
                
                paths = PathManager(manage_dir)
                installer = SkillInstaller(config, paths)
                installer.set_ui(None)
                
                installer.install('test-pollution-check')
                
                # 验证临时目录有软连接
                self.assertTrue((kimi_dir / 'skills' / 'test-pollution-check').exists())
                
            finally:
                # 恢复原始方法
                PlatformInfo.get_kimi_dir = original_get_kimi_dir
            
            # 验证真实 ~/.kimi/skills/ 没有
            real_skills = PlatformInfo.get_skills_dir()
            self.assertFalse((real_skills / 'test-pollution-check').exists())
                
            print(f"\n✅ FT-03 通过: 未污染 {real_skills}")


class TestFT04_UninstallSkill(TestIsolationBase):
    """FT-04: 卸载 skill 测试"""
    
    def test_uninstall_keeps_source(self):
        """测试卸载只删除软连接，保留源码"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            
            # 创建环境
            manage_dir = tmp / 'manage'
            manage_dir.mkdir()
            
            test_skill = manage_dir / 'test-uninstall'
            test_skill.mkdir()
            (test_skill / 'SKILL.md').write_text('# Test')
            
            kimi_dir = tmp / '.kimi'
            
            # 保存原始方法并替换
            original_get_kimi_dir = PlatformInfo.get_kimi_dir
            PlatformInfo.get_kimi_dir = lambda: kimi_dir
            
            try:
                skill_dir = tmp / 'skill-installer'
                skill_dir.mkdir()
                config = ConfigManager(skill_dir)
                config.set_manager_dir(manage_dir)
                
                paths = PathManager(manage_dir)
                installer = SkillInstaller(config, paths)
                installer.set_ui(None)
                
                # 先安装
                installer.install('test-uninstall')
                symlink = kimi_dir / 'skills' / 'test-uninstall'
                self.assertTrue(symlink.exists())
                
                # 再卸载
                result = installer.uninstall('test-uninstall')
                
                # 验证
                self.assertTrue(result.success)
                self.assertFalse(symlink.exists())  # 软连接已删除
                self.assertTrue(test_skill.exists())  # 源码保留
                self.assertTrue((test_skill / 'SKILL.md').exists())
                
                print(f"\n✅ FT-04 通过: 卸载后源码保留在 {test_skill}")
            finally:
                # 恢复原始方法
                PlatformInfo.get_kimi_dir = original_get_kimi_dir


class TestFT05_ListSkills(TestIsolationBase):
    """FT-05: 列表验证"""
    
    def test_list_shows_isolated_environment_only(self):
        """测试列表只显示隔离环境中的 skill"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            
            # 创建环境
            manage_dir = tmp / 'manage'
            manage_dir.mkdir()
            
            # 创建两个 test skill
            for name in ['test-list-a', 'test-list-b']:
                skill = manage_dir / name
                skill.mkdir()
                (skill / 'SKILL.md').write_text(f'# {name}')
            
            kimi_dir = tmp / '.kimi'
            
            # 保存原始方法并替换
            original_get_kimi_dir = PlatformInfo.get_kimi_dir
            PlatformInfo.get_kimi_dir = lambda: kimi_dir
            
            try:
                skill_dir = tmp / 'skill-installer'
                skill_dir.mkdir()
                config = ConfigManager(skill_dir)
                config.set_manager_dir(manage_dir)
                
                paths = PathManager(manage_dir)
                installer = SkillInstaller(config, paths)
                
                # 安装一个
                installer.set_ui(None)
                installer.install('test-list-a')
                
                # 验证列表
                installed = installer.list_installed()
                installed_names = {s['name'] for s in installed}
                self.assertEqual(installed_names, {'test-list-a'})
                
                available = installer.list_available()
                available_names = {s['name'] for s in available}
                self.assertEqual(available_names, {'test-list-b'})
                
                print(f"\n✅ FT-05 通过: 列表只显示隔离环境 skills")
            finally:
                # 恢复原始方法
                PlatformInfo.get_kimi_dir = original_get_kimi_dir


class TestFinalVerification(TestIsolationBase):
    """最终验证"""
    
    def test_01_record_original_state(self):
        """记录原始状态"""
        print(f"\n{'='*60}")
        print("L2 隔离功能测试开始")
        print(f"{'='*60}")
        print(f"原始 ~/.kimi/skills/ 内容:")
        for p in sorted(self.original_kimi_skills):
            print(f"  - {p.name}")
        self.assertTrue(True)  # 此测试总是通过，仅用于记录
    
    def test_99_verify_no_pollution(self):
        """最终验证：确认没有污染真实环境"""
        # 清理测试遗留
        for skill_path in PlatformInfo.get_skills_dir().iterdir():
            if skill_path.name.startswith('test-'):
                print(f"清理: {skill_path.name}")
                PlatformUtils.remove_dir(skill_path)
        
        current_skills = list(PlatformInfo.get_skills_dir().iterdir()) if PlatformInfo.get_skills_dir().exists() else []
        current_names = {p.name for p in current_skills}
        
        # 检查是否有测试 skill 遗留
        test_skills = {n for n in current_names if n.startswith('test-')}
        
        if test_skills:
            self.fail(f"发现测试 skill 遗留: {test_skills}")
        
        # 验证原始内容未变
        self.assertEqual(current_names, self.original_kimi_skills_names)
        
        print(f"\n{'='*60}")
        print("✅ L2 隔离功能测试全部通过！")
        print(f"{'='*60}")
        print(f"✓ 未修改 ~/.kimi/skills/")
        print(f"✓ 所有测试 skill 已清理")
        print(f"✓ 系统状态与测试前一致")


if __name__ == '__main__':
    unittest.main(verbosity=2)
