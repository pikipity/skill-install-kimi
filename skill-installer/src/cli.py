"""
命令行接口 - 基于 API 层的终端交互封装

⚠️ 此文件保留但不使用

当前 skill-installer 使用 Kimi 交互式工作流，用户通过自然语言与 Kimi 对话完成操作。
CLI 模式代码完整保留作为参考实现，如需使用可直接运行：
    python -m skill_installer.src.cli install <skill-name>

CLI 模式入口，通过 cli_ui 处理交互，调用 api 执行操作。
"""
# ============================================================================
# NOTE: This module is kept for reference but not used in the Kimi interactive
# workflow. See SKILL.md for the current usage pattern.
# ============================================================================

import sys
import argparse
from pathlib import Path
from typing import Optional, List

# API 层
from . import api

# CLI UI 层
from .cli_ui import (
    ConsoleUI, ConfigSetupUI, 
    InstallUI, UninstallUI
)

# 核心类型
from .config import ConfigManager, ConfigError
from .platform_utils import PlatformInfo, PlatformUtils


class CLI:
    """命令行接口主类"""
    
    def __init__(self):
        self.ui = ConsoleUI()
        self.config: Optional[ConfigManager] = None
        self.config_ui: Optional[ConfigSetupUI] = None
    
    def init_config(self) -> bool:
        """
        初始化配置
        
        Returns:
            是否成功
        """
        self.config = ConfigManager()
        self.config_ui = ConfigSetupUI(self.ui)
        
        # 检查是否已配置
        if not self.config.is_configured:
            # 首次配置
            if not self.config_ui.interactive_setup(self.config):
                self.ui.print_error("配置失败，无法继续")
                return False
        else:
            # 确认现有配置
            try:
                if not self.config_ui.interactive_confirm(self.config):
                    self.ui.print_error("配置无效，无法继续")
                    return False
            except ConfigError as e:
                self.ui.print_error(f"配置错误: {e}")
                return False
        
        return True
    
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
        
        # config 命令不需要初始化配置
        if parsed_args.command == "config":
            return self._cmd_config(parsed_args)
        
        # 其他命令需要初始化配置
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
        skill_name = args.skill_name
        
        # Windows 权限检查
        if PlatformInfo.is_windows() and not PlatformUtils.is_admin():
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
                cmd_info = api.get_manual_symlink_command(skill_name)
                if cmd_info:
                    self.ui.print_header("手动创建软连接指令")
                    self.ui.print_info("请以管理员身份打开 PowerShell，执行：")
                    self.ui.print()
                    self.ui.print(cmd_info['powershell'])
                    self.ui.print()
                    self.ui.print_info("或以管理员身份打开 CMD，执行：")
                    self.ui.print()
                    self.ui.print(cmd_info['cmd'])
                    self.ui.print()
                return 0
        
        # 生成安装方案
        plan = api.generate_install_plan(skill_name, args.option)
        if not plan:
            self.ui.print_error("配置未初始化")
            return 1
        
        # 显示方案并交互
        install_ui = InstallUI(self.ui)
        install_ui.display_install_plan(plan)
        
        # 如果预检查失败，直接返回
        if not plan.pre_check_passed:
            return 1
        
        # 选择安装选项
        choice = install_ui.prompt_install_option()
        if choice == "D":
            self.ui.print_info("已取消安装")
            return 0
        
        # 映射选项
        option_map = {"A": "full", "B": "light", "C": "clone-only"}
        selected_option = option_map.get(choice, "full")
        
        # 二次确认
        if not install_ui.confirm_install():
            self.ui.print_info("已取消安装")
            return 0
        
        # 执行安装
        result = api.install_skill(skill_name, selected_option, skip_confirm=True)
        install_ui.display_install_result(result)
        
        return 0 if result.success else 1
    
    def _cmd_uninstall(self, args) -> int:
        """卸载命令"""
        skill_name = args.skill_name
        
        # 生成卸载方案
        plan = api.generate_uninstall_plan(skill_name)
        if not plan:
            self.ui.print_error("配置未初始化或 skill 不存在")
            return 1
        
        # 显示方案并交互
        uninstall_ui = UninstallUI(self.ui)
        uninstall_ui.display_uninstall_plan(plan)
        
        # 如果预检查失败，直接返回
        if not plan.pre_check_passed:
            return 1
        
        # 确认卸载
        if not uninstall_ui.confirm_uninstall():
            self.ui.print_info("已取消卸载")
            return 0
        
        # 执行卸载
        result = api.uninstall_skill(skill_name, skip_confirm=True)
        uninstall_ui.display_uninstall_result(result)
        
        return 0 if result.success else 1
    
    def _cmd_list(self, args) -> int:
        """列表命令"""
        show_installed = args.installed or not args.available
        show_available = args.available or not args.installed
        
        if show_installed:
            self.ui.print_header("📦 已安装的 Skills")
            installed = api.list_installed_skills()
            
            if installed:
                rows = []
                for info in installed:
                    status = "✅" if info.symlink_valid else "⚠️"
                    source = info.source_path[:40] + "..." if len(info.source_path) > 40 else info.source_path
                    rows.append([info.name, status, source])
                self.ui.print_table(["名称", "状态", "源路径"], rows)
            else:
                self.ui.print_info("  暂无已安装的 skill")
            
            if show_available:
                self.ui.print()
        
        if show_available:
            self.ui.print_header("📋 可安装的 Skills")
            available = api.list_available_skills()
            
            if available:
                rows = []
                for info in available:
                    valid = "✅" if info.source_valid else "❌"
                    source = info.source_path[:40] + "..." if len(info.source_path) > 40 else info.source_path
                    rows.append([info.name, valid, source])
                self.ui.print_table(["名称", "有效", "源路径"], rows)
            else:
                self.ui.print_info("  暂无可安装的 skill")
                if self.config:
                    try:
                        manager_dir = self.config.get_manager_dir()
                        self.ui.print_info(f"\n  管理目录：{manager_dir}")
                    except Exception:
                        pass
        
        return 0
    
    def _cmd_info(self, args) -> int:
        """信息命令"""
        info = api.get_skill_detail(args.skill_name)
        
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
        config = ConfigManager()
        
        if args.reset:
            if self.ui.confirm("确定要重置配置吗？这将删除配置文件", default=False):
                if api.reset_config():
                    self.ui.print_success("配置已重置")
                    # 重新配置
                    config = ConfigManager()
                    config_ui = ConfigSetupUI(self.ui)
                    if config_ui.interactive_setup(config):
                        self.ui.print_success("重新配置完成")
                    else:
                        self.ui.print_error("重新配置失败")
                else:
                    self.ui.print_error("重置配置失败")
            return 0
        
        # 显示配置
        self.ui.print_header("⚙️ 当前配置")
        info = api.get_config_info()
        
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


def main(args: Optional[List[str]] = None) -> int:
    """主入口函数"""
    cli = CLI()
    return cli.run(args)
