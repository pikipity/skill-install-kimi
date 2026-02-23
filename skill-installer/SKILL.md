---
name: skill-installer
description: 标准化安装、卸载、管理 Kimi CLI Skills 的交互式工具。通过自然语言与 Kimi 对话完成操作，支持 macOS、Linux 和 Windows 系统。
---

# Skill Installer

标准化安装、卸载、管理 Kimi CLI Skills 的**Kimi 交互式**工具。

**使用方式**：直接告诉 Kimi 你的需求，如"安装 skill-pdf"、"列出我的 skills"、"卸载 skill-xxx"。

---

## When to Use

当用户想要：
- 安装新的 skill（"安装 skill-xxx"、"添加 xxx skill"、"帮我装一下 xxx"）
- 卸载已安装的 skill（"卸载 skill-xxx"、"删除 xxx"、"移除 xxx"）
- 查看已安装的 skills（"列出我的 skills"、"安装了哪些 skill"）
- 查看可安装的 skills（"有哪些 skill 可以安装"）
- 配置 skill 管理目录（"更改管理目录"、"配置 skill-installer"）

---

## Workflow

### 第一步：检查配置状态

首先检查 skill-installer 是否已配置：

```python
from skill_installer import api
status = api.validate_setup()
```

返回的 `SetupStatus` 包含：
- `configured`: bool - 是否已配置
- `manager_dir`: str - 管理目录路径
- `platform`: str - 平台标识 ('macos' | 'linux' | 'windows')
- `is_admin`: bool - 是否有管理员权限（Windows 关键）
- `error`: str - 错误信息（如有）

### 第二步：初始配置（如需要）

如果 `status.configured` 为 `False`，引导用户完成初始配置：

```
⚙️ 初始配置
═══════════════════════════════════════════════════════

【说明】
skill-installer 需要一个管理目录来存放所有 skill 仓库。

【选项】
  [A] 使用当前目录：/Users/{username}/Documents/kimi/skills/
  [B] 自定义其他目录

请选择 > 
```

用户选择并确认路径后，保存配置：

```python
success, error = api.initialize_config(manager_dir)
```

### 第三步：跨平台处理（重要）

#### Windows 权限检测

如果 `status.platform == 'windows'` 且 `status.is_admin == False`：

```
⚠️ Windows 权限提示
═══════════════════════════════════════════════════════

检测到 Windows，创建软连接需要管理员权限。

【选项】
  [A] 退出，以管理员身份重新运行 Kimi CLI
  [B] 获取手动创建软连接的指令
  [C] 取消安装

> B

═══════════════════════════════════════════════════════
手动创建软连接指令
═══════════════════════════════════════════════════════

请以管理员身份打开 PowerShell，执行：

New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
  -Target "C:\Users\{username}\skill-install-project\skill-installer"

完成后告诉我"已手动创建"，我继续完成配置记录。
```

**注意**：Windows 用户选择手动创建后，Kimi 应记录此情况，后续操作继续通过 API 管理配置，软连接由用户手动维护。

### 第四步：执行用户请求

根据用户意图调用相应 API：

#### 安装 Skill

1. 列出可安装的 skills：
```python
available = api.list_available_skills()
```

2. 如果用户指定了 skill 名称，生成安装方案：
```python
plan = api.generate_install_plan(skill_name, option="full")
```

3. **Windows 特殊处理**：如果 `plan.requires_admin` 为 `True`，展示 `plan.windows_manual_command`

4. 向用户展示方案：
```
📦 安装方案：skill-pdf
═══════════════════════════════════════════════════════

【安装位置】
  原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
  软连接：  ~/.kimi/skills/skill-pdf

【依赖清单】
  1. skill-pdf
     - 作用：PDF 处理工具
     - 大小：2.5 MB

【选项】
  [A] 完全安装
  [B] 轻量安装
  [C] 仅克隆仓库
  [D] 取消

> A

是否确认执行安装？ [Y/n]：Y
```

5. 用户确认后执行安装：
```python
result = api.install_skill(skill_name, option="full")
```

6. 展示结果：
```
✅ 安装成功：skill-pdf

【安装位置】
  原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
  软连接：  ~/.kimi/skills/skill-pdf

【使用方式】
  现在可以直接使用：@skill-pdf <指令>
```

#### 卸载 Skill

1. 生成卸载方案：
```python
plan = api.generate_uninstall_plan(skill_name)
```

2. 向用户展示方案（仅删除软连接，保留原始仓库）：
```
🗑️ 卸载方案：skill-pdf
═══════════════════════════════════════════════════════

【将执行的操作】
  ✅ 删除软连接：~/.kimi/skills/skill-pdf

【将保留的内容】（如需删除，请手动执行）

  1. Skill 原始仓库
     位置：/Users/{username}/Documents/kimi/skills/skill-pdf/
     删除命令：
       macOS/Linux: rm -rf '/Users/{username}/Documents/kimi/skills/skill-pdf/'
       Windows:     Remove-Item -Recurse -Force "C:\Users\{username}\Documents\kimi\skills\skill-pdf\"

═══════════════════════════════════════════════════════

是否确认删除软连接？ [Y/n]：Y
```

**跨平台删除命令**：从 `plan.delete_commands` 获取当前平台对应的命令：
- `plan.delete_commands['macos']`
- `plan.delete_commands['linux']`
- `plan.delete_commands['windows']`

