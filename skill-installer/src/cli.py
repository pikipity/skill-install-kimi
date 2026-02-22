"""
命令行接口 - 处理用户交互和命令分发
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List, Any

from .config import ConfigManager, ConfigError, ConfigValidationError
from .path_manager import PathManager
from .core import SkillInstaller, InstallResult, UninstallResult, InstallOption
from .platform_utils import PlatformInfo


class ConsoleUI:
    """
    控制台用户交互接口
    
    提供统一的交互方式，所有关键决策使用 [Y/n] 确认
    """
    
    # 分隔线宽度
    SEPARATOR_WIDTH = 55
    
    def __init__(self, input_func=None, output_func=None):
        """
        初始化 UI
        
        Args:
            input_func: 输入函数（用于测试注入）
            output_func: 输出函数（用于测试注入）
        """
        self._input = input_func or input
        self._print = output_func or print
    
    def print(self, *args, **kwargs):
        """打印输出"""
        self._print(*args, **kwargs)
    
    def print_header(self, title: str):
        """打印标题"""
        self._print("")
        self._print("═" * self.SEPARATOR_WIDTH)
        self._print(title)
        self._print("═" * self.SEPARATOR_WIDTH)
    
    def print_info(self, message: str):
        """打印信息"""
        self._print(message)
    
    def print_success(self, message: str):
        """打印成功信息"""
        self._print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误信息"""
        self._print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        self._print(f"⚠️  {message}")
    
    def prompt(self, message: str, choices: Optional[List[str]] = None) -> str:
        """
        提示用户输入（必须有明确输入，禁止空输入使用默认）
        
        Args:
            message: 提示消息
            choices: 可选值列表
        
        Returns:
            用户输入（已转大写）
        """
        prompt_str = f"{message}> "
        
        while True:
            try:
                user_input = self._input(prompt_str).strip()
                
                # 禁止空输入
                if not user_input:
                    self._print("请输入有效值")
                    continue
                
                user_input = user_input.upper()
                
                # 验证可选值
                if choices:
                    if user_input in [c.upper() for c in choices]:
                        return user_input
                    self._print(f"无效输入，请选择: {', '.join(choices)}")
                    continue
                
                return user_input
                
            except (EOFError, KeyboardInterrupt):
                self._print("\n操作已取消")
                sys.exit(0)
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """
        Y/n 确认
        
        Args:
            message: 提示消息
            default: 默认值（True=Y, False=n）
        
        Returns:
            用户是否确认
        """
        if default:
            prompt_str = f"{message} [Y/n]："
        else:
            prompt_str = f"{message} [y/N]："
        
        while True:
            try:
                user_input = self._input(prompt_str).strip().lower()
                
                # 空输入使用默认值
                if not user_input:
                    return default
                
                if user_input in ['y', 'yes', '是']:
                    return True
                elif user_input in ['n', 'no', '否']:
                    return False
                else:
                    self._print("请输入 Y 或 n")
                    
            except (EOFError, KeyboardInterrupt):
                self._print("\n操作已取消")
                sys.exit(0)
    
    def print_table(self, headers: List[str], rows: List[List[str]]):
        """打印简单表格"""
        if not rows:
            self._print("  (无数据)")
            return
        
        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        self._print(header_line)
        self._print("-" * len(header_line))
        
        # 打印行
        for row in rows:
            row_str = "  ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            self._print(row_str)


