"""
CLI 专用 UI 交互层

集中管理所有 input()/print() 调用，仅用于命令行模式。
Kimi 交互模式不使用此模块。
"""

import sys
from typing import Optional, List, Any


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
        if args:
            self._print(*args, **kwargs)
        else:
            self._print("")
    
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


class ConfigSetupUI:
    """配置设置交互（从 config.py 提取）"""
    
    def __init__(self, ui: ConsoleUI):
        self.ui = ui
    
    def interactive_setup(self, config) -> bool:
        """
        交互式配置引导
        
        Args:
            config: ConfigManager 实例
        
        Returns:
            是否成功配置
        """
        self.ui.print_header("⚙️ 初始配置")
        
        # 显示当前项目目录
        current_project = config.skill_dir.parent.resolve()
        self.ui.print_info("【当前项目目录】")
        self.ui.print(f"  {current_project}")
        self.ui.print()
        
        # 提供选项
        self.ui.print_info("【请选择管理目录】")
        self.ui.print("  [A] 使用当前项目目录作为管理目录")
        self.ui.print("  [B] 自定义管理目录")
        self.ui.print()
        
        from pathlib import Path
        
        choice = self.ui.prompt("请选择", choices=["A", "B"])
        
        if choice == "A":
            manager_dir = current_project
        else:
            # 自定义目录
            while True:
                custom_path = self.ui.prompt("请输入管理目录的绝对路径")
                manager_dir = Path(custom_path).expanduser().resolve()
                
                if not manager_dir.is_absolute():
                    self.ui.print_error("必须是绝对路径，请重新输入")
                    continue
                
                if not manager_dir.exists():
                    self.ui.print_error(f"目录不存在: {manager_dir}")
                    create = self.ui.confirm(f"是否创建目录?", default=False)
                    if create:
                        try:
                            manager_dir.mkdir(parents=True, exist_ok=True)
                            self.ui.print_success(f"已创建目录: {manager_dir}")
                            break
                        except Exception as e:
                            self.ui.print_error(f"创建目录失败: {e}")
                    continue
                
                import os
                if not os.access(manager_dir, os.W_OK):
                    self.ui.print_error(f"没有写入权限: {manager_dir}")
                    continue
                
                break
        
        # 确认
        self.ui.print_header("配置确认")
        self.ui.print_info("您选择了：")
        self.ui.print(f"  管理目录：{manager_dir}")
        self.ui.print()
        
        if not self.ui.confirm("是否确认？", default=True):
            self.ui.print_info("已取消配置")
            return False
        
        # 保存配置
        try:
            config.set_manager_dir(manager_dir)
            self.ui.print_success("✅ 配置已保存")
            return True
        except Exception as e:
            self.ui.print_error(f"保存配置失败: {e}")
            return False
    
    def interactive_confirm(self, config) -> bool:
        """
        交互式确认当前配置
        
        Args:
            config: ConfigManager 实例
        
        Returns:
            是否继续使用当前配置
        """
        self.ui.print_header("⚙️ 配置确认")
        
        try:
            manager_dir = config.get_manager_dir()
            self.ui.print_info(f"当前管理目录：{manager_dir}")
            self.ui.print()
            self.ui.print_info("是否继续使用此目录？")
            self.ui.print("  [Y] 是的，继续使用")
            self.ui.print("  [N] 更换管理目录")
            self.ui.print()
            
            choice = self.ui.prompt("请选择", choices=["Y", "N"])
            
            if choice == "Y":
                return True
            else:
                # 重新配置
                config.reset()
                return self.interactive_setup(config)
                
        except Exception:
            # 配置无效，重新配置
            self.ui.print_warning("当前配置无效，需要重新配置")
            return self.interactive_setup(config)


class InstallUI:
    """安装交互辅助类"""
    
    def __init__(self, ui: ConsoleUI):
        self.ui = ui
    
    def display_install_plan(self, plan):
        """显示安装方案"""
        self.ui.print_header(f"📦 安装方案：{plan.skill_name}")
        
        self.ui.print_info("【安装位置】")
        self.ui.print(f"  原始仓库：{plan.source_path}")
        self.ui.print(f"  软连接：  {plan.symlink_path}")
        self.ui.print(f"         → {plan.relative_path}")
        
        if plan.estimated_size:
            size_mb = plan.estimated_size / (1024 * 1024)
            self.ui.print()
            self.ui.print_info(f"【预估大小】{size_mb:.1f} MB")
        
        if plan.dependencies:
            self.ui.print()
            self.ui.print_info("【依赖清单】")
            for i, dep in enumerate(plan.dependencies, 1):
                self.ui.print(f"  {i}. {dep.get('name', '未知')}")
                if 'description' in dep:
                    self.ui.print(f"     作用：{dep['description']}")
                if 'size' in dep:
                    size_str = f"{dep['size'] / (1024*1024):.1f} MB" if dep['size'] > 1024*1024 else f"{dep['size'] / 1024:.1f} KB"
                    self.ui.print(f"     大小：{size_str}")
        
        if not plan.pre_check_passed:
            self.ui.print()
            self.ui.print_error("【预检查失败】")
            for error in plan.pre_check_errors:
                self.ui.print(f"  - {error}")
        
        self.ui.print()
        self.ui.print_info("【选项】")
        self.ui.print("  [A] 完全安装")
        self.ui.print("  [B] 轻量安装")
        self.ui.print("  [C] 仅克隆")
        self.ui.print("  [D] 取消安装")
        self.ui.print()
    
    def prompt_install_option(self) -> str:
        """提示用户选择安装选项"""
        return self.ui.prompt("请选择", choices=["A", "B", "C", "D"])
    
    def confirm_install(self) -> bool:
        """确认执行安装"""
        return self.ui.confirm("是否确认执行安装？", default=True)
    
    def display_install_result(self, result):
        """显示安装结果"""
        self.ui.print(result.format_display())


class UninstallUI:
    """卸载交互辅助类"""
    
    def __init__(self, ui: ConsoleUI):
        self.ui = ui
    
    def display_uninstall_plan(self, plan):
        """显示卸载方案"""
        self.ui.print_header(f"🗑️ 卸载方案：{plan.skill_name}")
        
        self.ui.print_info("【将执行的操作】")
        self.ui.print(f"  ✅ 删除软连接：{plan.symlink_path}")
        
        self.ui.print()
        self.ui.print_info("【将保留的内容】（手动删除命令）")
        self.ui.print()
        self.ui.print(f"  1. Skill 原始仓库")
        self.ui.print(f"     位置：{plan.source_path}")
        
        if plan.delete_commands and 'source' in plan.delete_commands:
            cmd_info = plan.delete_commands['source']
            self.ui.print(f"     删除命令：")
            self.ui.print(f"       {cmd_info.get('platform', 'unknown')}: {cmd_info.get('command', '')}")
        
        if not plan.pre_check_passed:
            self.ui.print()
            self.ui.print_error("【预检查失败】")
            for error in plan.pre_check_errors:
                self.ui.print(f"  - {error}")
        
        self.ui.print()
    
    def confirm_uninstall(self) -> bool:
        """确认执行卸载"""
        return self.ui.confirm("是否确认删除软连接？", default=True)
    
    def display_uninstall_result(self, result):
        """显示卸载结果"""
        self.ui.print(result.format_display())
