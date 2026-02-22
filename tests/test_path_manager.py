"""
路径管理测试 - L1 代码测试
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# 方案 D：动态导入设置（必须先导入 helper）
# 确保 tests 目录在路径中
sys.path.insert(0, str(Path(__file__).parent))
import test_import_helper
from skill_installer.src.path_manager import PathManager, PathManagerError
from skill_installer.src.platform_utils import PlatformInfo


class TestPathManager(unittest.TestCase):
    """测试 PathManager 类"""
    
    def setUp(self):
        """创建临时目录结构"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        # 创建模拟结构
        self.manager_dir = self.tmp_dir / 'manage'
        self.manager_dir.mkdir()
        
        self.kimi_dir = self.tmp_dir / '.kimi'
        self.skills_dir = self.kimi_dir / 'skills'
        
        # 创建测试 skill
        self.test_skill = self.manager_dir / 'test-skill'
        self.test_skill.mkdir()
        (self.test_skill / 'SKILL.md').write_text('# Test Skill')
        
        # 使用 patch 临时修改 Kimi 目录
        with patch.object(PlatformInfo, 'get_kimi_dir', return_value=self.kimi_dir):
            self.path_manager = PathManager(self.manager_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.path_manager.manager_dir.resolve(), self.manager_dir.resolve())
        # skills 目录应该被创建
        self.assertTrue(self.skills_dir.exists())
    
    def test_get_skill_source_path(self):
        """测试获取 skill 源路径"""
        path = self.path_manager.get_skill_source_path('test-skill')
        self.assertEqual(path.resolve(), (self.manager_dir / 'test-skill').resolve())
    
    def test_get_skill_symlink_path(self):
        """测试获取 skill 软连接路径"""
        path = self.path_manager.get_skill_symlink_path('test-skill')
        self.assertEqual(path, self.skills_dir / 'test-skill')
    
    def test_calculate_relative_symlink(self):
        """测试计算相对路径"""
        rel = self.path_manager.calculate_relative_symlink('test-skill')
        self.assertIsInstance(rel, str)
        self.assertNotIn('\\', rel)  # 使用 / 分隔符
    
    def test_validate_skill_source_valid(self):
        """测试验证有效的 skill 源"""
        valid, error = self.path_manager.validate_skill_source('test-skill')
        self.assertTrue(valid)
        self.assertEqual(error, '')
    
    def test_validate_skill_source_not_exists(self):
        """测试验证不存在的 skill 源"""
        valid, error = self.path_manager.validate_skill_source('not-exist')
        self.assertFalse(valid)
        self.assertIn('不存在', error)
    
    def test_validate_skill_source_no_skill_md(self):
        """测试验证缺少 SKILL.md 的 skill"""
        # 创建一个没有 SKILL.md 的目录
        (self.manager_dir / 'no-skill-md').mkdir()
        
        valid, error = self.path_manager.validate_skill_source('no-skill-md')
        self.assertFalse(valid)
        self.assertIn('SKILL.md', error)
    
    def test_is_skill_installed_false(self):
        """测试 skill 未安装"""
        self.assertFalse(self.path_manager.is_skill_installed('test-skill'))
    
    def test_get_installed_skills_empty(self):
        """测试获取空的已安装列表"""
        installed = self.path_manager.get_installed_skills()
        self.assertEqual(installed, [])
    
    def test_get_available_skills(self):
        """测试获取可安装的 skills"""
        available = self.path_manager.get_available_skills()
        self.assertIn('test-skill', available)
    
    def test_get_available_skills_exclude_installed(self):
        """测试已安装的 skill 不在可安装列表中"""
        # 创建一个已安装的软连接
        symlink = self.skills_dir / 'test-skill'
        if not PlatformInfo.is_windows():
            symlink.symlink_to(self.test_skill)
            
            available = self.path_manager.get_available_skills()
            self.assertNotIn('test-skill', available)
    
    def test_get_install_info(self):
        """测试获取安装信息"""
        info = self.path_manager.get_install_info('test-skill')
        
        self.assertEqual(info['name'], 'test-skill')
        self.assertEqual(Path(info['source_path']).resolve(), self.test_skill.resolve())
        self.assertEqual(info['symlink_path'], self.skills_dir / 'test-skill')
        self.assertTrue(info['source_exists'])
        self.assertTrue(info['source_valid'])
        self.assertFalse(info['is_installed'])
    
    def test_get_delete_commands(self):
        """测试获取删除命令"""
        cmds = self.path_manager.get_delete_commands('test-skill')
        
        self.assertIn('symlink', cmds)
        self.assertIn('source', cmds)
        self.assertIn('command', cmds['symlink'])
        self.assertIn('command', cmds['source'])


