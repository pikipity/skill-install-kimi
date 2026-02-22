"""
验证器测试 - L1 代码测试
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
from skill_installer.src.validator import Validator, ValidationStatus, ValidationResult


class TestValidationResult(unittest.TestCase):
    """测试 ValidationResult 类"""
    
    def test_is_ok(self):
        """测试 is_ok 属性"""
        result = ValidationResult(status=ValidationStatus.OK, message='OK')
        self.assertTrue(result.is_ok)
        self.assertFalse(result.is_warning)
        self.assertFalse(result.is_error)
    
    def test_is_warning(self):
        """测试 is_warning 属性"""
        result = ValidationResult(status=ValidationStatus.WARNING, message='Warning')
        self.assertFalse(result.is_ok)
        self.assertTrue(result.is_warning)
        self.assertFalse(result.is_error)
    
    def test_is_error(self):
        """测试 is_error 属性"""
        result = ValidationResult(status=ValidationStatus.ERROR, message='Error')
        self.assertFalse(result.is_ok)
        self.assertFalse(result.is_warning)
        self.assertTrue(result.is_error)


class TestValidateSourceExists(unittest.TestCase):
    """测试验证源目录存在"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_source_exists(self):
        """测试源目录存在"""
        source = self.tmp_dir / 'skill'
        source.mkdir()
        
        result = Validator.validate_source_exists(source)
        
        self.assertTrue(result.is_ok)
        self.assertIn('存在', result.message)
    
    def test_source_not_exists(self):
        """测试源目录不存在"""
        source = self.tmp_dir / 'not_exist'
        
        result = Validator.validate_source_exists(source)
        
        self.assertTrue(result.is_error)
        self.assertIn('不存在', result.message)
        self.assertIsNotNone(result.suggestion)
    
    def test_source_is_file(self):
        """测试源路径是文件而非目录"""
        source = self.tmp_dir / 'file'
        source.write_text('content')
        
        result = Validator.validate_source_exists(source)
        
        self.assertTrue(result.is_error)
        self.assertIn('不是目录', result.message)


class TestValidateSkillStructure(unittest.TestCase):
    """测试验证 skill 结构"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_valid_structure(self):
        """测试有效结构"""
        skill = self.tmp_dir / 'skill'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('# Skill Description')
        
        result = Validator.validate_skill_structure(skill)
        
        self.assertTrue(result.is_ok)
    
    def test_missing_skill_md(self):
        """测试缺少 SKILL.md"""
        skill = self.tmp_dir / 'skill'
        skill.mkdir()
        
        result = Validator.validate_skill_structure(skill)
        
        self.assertTrue(result.is_error)
        self.assertIn('SKILL.md', result.message)
    
    def test_empty_skill_md(self):
        """测试空的 SKILL.md"""
        skill = self.tmp_dir / 'skill'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('')
        
        result = Validator.validate_skill_structure(skill)
        
        self.assertTrue(result.is_warning)
        self.assertIn('为空', result.message)


class TestValidateNotAlreadyInstalled(unittest.TestCase):
    """测试验证未安装"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_not_installed(self):
        """测试未安装"""
        symlink = self.tmp_dir / 'symlink'
        
        result = Validator.validate_not_already_installed(symlink)
        
        self.assertTrue(result.is_ok)
        self.assertIn('可用', result.message)
    
    def test_already_installed(self):
        """测试已安装"""
        symlink = self.tmp_dir / 'symlink'
        source = self.tmp_dir / 'source'
        source.mkdir()
        symlink.symlink_to(source)
        
        result = Validator.validate_not_already_installed(symlink)
        
        self.assertTrue(result.is_warning)
        self.assertIn('已安装', result.message)
    
    def test_target_is_regular_file(self):
        """测试目标是普通文件"""
        target = self.tmp_dir / 'file'
        target.write_text('content')
        
        result = Validator.validate_not_already_installed(target)
        
        self.assertTrue(result.is_error)
        self.assertIn('非软连接', result.message)


