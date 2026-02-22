# skill-installer 项目指导

> 本项目是一个用于标准化安装、卸载、管理 Kimi CLI Skills 的 skill。
> 
> 遵循《install-principle.md》中的六大原则：方案先行、依赖解释、路径规范、非侵入式、双位置分离、可回滚。

---

## 一、目录结构

```
skill-install-project/                      # 项目目录 = 管理目录（当前目录）
├── AGENTS.md                               # 本文件（项目指导）
├── README.md                               # 面向用户的使用说明
├── install-principle.md                    # 安装原则文档（已有）
└── skill-installer/                        # ★ skill 目录（核心代码）
    ├── SKILL.md                            # Skill 定义文档（Kimi CLI 读取入口）
    ├── src/                                # 源代码目录
    │   ├── __init__.py
    │   ├── core.py                         # 核心安装逻辑
    │   ├── config.py                       # 配置管理器（读写 data/config.json）
    │   ├── dependency.py                   # 依赖分析与管理
    │   ├── path_manager.py                 # 路径计算（相对路径软连接）
    │   ├── platform_utils.py               # ★ 跨平台工具函数（核心）
    │   └── validator.py                    # 安装验证
    └── data/                               # 运行时数据目录（首次使用后生成）
        └── config.json                     # 配置文件（存储管理目录、历史记录）
```

### 软连接结构

```
~/.kimi/skills/skill-installer  →  ../../{管理目录相对路径}/skill-install-project/skill-installer
```

---

## 二、核心设计原则

### 2.1 配置管理原则

| 项目 | 说明 |
|------|------|
| **配置文件位置** | `skill-installer/data/config.json`（skill 内部，随项目迁移）|
| **首次使用前** | 配置文件**不存在**，首次运行时创建 |
| **配置内容** | 管理目录路径、首次配置时间、平台信息、安装历史 |
| **管理目录询问** | **每次使用**都要确认管理目录是否正确（Y/n 选项）|

### 2.2 交互原则（所有操作使用 Y/n 确认）

**禁止使用的交互方式**：
- ❌ "直接回车使用默认"
- ❌ "按任意键继续"
- ❌ 不提供明确取消选项

**必须使用的交互方式**：
- ✅ 所有关键决策使用 `[Y/n]` 确认
- ✅ 提供明确的选项 A/B/C/D
- ✅ 取消操作始终可用

### 2.3 卸载原则

| 操作 | 执行内容 | 说明 |
|------|----------|------|
| **执行** | 删除软连接 `~/.kimi/skills/{skill-name}` | 仅解除 Kimi CLI 的引用 |
| **保留** | 原始仓库、所有依赖 | 供用户自行决定是否删除 |
| **提供** | 完整的删除指令列表 | 包含路径和命令 |

---

## 三、配置持久化机制

### 3.1 首次使用流程

```
用户调用 skill-installer
    ↓
检查 skill-installer/data/config.json 是否存在
    ↓（不存在）
展示初始配置说明
    ↓
提供选项 [A]使用当前目录 [B]自定义目录
    ↓
用户选择并确认路径
    ↓
显示确认信息，询问 [Y/n]
    ↓（Y）
创建 data/ 目录，写入 config.json
    ↓
继续执行用户请求的操作
```

### 3.2 后续使用流程

```
用户调用 skill-installer
    ↓
读取 skill-installer/data/config.json
    ↓
显示当前管理目录
    ↓
询问是否继续使用 [Y]继续 [N]更换
    ↓
根据选择使用已有配置或重新配置
    ↓
继续执行用户请求的操作
```

### 3.3 配置验证

每次读取配置时验证：
1. 管理目录路径是否存在
2. 是否有写入权限
3. 路径是否为绝对路径

验证失败时提示重新配置。

---

## 四、跨平台兼容性（核心）

### 4.1 平台支持矩阵

