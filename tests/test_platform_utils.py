"""
跨平台工具测试 - L1 代码测试
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 方案 D：动态导入设置（必须先导入 helper）
# 确保 tests 目录在路径中
sys.path.insert(0, str(Path(__file__).parent))
import test_import_helper
from skill_installer.src.platform_utils import (
    PlatformInfo, PlatformUtils, SymlinkManager,
    DeleteCommandGenerator, get_platform, is_windows, is_macos, is_linux
)


class TestPlatformInfo(unittest.TestCase):
    """测试 PlatformInfo 类"""
    
    def test_get_system(self):
        """测试获取系统类型"""
        system = PlatformInfo.get_system()
        self.assertIn(system, ['macos', 'linux', 'windows'])
    
    def test_is_methods_consistency(self):
        """测试各 is_ 方法的一致性"""
        system = PlatformInfo.get_system()
        
        if system == 'windows':
            self.assertTrue(PlatformInfo.is_windows())
            self.assertFalse(PlatformInfo.is_macos())
            self.assertFalse(PlatformInfo.is_linux())
            self.assertFalse(PlatformInfo.is_unix_like())
        elif system == 'macos':
            self.assertFalse(PlatformInfo.is_windows())
            self.assertTrue(PlatformInfo.is_macos())
            self.assertFalse(PlatformInfo.is_linux())
            self.assertTrue(PlatformInfo.is_unix_like())
        else:  # linux
            self.assertFalse(PlatformInfo.is_windows())
            self.assertFalse(PlatformInfo.is_macos())
            self.assertTrue(PlatformInfo.is_linux())
            self.assertTrue(PlatformInfo.is_unix_like())
    
    def test_get_home_dir(self):
        """测试获取家目录"""
        home = PlatformInfo.get_home_dir()
        self.assertIsInstance(home, Path)
        self.assertTrue(home.is_absolute())
        self.assertTrue(home.exists())
    
    def test_get_kimi_dir(self):
        """测试获取 Kimi 配置目录"""
        kimi_dir = PlatformInfo.get_kimi_dir()
        self.assertIsInstance(kimi_dir, Path)
        # 应该是 ~/.kimi
        self.assertTrue(str(kimi_dir).endswith('.kimi'))
    
    def test_get_skills_dir(self):
        """测试获取 skills 目录"""
        skills_dir = PlatformInfo.get_skills_dir()
        self.assertIsInstance(skills_dir, Path)
        # 应该是 ~/.kimi/skills
        self.assertIn('skills', str(skills_dir))
    
    def test_get_shell(self):
        """测试获取 shell 类型"""
        shell = PlatformInfo.get_shell()
        self.assertIn(shell, ['powershell', 'zsh', 'bash', 'sh'])


class TestPlatformUtils(unittest.TestCase):
    """测试 PlatformUtils 类"""
    
    def test_normalize_path(self):
        """测试路径规范化"""
        # 测试展开 ~
        expanded = PlatformUtils.normalize_path('~/test')
        self.assertFalse(expanded.startswith('~'))
        self.assertTrue(expanded.startswith(str(Path.home())))
    
    def test_to_posix_path(self):
        """测试转换为 POSIX 路径"""
        if os.sep == '\\':  # Windows
            posix = PlatformUtils.to_posix_path('C:\\Users\\test')
            self.assertEqual(posix, 'C:/Users/test')
        else:
            posix = PlatformUtils.to_posix_path('/home/user/test')
            self.assertEqual(posix, '/home/user/test')
    
    def test_calculate_relative_path(self):
        """测试相对路径计算"""
        # 模拟：source = /a/b/c, symlink = /d/e/f
        # 相对路径应该是 ../../../a/b/c
        source = Path('/tmp/skill_installer_test/source/test_skill')
        symlink = Path('/tmp/skill_installer_test/kimi/skills/test_skill')
        
        rel = PlatformUtils.calculate_relative_path(source, symlink)
        self.assertIsInstance(rel, str)
        # 使用 / 分隔符
        self.assertNotIn('\\', rel)
    
    def test_ensure_dir(self):
        """测试确保目录存在"""
        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / 'test' / 'nested'
            result = PlatformUtils.ensure_dir(test_dir)
            self.assertTrue(test_dir.exists())
            self.assertEqual(result, test_dir)
    
    def test_remove_dir(self):
        """测试删除目录"""
        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / 'to_remove'
            test_dir.mkdir()
            (test_dir / 'file.txt').write_text('test')
            
            self.assertTrue(PlatformUtils.remove_dir(test_dir))
            self.assertFalse(test_dir.exists())


class TestSymlinkManager(unittest.TestCase):
    """测试 SymlinkManager 类"""
    
    def setUp(self):
        """创建临时目录"""
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_create_and_remove_symlink(self):
        """测试创建和删除软连接"""
        # 跳过 Windows（需要管理员权限）
        if PlatformInfo.is_windows():
            self.skipTest("Windows 创建软连接需要管理员权限")
        
        source = Path(self.tmp_dir) / 'source_dir'
        source.mkdir()
        (source / 'file.txt').write_text('test content')
        
        target = Path(self.tmp_dir) / 'symlink'
        
        # 创建软连接
        SymlinkManager.create_symlink(source, target)
        self.assertTrue(target.is_symlink())
        self.assertTrue(target.exists())
        
        # 验证内容可读
        self.assertEqual((target / 'file.txt').read_text(), 'test content')
        
        # 删除软连接
        self.assertTrue(SymlinkManager.remove_symlink(target))
        self.assertFalse(target.exists())
        self.assertTrue(source.exists())  # 源目录还在
    
    def test_is_symlink(self):
        """测试检查是否为软连接"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 创建软连接需要管理员权限")
        
        source = Path(self.tmp_dir) / 'source'
        source.mkdir()
        target = Path(self.tmp_dir) / 'link'
        
        self.assertFalse(SymlinkManager.is_symlink(target))
        
        SymlinkManager.create_symlink(source, target)
        self.assertTrue(SymlinkManager.is_symlink(target))
    
    def test_read_symlink(self):
        """测试读取软连接目标"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 创建软连接需要管理员权限")
        
        source = Path(self.tmp_dir) / 'source'
        source.mkdir()
        target = Path(self.tmp_dir) / 'link'
        
        SymlinkManager.create_symlink(source, target)
        
        read_target = SymlinkManager.read_symlink(target)
        self.assertIsNotNone(read_target)
        self.assertEqual(read_target.resolve(), source.resolve())
    
    def test_verify_symlink(self):
        """测试验证软连接有效性"""
        if PlatformInfo.is_windows():
            self.skipTest("Windows 创建软连接需要管理员权限")
        
        source = Path(self.tmp_dir) / 'source'
        source.mkdir()
        target = Path(self.tmp_dir) / 'link'
        
        # 未创建时验证失败
        self.assertFalse(SymlinkManager.verify_symlink(target))
        
        # 创建后验证通过
        SymlinkManager.create_symlink(source, target)
        self.assertTrue(SymlinkManager.verify_symlink(target))
        
        # 删除源后验证失败
        shutil.rmtree(source)
        self.assertFalse(SymlinkManager.verify_symlink(target))
    
    def test_create_symlink_source_not_exists(self):
        """测试源不存在时抛出异常"""
        source = Path(self.tmp_dir) / 'not_exist'
        target = Path(self.tmp_dir) / 'link'
        
        with self.assertRaises(FileNotFoundError):
            SymlinkManager.create_symlink(source, target)


class TestDeleteCommandGenerator(unittest.TestCase):
    """测试删除命令生成器"""
    
    def test_get_delete_command_dir_unix(self):
        """测试 Unix 目录删除命令"""
        if PlatformInfo.is_windows():
            self.skipTest("仅测试 Unix 格式")
        
        cmd = DeleteCommandGenerator.get_delete_command('/path/to/dir', 'dir')
        self.assertIn('rm -rf', cmd)
        self.assertIn('/path/to/dir', cmd)
    
    def test_get_delete_command_file_unix(self):
        """测试 Unix 文件删除命令"""
        if PlatformInfo.is_windows():
            self.skipTest("仅测试 Unix 格式")
        
        cmd = DeleteCommandGenerator.get_delete_command('/path/to/file', 'file')
        self.assertIn('rm -f', cmd)
        self.assertIn('/path/to/file', cmd)
    
    def test_get_delete_command_dir_windows(self):
        """测试 Windows 目录删除命令"""
        if not PlatformInfo.is_windows():
            self.skipTest("仅测试 Windows 格式")
        
        cmd = DeleteCommandGenerator.get_delete_command('C:\\path\\to\\dir', 'dir')
        self.assertIn('Remove-Item', cmd)
        self.assertIn('-Recurse', cmd)
    
    def test_get_rmdir_command(self):
        """测试获取目录删除命令"""
        cmd = DeleteCommandGenerator.get_rmdir_command('/test/path')
        self.assertIsInstance(cmd, str)
    
    def test_get_rmfile_command(self):
        """测试获取文件删除命令"""
        cmd = DeleteCommandGenerator.get_rmfile_command('/test/file')
        self.assertIsInstance(cmd, str)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def test_get_platform(self):
        """测试 get_platform"""
        platform = get_platform()
        self.assertIn(platform, ['macos', 'linux', 'windows'])
    
    def test_is_functions(self):
        """测试 is_* 函数"""
        # 确保只有一个返回 True
        results = [is_windows(), is_macos(), is_linux()]
        self.assertEqual(sum(results), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