class TestValidateSymlinkReadable(unittest.TestCase):
    """测试验证软连接可读"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_valid_symlink(self):
        """测试有效软连接"""
        source = self.tmp_dir / 'source'
        source.mkdir()
        symlink = self.tmp_dir / 'symlink'
        symlink.symlink_to(source)
        
        result = Validator.validate_symlink_readable(symlink)
        
        self.assertTrue(result.is_ok)
        self.assertIn('可读', result.message)
    
    def test_broken_symlink(self):
        """测试损坏的软连接"""
        source = self.tmp_dir / 'source'
        source.mkdir()
        symlink = self.tmp_dir / 'symlink'
        symlink.symlink_to(source)
        
        # 删除源
        shutil.rmtree(source)
        
        result = Validator.validate_symlink_readable(symlink)
        
        self.assertTrue(result.is_error)
        self.assertIn('不存在', result.message)
    
    def test_not_symlink(self):
        """测试不是软连接"""
        target = self.tmp_dir / 'file'
        target.write_text('content')
        
        result = Validator.validate_symlink_readable(target)
        
        self.assertTrue(result.is_error)
        self.assertIn('不是软连接', result.message)


class TestValidateUninstallTarget(unittest.TestCase):
    """测试验证卸载目标"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    def test_valid_symlink(self):
        """测试有效软连接"""
        source = self.tmp_dir / 'source'
        source.mkdir()
        symlink = self.tmp_dir / 'symlink'
        symlink.symlink_to(source)
        
        result = Validator.validate_uninstall_target(symlink)
        
        self.assertTrue(result.is_ok)
    
    def test_not_installed(self):
        """测试未安装"""
        symlink = self.tmp_dir / 'symlink'
        
        result = Validator.validate_uninstall_target(symlink)
        
        self.assertTrue(result.is_error)
        self.assertIn('未安装', result.message)
    
    def test_regular_file(self):
        """测试是普通文件"""
        target = self.tmp_dir / 'file'
        target.write_text('content')
        
        result = Validator.validate_uninstall_target(target)
        
        self.assertTrue(result.is_warning)
        self.assertIn('不是软连接', result.message)


class TestRunPreInstallChecks(unittest.TestCase):
    """测试运行安装前检查"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        
        self.source = self.tmp_dir / 'skill'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('# Test')
        
        self.symlink = self.tmp_dir / 'symlink'
    
    def test_all_pass(self):
        """测试全部通过"""
        results = Validator.run_pre_install_checks(self.source, self.symlink)
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.is_ok for r in results))
    
    def test_source_not_exists(self):
        """测试源不存在"""
        results = Validator.run_pre_install_checks(
            self.tmp_dir / 'not_exist', self.symlink
        )
        
        self.assertTrue(Validator.has_errors(results))
    
    def test_has_errors_static(self):
        """测试 has_errors 静态方法"""
        results = [
            ValidationResult(ValidationStatus.OK, 'OK'),
            ValidationResult(ValidationStatus.ERROR, 'Error'),
        ]
        
        self.assertTrue(Validator.has_errors(results))
        self.assertFalse(Validator.has_warnings(results))
    
    def test_has_warnings_static(self):
        """测试 has_warnings 静态方法"""
        results = [
            ValidationResult(ValidationStatus.OK, 'OK'),
            ValidationResult(ValidationStatus.WARNING, 'Warning'),
        ]
        
        self.assertTrue(Validator.has_warnings(results))
        self.assertFalse(Validator.has_errors(results))
    
    def test_get_errors(self):
        """测试获取错误列表"""
        results = [
            ValidationResult(ValidationStatus.OK, 'OK'),
            ValidationResult(ValidationStatus.ERROR, 'Error 1'),
            ValidationResult(ValidationStatus.ERROR, 'Error 2'),
        ]
        
        errors = Validator.get_errors(results)
        self.assertEqual(len(errors), 2)
    
    def test_get_warnings(self):
        """测试获取警告列表"""
        results = [
            ValidationResult(ValidationStatus.OK, 'OK'),
            ValidationResult(ValidationStatus.WARNING, 'Warning 1'),
            ValidationResult(ValidationStatus.WARNING, 'Warning 2'),
        ]
        
        warnings = Validator.get_warnings(results)
        self.assertEqual(len(warnings), 2)


class TestRunPostInstallChecks(unittest.TestCase):
    """测试运行安装后检查"""
    
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir)
    
    @patch('skill_installer.src.validator.PlatformInfo')
    def test_all_pass(self, mock_platform):
        """测试全部通过"""
        # Mock PlatformInfo.get_skills_dir 返回临时目录
        skills_dir = self.tmp_dir / '.kimi' / 'skills'
        skills_dir.mkdir(parents=True)
        mock_platform.get_skills_dir.return_value = skills_dir
        
        source = self.tmp_dir / 'source'
        source.mkdir()
        (source / 'SKILL.md').write_text('# Test')
        
        # 在 mocked skills 目录创建软连接
        symlink = skills_dir / 'test-skill'
        symlink.symlink_to(source)
        
        results = Validator.run_post_install_checks(symlink, 'test-skill')
        
        self.assertTrue(all(r.is_ok for r in results))


if __name__ == '__main__':
    unittest.main(verbosity=2)