| 功能 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 基础安装 | ✅ 原生支持 | ✅ 原生支持 | ✅ 支持 |
| 软连接创建 | ✅ `ln -s` | ✅ `ln -s` | ⚠️ 需管理员权限 |
| 路径分隔符 | `/` | `/` | `\` 或 `/` |
| 家目录变量 | `$HOME` | `$HOME` | `%USERPROFILE%` |
| 配置文件路径 | `~/.kimi/` | `~/.kimi/` | `%USERPROFILE%\.kimi\` |

### 4.2 平台差异详细对照

#### 软连接创建

| 平台 | 命令 | 权限要求 | 代码实现 |
|------|------|----------|----------|
| **macOS** | `ln -s <源> <目标>` | 普通用户 | `os.symlink(src, dst)` |
| **Linux** | `ln -s <源> <目标>` | 普通用户 | `os.symlink(src, dst)` |
| **Windows** | `mklink /D <目标> <源>` | **管理员权限** | `subprocess.run(["cmd", "/c", "mklink", ...])` |

**Windows 软连接创建代码示例**：

```python
def create_symlink_windows(source: Path, target: Path):
    """
    Windows 创建目录联接/符号链接
    注意：需要管理员权限
    """
    import subprocess
    
    source_str = str(source.resolve())
    target_str = str(target)
    
    # 判断是文件还是目录
    if source.is_dir():
        cmd = ["cmd", "/c", "mklink", "/D", target_str, source_str]
    else:
        cmd = ["cmd", "/c", "mklink", target_str, source_str]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if "拒绝访问" in e.stderr or "access denied" in e.stderr.lower():
            raise PermissionError(
                "Windows 创建软连接需要管理员权限。\n"
                "请以管理员身份重新运行，或手动执行：\n"
                f"cmd /c mklink /D {target_str} {source_str}"
            )
        raise
```

#### 路径处理

```python
from pathlib import Path
import os

def get_kimi_config_dir() -> Path:
    """获取 Kimi 全局配置目录（跨平台）"""
    home = Path.home()
    return home / ".kimi"

def normalize_path(path: str) -> str:
    """规范化路径（跨平台）"""
    return os.path.normpath(os.path.expanduser(path))

def calculate_relative_path(from_path: Path, to_path: Path) -> str:
    """计算相对路径（跨平台统一使用 / 分隔符）"""
    rel = os.path.relpath(from_path, to_path)
    # Windows 下也使用 / 便于显示一致
    return rel.replace(os.sep, "/")
```

#### 删除命令

| 平台 | 删除目录 | 删除文件 | 实现方式 |
|------|----------|----------|----------|
| **macOS/Linux** | `rm -rf <path>` | `rm -f <path>` | `shutil.rmtree()` / `path.unlink()` |
| **Windows** | `rmdir /s /q <path>` | `del /f <path>` | `shutil.rmtree()` / `path.unlink()` |

**推荐**：使用 Python 标准库 `shutil` 和 `pathlib`，避免直接调用系统命令。

### 4.3 Windows 特殊处理策略

当检测到 Windows 平台时，采用以下策略：

#### 策略 1：检测管理员权限

```python
import ctypes