class CLI:
    """命令行接口主类"""
    
    def __init__(self):
        self.ui = ConsoleUI()
        self.config: Optional[ConfigManager] = None
        self.paths: Optional[PathManager] = None
        self.installer: Optional[SkillInstaller] = None
    
    def init_config(self) -> bool:
        """
        初始化配置
        
        Returns:
            是否成功
        """
        self.config = ConfigManager()
        
        # 检查是否已配置
        if not self.config.is_configured:
            # 首次配置
            if not self.config.interactive_setup(self.ui):
                self.ui.print_error("配置失败，无法继续")
                return False
        else:
            # 确认现有配置
            try:
                if not self.config.interactive_confirm(self.ui):
                    self.ui.print_error("配置无效，无法继续")
                    return False
            except ConfigError as e:
                self.ui.print_error(f"配置错误: {e}")
                return False
        
        # 初始化路径管理器和安装器
        try:
            manager_dir = self.config.get_manager_dir()
            self.paths = PathManager(manager_dir)
            self.installer = SkillInstaller(self.config, self.paths)
            self.installer.set_ui(self.ui)
            return True
        except Exception as e:
            self.ui.print_error(f"初始化失败: {e}")
            return False
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        运行 CLI
        
        Args:
            args: 命令行参数
        
        Returns:
            退出码
        """
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # 初始化配置
        if not self.init_config():
            return 1
        
        # 分发命令
        try:
            if parsed_args.command == "install":
                return self._cmd_install(parsed_args)
            elif parsed_args.command == "uninstall":
                return self._cmd_uninstall(parsed_args)
            elif parsed_args.command == "list":
                return self._cmd_list(parsed_args)
            elif parsed_args.command == "config":
                return self._cmd_config(parsed_args)
            elif parsed_args.command == "info":
                return self._cmd_info(parsed_args)
            else:
                parser.print_help()
                return 1
        except KeyboardInterrupt:
            self.ui.print("\n\n操作已取消")
            return 130
        except Exception as e:
            self.ui.print_error(f"发生错误: {e}")
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            prog="skill-installer",
            description="标准化安装、卸载、管理 Kimi CLI Skills 的工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  skill-installer install skill-name          安装指定 skill
  skill-installer uninstall skill-name        卸载指定 skill
  skill-installer list                        列出已安装 skill
  skill-installer list --available            列出可安装 skill
  skill-installer info skill-name             查看 skill 详情
  skill-installer config --show               显示当前配置
  skill-installer config --reset              重置配置
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="可用命令")
        
        # install 命令
        install_parser = subparsers.add_parser("install", help="安装 skill")
        install_parser.add_argument("skill_name", help="skill 名称")
        install_parser.add_argument(
            "--option", "-o",
            choices=["full", "light", "clone-only"],
            default="full",
            help="安装选项（默认: full）"
        )
        
        # uninstall 命令
        uninstall_parser = subparsers.add_parser("uninstall", help="卸载 skill")
        uninstall_parser.add_argument("skill_name", help="skill 名称")
        
        # list 命令
        list_parser = subparsers.add_parser("list", help="列出 skill")
        list_parser.add_argument(
            "--installed", "-i",
            action="store_true",
            help="仅显示已安装的 skill"
        )
        list_parser.add_argument(
            "--available", "-a",
            action="store_true",
            help="仅显示可安装的 skill"
        )
        
        # info 命令
        info_parser = subparsers.add_parser("info", help="查看 skill 详情")
        info_parser.add_argument("skill_name", help="skill 名称")
        
        # config 命令
        config_parser = subparsers.add_parser("config", help="配置管理")
        config_parser.add_argument(
            "--show", "-s",
            action="store_true",
            help="显示当前配置"
        )
        config_parser.add_argument(
            "--reset", "-r",
            action="store_true",
            help="重置配置"
        )
        
        return parser
    
    def _cmd_install(self, args) -> int:
        """安装命令"""
        # Windows 权限检查
        if PlatformInfo.is_windows() and not PlatformInfo.is_admin():
            self.ui.print_warning("Windows 创建软连接需要管理员权限")
            self.ui.print_info("\n【选项】")
            self.ui.print("  [A] 继续尝试（可能失败）")
            self.ui.print("  [B] 显示手动创建指令")
            self.ui.print("  [C] 取消")
            self.ui.print()
            
            choice = self.ui.prompt("请选择", choices=["A", "B", "C"])
            
            if choice == "C":
                return 0
            elif choice == "B":
                skill_name = args.skill_name
                source = self.paths.get_skill_source_path(skill_name)
                target = self.paths.get_skill_symlink_path(skill_name)
                
                self.ui.print_header("手动创建软连接指令")
                self.ui.print_info("请以管理员身份打开 PowerShell，执行：")
                self.ui.print()
                self.ui.print(f'New-Item -ItemType SymbolicLink `')
                self.ui.print(f'  -Path "{target}" `')
                self.ui.print(f'  -Target "{source}"')
                self.ui.print()
                self.ui.print_info("或以管理员身份打开 CMD，执行：")
                self.ui.print()
                self.ui.print(f'mklink /D "{target}" "{source}"')
                self.ui.print()
                return 0
        
        # 转换选项
        option_map = {
            "full": InstallOption.FULL,
            "light": InstallOption.LIGHT,
            "clone-only": InstallOption.CLONE_ONLY
        }
        option = option_map.get(args.option, InstallOption.FULL)
        
        # 执行安装
        result = self.installer.install(args.skill_name, option)
        
        self.ui.print(result.format_display())
        
        return 0 if result.success else 1
    
    def _cmd_uninstall(self, args) -> int:
        """卸载命令"""
        result = self.installer.uninstall(args.skill_name)
        
        self.ui.print(result.format_display())
        
        if result.success and result.preserved_paths:
            self.ui.print()
            self.ui.print_info("如需删除原始仓库，请执行以下命令：")
            for path in result.preserved_paths:
                cmd = self.installer.paths.get_delete_commands(args.skill_name).get('source', {}).get('command', '')
                self.ui.print(f"  {cmd}")
        
        return 0 if result.success else 1
    
    def _cmd_list(self, args) -> int:
        """列表命令"""
        show_installed = args.installed or not args.available
        show_available = args.available or not args.installed
        
        if show_installed:
            self.ui.print_header("📦 已安装的 Skills")
            installed = self.installer.list_installed()
            
            if installed:
                rows = []
                for info in installed:
                    status = "✅" if info['symlink_valid'] else "⚠️"
                    rows.append([
                        info['name'],
                        status,
                        str(info['source_path'])[:40] + "..." if len(str(info['source_path'])) > 40 else str(info['source_path'])
                    ])
                self.ui.print_table(["名称", "状态", "源路径"], rows)
            else:
                self.ui.print_info("  暂无已安装的 skill")
            
            if show_available:
                self.ui.print()
        
        if show_available:
            self.ui.print_header("📋 可安装的 Skills")
            available = self.installer.list_available()
            
            if available:
                rows = []
                for info in available:
                    valid = "✅" if info['source_valid'] else "❌"
                    rows.append([
                        info['name'],
                        valid,
                        str(info['source_path'])[:40] + "..." if len(str(info['source_path'])) > 40 else str(info['source_path'])
                    ])
                self.ui.print_table(["名称", "有效", "源路径"], rows)
            else:
                self.ui.print_info("  暂无可安装的 skill")
                self.ui.print_info(f"\n  管理目录：{self.paths.manager_dir}")
        
        return 0
    
    def _cmd_info(self, args) -> int:
        """信息命令"""
        info = self.installer.get_skill_info(args.skill_name)
        
        if not info:
            self.ui.print_error(f"Skill '{args.skill_name}' 不存在")
            return 1
        
        self.ui.print_header(f"📄 Skill 详情：{args.skill_name}")
        
        self.ui.print_info("【基本信息】")
        self.ui.print(f"  名称：{info['name']}")
        self.ui.print(f"  源路径：{info['source_path']}")
        self.ui.print(f"  源有效：{'✅ 是' if info['source_valid'] else '❌ 否'}")
        
        self.ui.print()
        self.ui.print_info("【安装状态】")
        self.ui.print(f"  已安装：{'✅ 是' if info['is_installed'] else '❌ 否'}")
        
        if info['is_installed']:
            self.ui.print(f"  软连接：{info['symlink_path']}")
            self.ui.print(f"  相对路径：{info['relative_path']}")
            self.ui.print(f"  软连接有效：{'✅ 是' if info.get('symlink_valid', False) else '❌ 否'}")
            if info.get('symlink_target'):
                self.ui.print(f"  指向目标：{info['symlink_target']}")
        
        if info.get('skill_md_preview'):
            self.ui.print()
            self.ui.print_info("【SKILL.md 预览】")
            self.ui.print("─" * 40)
            self.ui.print(info['skill_md_preview'])
            self.ui.print("─" * 40)
        
        return 0
    
    def _cmd_config(self, args) -> int:
        """配置命令"""
        if args.reset:
            if self.ui.confirm("确定要重置配置吗？这将删除配置文件", default=False):
                self.config.reset()
                self.ui.print_success("配置已重置")
                # 重新配置
                if self.config.interactive_setup(self.ui):
                    self.ui.print_success("重新配置完成")
                else:
                    self.ui.print_error("重新配置失败")
            return 0
        
        if args.show or not (args.reset):
            self.ui.print_header("⚙️ 当前配置")
            info = self.config.get_config_info()
            
            self.ui.print_info("【路径信息】")
            self.ui.print(f"  Skill 目录：{info['skill_dir']}")
            self.ui.print(f"  配置文件：{info['config_file']}")
            
            self.ui.print()
            self.ui.print_info("【配置状态】")
            self.ui.print(f"  已配置：{'✅ 是' if info['is_configured'] else '❌ 否'}")
            
            if info['is_configured']:
                self.ui.print(f"  管理目录：{info.get('manager_dir', 'N/A')}")
                self.ui.print(f"  平台：{info.get('platform', 'N/A')}")
                self.ui.print(f"  配置时间：{info.get('first_config_time', 'N/A')}")
                self.ui.print(f"  配置版本：{info.get('version', 'N/A')}")
                
                if 'is_valid' in info:
                    self.ui.print(f"  配置有效：{'✅ 是' if info['is_valid'] else '❌ 否'}")
                if 'validation_error' in info:
                    self.ui.print(f"  验证错误：{info['validation_error']}")
            
            return 0
        
        return 0


def main(args: Optional[List[str]] = None) -> int:
    """主入口函数"""
    cli = CLI()
    return cli.run(args)
