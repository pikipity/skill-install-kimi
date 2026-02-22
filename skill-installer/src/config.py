"""
配置管理器 - 读写 skill-installer/data/config.json

注意：本模块不包含任何 UI 交互代码。
交互式配置引导已移至 cli_ui.py 的 ConfigSetupUI 类。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .platform_utils import PlatformInfo, PlatformUtils


class ConfigError(Exception):
    """配置相关错误"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass


class ConfigManager:
    """
    配置管理器
    
    配置文件位置: skill-installer/data/config.json
    首次使用前不存在，首次运行时创建
    
    注意：交互式配置引导已移至 cli_ui.ConfigSetupUI
    """
    
    CONFIG_FILENAME = "config.json"
    DATA_DIRNAME = "data"
    CONFIG_VERSION = "1.0"
    
    def __init__(self, skill_dir: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            skill_dir: skill-installer 目录路径，默认为当前文件所在目录的父目录
        """
        if skill_dir is None:
            # 默认: src/config.py -> skill-installer/
            self.skill_dir = Path(__file__).parent.parent.resolve()
        else:
            self.skill_dir = Path(skill_dir).resolve()
        
        self.data_dir = self.skill_dir / self.DATA_DIRNAME
        self.config_file = self.data_dir / self.CONFIG_FILENAME
        
        # 启动时清理无效的配置文件
        self._cleanup_invalid_config()
        
        self._config: Optional[Dict[str, Any]] = None
    
    def _cleanup_invalid_config(self) -> bool:
        """
        清理无效的配置文件（空文件或无法访问的文件）
        
        Returns:
            是否执行了清理
        """
        if not self.config_file.exists():
            return False
        
        # 检查文件是否为空或无法访问
        try:
            if self.config_file.stat().st_size == 0:
                self.config_file.unlink()
                return True
        except (OSError, IOError):
            # 无法访问文件，尝试删除
            try:
                self.config_file.unlink()
                return True
            except (OSError, IOError):
                pass
        
        return False
    
    @property
    def is_configured(self) -> bool:
        """是否已配置（配置文件存在且有效）"""
        # 先清理无效文件
        self._cleanup_invalid_config()
        return self.config_file.exists()
    
    def load(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            配置字典
        
        Raises:
            ConfigError: 配置文件不存在或格式错误
        """
        if not self.config_file.exists():
            raise ConfigError(f"配置文件不存在: {self.config_file}")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            return self._config
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}")
    
    def save(self, config: Dict[str, Any]) -> None:
        """
        保存配置
        
        Args:
            config: 配置字典
        """
        # 确保 data 目录存在
        PlatformUtils.ensure_dir(self.data_dir)
        
        # 添加版本信息
        config['version'] = self.CONFIG_VERSION
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._config = config
        except Exception as e:
            raise ConfigError(f"保存配置文件失败: {e}")
    
    def validate(self, config: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
        """
        验证配置有效性
        
        Args:
            config: 要验证的配置，默认为已加载的配置
        
        Returns:
            (是否有效, 错误信息)
        """
        if config is None:
            config = self._config
        
        if config is None:
            return False, "配置未加载"
        
        # 检查必需字段
        required_fields = ['manager_dir']
        for field in required_fields:
            if field not in config:
                return False, f"缺少必需字段: {field}"
        
        # 验证管理目录
        manager_dir = Path(config['manager_dir'])
        
        # 检查是否为绝对路径
        if not manager_dir.is_absolute():
            return False, f"管理目录必须是绝对路径: {manager_dir}"
        
        # 检查目录是否存在
        if not manager_dir.exists():
            return False, f"管理目录不存在: {manager_dir}"
        
        # 检查是否有写入权限
        if not os.access(manager_dir, os.W_OK):
            return False, f"没有管理目录的写入权限: {manager_dir}"
        
        return True, ""
    
    def get_manager_dir(self) -> Path:
        """
        获取管理目录路径
        
        Returns:
            管理目录的 Path 对象
        
        Raises:
            ConfigError: 配置未加载或无效
        """
        if self._config is None:
            self.load()
        
        valid, error = self.validate()
        if not valid:
            raise ConfigValidationError(error)
        
        return Path(self._config['manager_dir'])
    
    def set_manager_dir(self, path: Path) -> None:
        """
        设置管理目录
        
        Args:
            path: 管理目录路径（必须是绝对路径）
        
        Raises:
            ConfigValidationError: 路径无效
        """
        path = Path(path).resolve()
        
        # 验证
        if not path.is_absolute():
            raise ConfigValidationError(f"必须是绝对路径: {path}")
        
        if not path.exists():
            raise ConfigValidationError(f"目录不存在: {path}")
        
        if not os.access(path, os.W_OK):
            raise ConfigValidationError(f"没有写入权限: {path}")
        
        # 更新配置
        if self._config is None:
            self._config = {}
        
        self._config['manager_dir'] = str(path)
        self._config['platform'] = PlatformInfo.get_system()
        self._config['first_config_time'] = datetime.now().isoformat()
        
        self.save(self._config)
    
    def reset(self) -> None:
        """重置配置（删除配置文件）"""
        if self.config_file.exists():
            self.config_file.unlink()
        self._config = None
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息摘要
        
        Returns:
            包含配置信息的字典
        """
        info = {
            'skill_dir': str(self.skill_dir),
            'config_file': str(self.config_file),
            'is_configured': self.is_configured,
        }
        
        if self.is_configured:
            try:
                config = self.load()
                info['manager_dir'] = config.get('manager_dir', 'N/A')
                info['platform'] = config.get('platform', 'N/A')
                info['first_config_time'] = config.get('first_config_time', 'N/A')
                info['version'] = config.get('version', 'N/A')
                
                valid, error = self.validate()
                info['is_valid'] = valid
                if not valid:
                    info['validation_error'] = error
            except ConfigError as e:
                info['error'] = str(e)
        
        return info
    
    # 注意：交互式方法已移至 cli_ui.ConfigSetupUI
    # - interactive_setup(ui) -> cli_ui.ConfigSetupUI.interactive_setup(config)
    # - interactive_confirm(ui) -> cli_ui.ConfigSetupUI.interactive_confirm(config)


# 便捷函数

def get_default_config_manager() -> ConfigManager:
    """获取默认配置管理器实例"""
    return ConfigManager()