def is_admin() -> bool:
    """检测当前是否具有管理员权限（Windows）"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
```

#### 策略 2：无管理员权限时的处理

```
检测到 Windows 且无管理员权限时：

═══════════════════════════════════════════════════════
⚠️ Windows 权限提示
═══════════════════════════════════════════════════════

创建软连接需要管理员权限。

【选项】
  [A] 退出，以管理员身份重新运行 Kimi CLI
  [B] 获取手动创建软连接的指令
  [C] 使用目录拷贝代替软连接（不推荐，占用双倍空间）

> B

═══════════════════════════════════════════════════════
手动创建软连接指令
═══════════════════════════════════════════════════════

请以管理员身份打开 PowerShell 或 CMD，执行以下命令：

PowerShell:
  New-Item -ItemType SymbolicLink `
    -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
    -Target "C:\Users\ze\skill-install-project\skill-installer"

CMD:
  mklink /D %USERPROFILE%\.kimi\skills\skill-installer `
    C:\Users\ze\skill-install-project\skill-installer

完成后，按回车继续...
```

#### 策略 3：卸载时的跨平台命令

卸载时提供的删除指令必须区分平台：

```python
def get_delete_command(path: Path, platform: str) -> str:
    """获取当前平台的删除命令（用于显示给用户）"""
    path_str = str(path)
    
    if platform in ["macos", "linux"]:
        return f"rm -rf '{path_str}'"
    elif platform == "windows":
        # PowerShell 格式
        return f'Remove-Item -Recurse -Force "{path_str}"'
    else:
        return f"[删除] {path_str}"
```

### 4.4 平台检测工具函数

所有平台相关代码统一放在 `src/platform_utils.py`：

```python
# src/platform_utils.py

import platform
from pathlib import Path

class PlatformInfo:
    """跨平台信息获取"""
    
    @staticmethod
    def get_system() -> str:
        """
        返回标准化平台名称
        Returns: 'macos' | 'linux' | 'windows'
        """
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        return system  # 'linux' 或 'windows'
    
    @staticmethod
    def get_home_dir() -> Path:
        """获取用户家目录"""
        return Path.home()
    
    @staticmethod
    def get_kimi_dir() -> Path:
        """获取 Kimi 配置目录"""
        return PlatformInfo.get_home_dir() / ".kimi"
    
    @staticmethod
    def get_shell() -> str:
        """获取当前 shell 类型（用于显示命令）"""
        import os
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return "zsh"
        elif "bash" in shell:
            return "bash"
        elif platform.system() == "Windows":
            return "powershell"
        return "sh"
```

### 4.5 跨平台测试清单

开发完成后，必须在以下环境测试：

| 测试项 | macOS | Linux | Windows |
|--------|-------|-------|---------|
| 首次配置流程 | ✅ | ✅ | ✅ |
| 软连接创建 | ✅ | ✅ | ⚠️ 需管理员 |
| 配置文件读写 | ✅ | ✅ | ✅ |
| 路径计算（相对路径）| ✅ | ✅ | ✅ |
| 卸载并提供删除指令 | ✅ | ✅ | ✅ |
| 无管理员权限提示（Win）| N/A | N/A | ✅ |

---

## 五、代码组织规范

### 5.1 文件职责

| 文件 | 职责 |
|------|------|
| `SKILL.md` | Skill 定义，触发条件，命令说明（Kimi CLI 读取）|
| `src/config.py` | 配置读取、保存、验证（操作 data/config.json）|
| `src/core.py` | 安装/卸载/列表等核心逻辑 |
| `src/dependency.py` | 分析 skill 依赖，计算磁盘占用 |
| `src/path_manager.py` | 计算相对路径，创建软连接 |
| `src/platform_utils.py` | ★ **平台检测，跨平台命令执行（核心）**|
| `src/validator.py` | 安装前后验证 |

### 5.2 依赖要求

**本项目不依赖任何第三方 Python 包**，仅使用标准库：
- `pathlib` / `os` - 路径操作
- `json` - 配置读写
- `subprocess` - 执行系统命令
- `platform` / `sys` - 系统检测
- `ctypes` - Windows 权限检测
- `shutil` - 文件操作

---

## 六、交互范例模板

### 6.1 首次配置

```
═══════════════════════════════════════════════════════
⚙️ 初始配置
═══════════════════════════════════════════════════════

【当前项目目录】
  /Users/ze/Documents/kimi/skill/skill-install-project/

【请选择管理目录】
  [A] 使用当前项目目录作为管理目录
  [B] 自定义管理目录

> A

═══════════════════════════════════════════════════════
配置确认
═══════════════════════════════════════════════════════

您选择了：
  管理目录：/Users/ze/Documents/kimi/skill/skill-install-project/

是否确认？ [Y/n]：Y

✅ 配置已保存。
```

### 6.2 后续确认

```
═══════════════════════════════════════════════════════
⚙️ 配置确认
═══════════════════════════════════════════════════════

当前管理目录：/Users/ze/Documents/kimi/skill/skill-install-project/

是否继续使用此目录？
  [Y] 是的，继续使用
  [N] 更换管理目录

> Y
```

### 6.3 Windows 权限提示

```
═══════════════════════════════════════════════════════
⚠️ Windows 权限提示
═══════════════════════════════════════════════════════

检测到 Windows 系统，创建软连接需要管理员权限。

【请选择】
  [A] 退出，以管理员身份重新运行
  [B] 显示手动创建软连接的指令
  [C] 取消安装

> B

═══════════════════════════════════════════════════════
手动创建软连接指令
═══════════════════════════════════════════════════════

请以管理员身份打开 PowerShell，执行：

New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
  -Target "C:\Users\ze\skill-install-project\skill-installer"

完成后按回车继续...
```

### 6.4 安装方案确认

```
═══════════════════════════════════════════════════════
📦 安装方案：{skill-name}
═══════════════════════════════════════════════════════

【安装位置】
  原始仓库：{管理目录}/{skill-name}/
  软连接：  ~/.kimi/skills/{skill-name} → {相对路径}

【依赖清单】
  1. {依赖名}
     - 作用：...
     - 大小：...

请选择安装选项：
  [A] 完全安装
  [B] 轻量安装
  [C] 仅克隆仓库
  [D] 取消安装

> A

是否确认执行安装？ [Y/n]：Y
```

### 6.5 卸载确认（跨平台命令）

```
═══════════════════════════════════════════════════════
🗑️ 卸载方案：{skill-name}
═══════════════════════════════════════════════════════

【将执行的操作】
  ✅ 删除软连接：~/.kimi/skills/{skill-name}

【将保留的内容】（手动删除命令）

  1. Skill 原始仓库
     位置：{管理目录}/{skill-name}/
     删除命令：
       macOS/Linux: rm -rf '{管理目录}/{skill-name}/'
       Windows:     Remove-Item -Recurse -Force "{管理目录}\{skill-name}\"

  2. {依赖名}
     位置：{依赖路径}/
     删除命令：
       macOS/Linux: rm -rf '{依赖路径}/'
       Windows:     Remove-Item -Recurse -Force "{依赖路径}\"

═══════════════════════════════════════════════════════

是否确认删除软连接？ [Y/n]：Y

✅ 已删除软连接：~/.kimi/skills/{skill-name}
```

---

## 七、待修复问题（TODO）

### ~~TODO-1：confirm() 方法显示逻辑修复~~ ✅ 已修复

**问题描述**：
`cli.py` 第117行的 `confirm()` 方法，默认值显示逻辑有误。无论 `default` 是 `True` 还是 `False`，提示符都显示 `[Y/Y]`，不符合 `[Y/n]` 或 `[y/N]` 的规范格式。

**问题代码**（`cli.py:115-118`）：
```python
def confirm(self, message: str, default: bool = True) -> bool:
    default_str = "Y" if default else "n"
    # 实际效果：default=True 时显示 [Y/Y]，default=False 时也显示 [Y/Y]
    prompt_str = f"{message} [{'Y' if default else 'Y'}/{'n' if default else 'n'}]："
```

**修复方案**（已应用）：
```python
def confirm(self, message: str, default: bool = True) -> bool:
    """Y/n 确认"""
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
```

---

### ~~TODO-2：prompt() 方法空输入处理修复~~ ✅ 已修复

**问题描述**：
`cli.py` 第83-99行的 `prompt()` 方法，当用户输入为空时，如果提供了 `default` 参数，会自动使用默认值。这违反了方案中"**所有关键决策使用 [Y/n] 确认**，不允许直接回车使用默认"的原则。

**问题代码**（`cli.py:83-99`）：
```python
def prompt(self, message: str, default: Optional[str] = None, 
           choices: Optional[List[str]] = None) -> str:
    # ...
    while True:
        try:
            user_input = self._input(prompt_str).strip()
            
            # 使用默认值 - 这里违反了方案原则
            if not user_input and default:
                return default.upper()
```

**修复方案**（已应用）：
```python
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
```

**配套修改**（已应用）：
- `cli.py:64-99` - 移除了 `default` 参数
- `cli.py:325` - 移除了 `default="A"` 参数
- `config.py:251` - 移除了 `default="A"` 参数
- `config.py:323` - 移除了 `default="Y"` 参数
- `core.py:254` - 移除了 `default="A"` 参数

---

## 八、开发检查清单

在修改代码前，确认以下事项：

- [ ] 所有关键决策点都有 `[Y/n]` 确认
- [ ] 配置文件读写使用 `src/config.py` 中的 `ConfigManager`
- [ ] 路径计算使用 `path_manager.py` 中的相对路径方法
- [ ] **跨平台代码统一在 `platform_utils.py` 中处理**
- [ ] **Windows 软连接创建有管理员权限检测和降级方案**
- [ ] 软连接创建后立即验证可读性
- [ ] 卸载只删除软连接，提供**区分平台的**删除指令
- [ ] 不使用任何第三方 Python 包

---

## 九、修订记录

| 日期 | 版本 | 修订内容 |
|------|------|----------|
| 2026-02-22 | v1.0 | 初始版本，确立目录结构、交互规范和跨平台兼容性方案 |