3. 用户确认后执行卸载：
```python
result = api.uninstall_skill(skill_name)
```

#### 列出 Skills

```python
# 已安装的
installed = api.list_installed_skills()

# 可安装的
available = api.list_available_skills()
```

展示格式：
```
📋 Skill 列表
═══════════════════════════════════════════════════════

【已安装】(2)
  ✅ skill-pdf     ~/.kimi/skills/skill-pdf
  ✅ skill-xlsx    ~/.kimi/skills/skill-xlsx

【可安装】(3)
  ⭕ skill-youtube  /Users/{username}/Documents/kimi/skills/skill-youtube/
  ⭕ skill-git      /Users/{username}/Documents/kimi/skills/skill-git/
  ⭕ skill-web      /Users/{username}/Documents/kimi/skills/skill-web/
```

---

## Available Tools

### Python API

所有功能通过 `skill_installer.api` 模块提供：

#### 配置管理

| 函数 | 用途 | 返回 |
|------|------|------|
| `validate_setup()` | 检查配置状态 | `SetupStatus` |
| `initialize_config(manager_dir)` | 初始化配置 | `(bool, str)` |
| `reset_config()` | 重置配置 | `bool` |
| `get_config_info()` | 获取配置信息 | `dict` |

#### Skill 查询

| 函数 | 用途 | 返回 |
|------|------|------|
| `list_available_skills()` | 列出可安装的 skills | `List[SkillInfo]` |
| `list_installed_skills()` | 列出已安装的 skills | `List[SkillInfo]` |
| `get_skill_info(name)` | 获取 skill 基本信息 | `SkillInfo` |
| `get_skill_detail(name)` | 获取 skill 完整详情（含 SKILL.md 预览） | `dict` |

#### 方案生成（用于展示给用户）

| 函数 | 用途 | 返回 |
|------|------|------|
| `generate_install_plan(name, option)` | 生成安装方案 | `InstallPlan` |
| `generate_uninstall_plan(name)` | 生成卸载方案 | `UninstallPlan` |

#### 执行操作

| 函数 | 用途 | 返回 |
|------|------|------|
| `install_skill(name, option)` | 安装 skill | `InstallResult` |
| `uninstall_skill(name)` | 卸载 skill | `UninstallResult` |

### 数据类

```python
# 配置状态（含跨平台信息）
@dataclass
class SetupStatus:
    configured: bool
    manager_dir: Optional[str]
    platform: str              # 'macos' | 'linux' | 'windows'
    is_admin: bool             # Windows 权限关键
    error: Optional[str]

# Skill 信息
@dataclass
class SkillInfo:
    name: str
    source_path: str
    is_installed: bool
    symlink_path: Optional[str]
    symlink_valid: bool
    source_valid: bool

# 安装方案（含跨平台处理）
@dataclass
class InstallPlan:
    skill_name: str
    source_path: str
    symlink_path: str
    relative_path: str
    option: str                # "full", "light", "clone-only"
    requires_admin: bool       # Windows 是否需要管理员
    windows_manual_command: Optional[dict]  # 手动命令
    pre_check_passed: bool
    pre_check_errors: List[str]

# 卸载方案（含跨平台删除命令）
@dataclass
class UninstallPlan:
    skill_name: str
    source_path: str
    symlink_path: str
    delete_commands: dict      # {'macos': '...', 'linux': '...', 'windows': '...'}
    pre_check_passed: bool
    pre_check_errors: List[str]
```

---

## Directory Structure

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # 本文件（Kimi 交互指导）
│   ├── src/                        # 源代码
│   │   ├── __init__.py
│   │   ├── api.py                  # ★ Kimi API 层（核心，供 Kimi 调用）
│   │   ├── cli.py                  # CLI 入口（保留不使用）
│   │   ├── cli_ui.py               # CLI 交互层（保留不使用）
│   │   ├── core.py                 # 核心逻辑（无交互）
│   │   ├── config.py               # 配置管理（无交互）
│   │   ├── path_manager.py         # 路径管理
│   │   ├── platform_utils.py       # 跨平台工具
│   │   └── validator.py            # 安装验证
│   └── data/                       # 运行时数据目录
│       └── config.json             # 配置文件
├── skill-pdf/                      # 其他 skills...
├── skill-xlsx/
└── ...
```

---

## Design Principles

1. **Kimi 交互式**：用户通过自然语言与 Kimi 对话完成操作，无需记忆命令
2. **方案先行**：执行操作前先生成方案（`generate_*_plan`），用户确认后再执行
3. **非侵入式**：卸载仅删除软连接，保留原始仓库
4. **跨平台**：支持 macOS、Linux、Windows（Windows 需管理员权限创建软连接）
5. **无外部依赖**：仅使用 Python 标准库

---

## Platform Notes

### Windows

- 创建软连接需要**管理员权限**
- 无管理员权限时，通过 `validate_setup()` 检测，`generate_install_plan()` 返回手动命令
- **Kimi 处理流程**：检测到 `platform='windows'` 且 `is_admin=False` 时，提供三选项：
  - [A] 退出以管理员重开
  - [B] 获取手动创建软连接的 PowerShell/CMD 命令
  - [C] 取消操作

### macOS / Linux

- 普通用户权限即可创建软连接
- 建议使用相对路径软连接，便于项目迁移

---

## License

MIT
