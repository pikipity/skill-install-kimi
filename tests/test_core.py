"""
核心逻辑测试 - L1 代码测试
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# 方案 D：动态导入设置（必须先导入 helper）
sys.path.insert(0, str(Path(__file__).parent))
import test_import_helper
from skill_installer.src.core import (
    SkillInstaller, InstallOption,
    InstallResult, UninstallResult
)
from skill_installer.src.config import ConfigManager
from skill_installer.src.path_manager import PathManager
from skill_installer.src.platform_utils import PlatformInfo


class TestInstallResult(unittest.TestCase):
    """测试 InstallResult 类"""
    
    def test_format_display_success(self):
        """测试成功结果格式化"""
        result = InstallResult(
            success=True,
            skill_name='test-skill',
            symlink_path=Path('~/.kimi/skills/test-skill'),
            message='安装成功'
        )
        
        display = result.format_display()
        
        self.assertIn('✅', display)
        self.assertIn('test-skill', display)
    
    def test_format_display_failure(self):
        """测试失败结果格式化"""
        result = InstallResult(
            success=False,
            skill_name='test-skill',
            symlink_path=Path('~/.kimi/skills/test-skill'),
            message='安装失败原因'
        )
        
        display = result.format_display()
        
        self.assertIn('❌', display)
        self.assertIn('安装失败原因', display)


class TestUninstallResult(unittest.TestCase):
    """测试 UninstallResult 类"""
    
    def test_format_display_success(self):
        """测试成功结果格式化"""
        result = UninstallResult(
            success=True,
            skill_name='test-skill',
            deleted_symlink=Path('~/.kimi/skills/test-skill'),
            preserved_paths=[Path('/manage/test-skill')],
            delete_commands={'source': "rm -rf '/manage/test-skill'"}
        )
        
        display = result.format_display()
        
        self.assertIn('✅', display)
        self.assertIn('已删除软连接', display)


class TestSkillInstaller(unittest.TestCase):
    """测试 SkillInstaller 类"""
    
    def setUp(self):
        """创建临时目录结构"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        # 创建管理目录
        self.manager_dir = self.tmp_dir / 'manage'
        self.manager_dir.mkdir()
        
        # 创建测试 skill
        self.test_skill = self.manager_dir / 'test-skill'
        self.test_skill.mkdir()
        (self.test_skill / 'SKILL.md').write_text('# Test Skill')
        
        # 创建 Kimi 目录
        self.kimi_dir = self.tmp_dir / '.kimi'
        self.skills_dir = self.kimi_dir / 'skills'
        
        # 创建配置
        self.config = MagicMock(spec=ConfigManager)
        self.config.get_manager_dir.return_value = self.manager_dir
        
        # 创建路径管理器
        with patch.object(PlatformInfo, 'get_kimi_dir', return_value=self.kimi_dir):
            self.paths = PathManager(self.manager_dir)
            self.installer = SkillInstaller(self.config, self.paths)
    
    def test_install_source_not_exists(self):
        """测试安装不存在的 skill"""
        result = self.installer.install('not-exist')
        
        self.assertFalse(result.success)
        self.assertIn('不存在', result.message)
    
    def test_list_installed_empty(self):
        """测试列出空的已安装列表"""
        installed = self.installer.list_installed()
        
        self.assertEqual(installed, [])
    
    def test_list_available(self):
        """测试列出可安装的 skills"""
        available = self.installer.list_available()
        
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]['name'], 'test-skill')
    
    def test_get_skill_info_exists(self):
        """测试获取存在的 skill 信息"""
        info = self.installer.get_skill_info('test-skill')
        
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], 'test-skill')
        self.assertIn('skill_md_preview', info)
    
    def test_get_skill_info_not_exists(self):
        """测试获取不存在的 skill 信息"""
        info = self.installer.get_skill_info('not-exist')
        
        self.assertIsNone(info)
    
    def test_uninstall_not_installed(self):
        """测试卸载未安装的 skill"""
        result = self.installer.uninstall('not-installed')
        
        self.assertFalse(result.success)
        self.assertIn('未安装', result.message)


class TestInstallOption(unittest.TestCase):
    """测试 InstallOption 枚举"""
    
    def test_options(self):
        """测试选项值"""
        self.assertEqual(InstallOption.FULL.value, 'full')
        self.assertEqual(InstallOption.LIGHT.value, 'light')
        self.assertEqual(InstallOption.CLONE_ONLY.value, 'clone-only')


if __name__ == '__main__':
    unittest.main(verbosity=2)
