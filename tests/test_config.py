"""
配置管理测试 - L1 代码测试
"""

import unittest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# 方案 D：动态导入设置（必须先导入 helper）
# 确保 tests 目录在路径中
sys.path.insert(0, str(Path(__file__).parent))
import test_import_helper
from skill_installer.src.config import ConfigManager, ConfigError, ConfigValidationError


class TestConfigManager(unittest.TestCase):
    """测试 ConfigManager 类"""
    
    def setUp(self):
        """创建临时目录"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        # 模拟 skill-installer 目录结构
        self.skill_dir = self.tmp_dir / 'skill-installer'
        self.skill_dir.mkdir()
        
        self.config_manager = ConfigManager(self.skill_dir)
    
    def test_init_default_path(self):
        """测试默认路径初始化"""
        cm = ConfigManager()
        # 应该指向 skill-installer 目录
        self.assertTrue(str(cm.skill_dir).endswith('skill-installer'))
    
    def test_init_custom_path(self):
        """测试自定义路径初始化"""
        cm = ConfigManager(self.skill_dir)
        self.assertEqual(cm.skill_dir.resolve(), self.skill_dir.resolve())
        self.assertEqual(cm.data_dir, cm.skill_dir / 'data')
        self.assertEqual(cm.config_file, cm.data_dir / 'config.json')
    
    def test_is_configured_false(self):
        """测试未配置状态"""
        self.assertFalse(self.config_manager.is_configured)
    
    def test_is_configured_true(self):
        """测试已配置状态"""
        # 创建配置文件
        self.config_manager.data_dir.mkdir(exist_ok=True)
        config = {'manager_dir': str(self.tmp_dir), 'version': '1.0'}
        self.config_manager.config_file.write_text(json.dumps(config))
        
        self.assertTrue(self.config_manager.is_configured)
    
    def test_load_not_exists(self):
        """测试加载不存在的配置"""
        with self.assertRaises(ConfigError) as ctx:
            self.config_manager.load()
        self.assertIn('不存在', str(ctx.exception))
    
    def test_load_invalid_json(self):
        """测试加载无效 JSON"""
        self.config_manager.data_dir.mkdir(exist_ok=True)
        self.config_manager.config_file.write_text('invalid json')
        
        with self.assertRaises(ConfigError) as ctx:
            self.config_manager.load()
        self.assertIn('格式错误', str(ctx.exception))
    
    def test_save_and_load(self):
        """测试保存和加载配置"""
        config = {
            'manager_dir': str(self.tmp_dir),
            'platform': 'macos',
            'first_config_time': '2024-01-01T00:00:00'
        }
        
        self.config_manager.save(config)
        
        # 验证文件创建
        self.assertTrue(self.config_manager.config_file.exists())
        
        # 验证内容
        loaded = self.config_manager.load()
        self.assertEqual(loaded['manager_dir'], str(self.tmp_dir))
        self.assertEqual(loaded['version'], '1.0')  # 自动添加版本
    
    def test_validate_missing_manager_dir(self):
        """测试缺少 manager_dir 的验证"""
        config = {'platform': 'macos'}
        valid, error = self.config_manager.validate(config)
        self.assertFalse(valid)
        self.assertIn('manager_dir', error)
    
    def test_validate_not_absolute_path(self):
        """测试非绝对路径验证"""
        config = {'manager_dir': 'relative/path'}
        valid, error = self.config_manager.validate(config)
        self.assertFalse(valid)
        self.assertIn('绝对路径', error)
    
    def test_validate_not_exists(self):
        """测试不存在的目录验证"""
        config = {'manager_dir': '/not/exist/path'}
        valid, error = self.config_manager.validate(config)
        self.assertFalse(valid)
        self.assertIn('不存在', error)
    
    def test_validate_valid(self):
        """测试有效配置验证"""
        config = {'manager_dir': str(self.tmp_dir)}
        valid, error = self.config_manager.validate(config)
        self.assertTrue(valid)
        self.assertEqual(error, '')
    
    def test_get_manager_dir_not_loaded(self):
        """测试未加载时获取管理目录"""
        # 先保存一个有效配置
        self.config_manager.save({'manager_dir': str(self.tmp_dir)})
        
        # 新的实例，未显式 load
        cm = ConfigManager(self.skill_dir)
        path = cm.get_manager_dir()
        self.assertEqual(path, self.tmp_dir)
    
    def test_set_manager_dir(self):
        """测试设置管理目录"""
        self.config_manager.set_manager_dir(self.tmp_dir)
        
        # 验证配置保存
        self.assertTrue(self.config_manager.config_file.exists())
        
        loaded = self.config_manager.load()
        self.assertEqual(Path(loaded['manager_dir']).resolve(), self.tmp_dir.resolve())
        self.assertIn('first_config_time', loaded)
        self.assertIn('platform', loaded)
    
    def test_set_manager_dir_not_absolute(self):
        """测试设置不存在的路径"""
        with self.assertRaises(ConfigValidationError) as ctx:
            self.config_manager.set_manager_dir('/not/exist/path')
        self.assertIn('不存在', str(ctx.exception))
    
    def test_set_manager_dir_not_exists(self):
        """测试设置不存在的目录"""
        with self.assertRaises(ConfigValidationError) as ctx:
            self.config_manager.set_manager_dir('/not/exist')
        self.assertIn('不存在', str(ctx.exception))
    
    def test_reset(self):
        """测试重置配置"""
        # 先创建配置
        self.config_manager.save({'manager_dir': str(self.tmp_dir)})
        self.assertTrue(self.config_manager.config_file.exists())
        
        # 重置
        self.config_manager.reset()
        self.assertFalse(self.config_manager.config_file.exists())
        self.assertIsNone(self.config_manager._config)
    
    def test_get_config_info_not_configured(self):
        """测试获取未配置时的信息"""
        info = self.config_manager.get_config_info()
        
        self.assertEqual(Path(info['skill_dir']).resolve(), self.skill_dir.resolve())
        self.assertEqual(info['is_configured'], False)
        self.assertIn('config_file', info)
    
    def test_get_config_info_configured(self):
        """测试获取已配置时的信息"""
        self.config_manager.set_manager_dir(self.tmp_dir)
        
        info = self.config_manager.get_config_info()
        
        self.assertEqual(info['is_configured'], True)
        self.assertEqual(Path(info['manager_dir']).resolve(), self.tmp_dir.resolve())
        self.assertIn('platform', info)
        self.assertIn('first_config_time', info)
        self.assertIn('version', info)


class TestInteractiveSetup(unittest.TestCase):
    """测试交互式配置"""
    
    def setUp(self):
        """创建临时目录"""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        self.skill_dir = self.tmp_dir / 'skill-installer'
        self.skill_dir.mkdir()
        
        self.config_manager = ConfigManager(self.skill_dir)
        
        # Mock UI
        self.ui = MagicMock()
    
    def test_interactive_setup_select_current(self):
        """测试选择当前目录作为管理目录"""
        # 确保未配置状态
        if self.config_manager.is_configured:
            self.config_manager.reset()
        
        # 模拟用户选择 A（使用当前目录）并确认 Y
        self.ui.prompt.return_value = 'A'
        self.ui.confirm.return_value = True
        
        result = self.config_manager.interactive_setup(self.ui)
        
        self.assertTrue(result)
        self.assertTrue(self.config_manager.is_configured)
        
        # 验证 UI 调用（至少有一次是初始配置）
        calls = [call for call in self.ui.print_header.call_args_list 
                 if call[0][0] == '⚙️ 初始配置']
        self.assertTrue(len(calls) > 0, "应该显示初始配置标题")
        self.ui.confirm.assert_called_with('是否确认？', default=True)
    
    def test_interactive_setup_cancel(self):
        """测试配置时取消确认"""
        self.ui.prompt.return_value = 'A'
        self.ui.confirm.return_value = False
        
        result = self.config_manager.interactive_setup(self.ui)
        
        self.assertFalse(result)
        self.assertFalse(self.config_manager.is_configured)
    
    def test_interactive_confirm_continue(self):
        """测试确认继续使用当前配置"""
        # 先设置配置
        self.config_manager.set_manager_dir(self.tmp_dir)
        
        self.ui.prompt.return_value = 'Y'
        
        result = self.config_manager.interactive_confirm(self.ui)
        
        self.assertTrue(result)
        # 配置应该还在
        self.assertTrue(self.config_manager.is_configured)
    
    def test_interactive_confirm_reset(self):
        """测试选择更换配置"""
        # 先设置配置
        self.config_manager.set_manager_dir(self.tmp_dir)
        
        # 先选择 N（更换），然后选择 A（使用当前）并确认
        self.ui.prompt.side_effect = ['N', 'A']
        self.ui.confirm.return_value = True
        
        result = self.config_manager.interactive_confirm(self.ui)
        
        self.assertTrue(result)
        self.assertTrue(self.config_manager.is_configured)
    
    def test_interactive_confirm_invalid_config(self):
        """测试配置无效时重新配置"""
        # 创建无效配置（缺少 manager_dir）
        self.config_manager.save({'invalid': 'config'})
        
        self.ui.prompt.return_value = 'A'
        self.ui.confirm.return_value = True
        
        result = self.config_manager.interactive_confirm(self.ui)
        
        self.assertTrue(result)
        self.ui.print_warning.assert_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