class TestSymlinkOperations(unittest.TestCase):
    """测试软连接操作（需要真实创建软连接）"""
    
    def setUp(self):
        """创建临时目录"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        self.manager_dir = self.tmp_dir / 'manage'
        self.manager_dir.mkdir()
        
        self.kimi_dir = self.tmp_dir / '.kimi'
        self.skills_dir = self.kimi_dir / 'skills'
        
        # 创建测试 skill
        self.test_skill = self.manager_dir / 'test-skill'
        self.test_skill.mkdir()
        (self.test_skill / 'SKILL.md').write_text('# Test Skill')
        
        with patch.object(PlatformInfo, 'get_kimi_dir', return_value=self.kimi_dir):
            self.path_manager = PathManager(self.manager_dir)
    
    def test_create_skill_symlink(self):
        """测试创建 skill 软连接"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        self.path_manager.create_skill_symlink('test-skill')
        
        symlink = self.skills_dir / 'test-skill'
        self.assertTrue(symlink.is_symlink())
        self.assertTrue(symlink.exists())
    
    def test_create_skill_symlink_already_installed(self):
        """测试重复安装抛出异常"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        self.path_manager.create_skill_symlink('test-skill')
        
        with self.assertRaises(PathManagerError) as ctx:
            self.path_manager.create_skill_symlink('test-skill')
        
        self.assertIn('已安装', str(ctx.exception))
    
    def test_create_skill_symlink_source_not_exists(self):
        """测试源不存在时抛出异常"""
        with self.assertRaises(PathManagerError) as ctx:
            self.path_manager.create_skill_symlink('not-exist')
        
        self.assertIn('不存在', str(ctx.exception))
    
    def test_remove_skill_symlink(self):
        """测试删除 skill 软连接"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        # 先创建
        self.path_manager.create_skill_symlink('test-skill')
        
        # 再删除
        result = self.path_manager.remove_skill_symlink('test-skill')
        self.assertTrue(result)
        
        symlink = self.skills_dir / 'test-skill'
        self.assertFalse(symlink.exists())
        
        # 源目录应该还在
        self.assertTrue(self.test_skill.exists())
    
    def test_remove_skill_symlink_not_installed(self):
        """测试删除未安装的 skill"""
        result = self.path_manager.remove_skill_symlink('not-installed')
        self.assertFalse(result)
    
    def test_is_skill_installed_true(self):
        """测试检查已安装的 skill"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        self.path_manager.create_skill_symlink('test-skill')
        
        self.assertTrue(self.path_manager.is_skill_installed('test-skill'))
    
    def test_verify_skill_symlink(self):
        """测试验证软连接有效性"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        self.path_manager.create_skill_symlink('test-skill')
        
        self.assertTrue(self.path_manager.verify_skill_symlink('test-skill'))
    
    def test_get_symlink_target(self):
        """测试获取软连接目标"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 需要管理员权限")
        
        self.path_manager.create_skill_symlink('test-skill')
        
        target = self.path_manager.get_symlink_target('test-skill')
        self.assertIsNotNone(target)
        self.assertEqual(target.resolve(), self.test_skill.resolve())


if __name__ == '__main__':
    unittest.main(verbosity=2)
