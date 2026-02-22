---
name: skill-installer
description: 标准化安装、卸载、管理 Kimi CLI Skills 的工具。提供跨平台的 skill 管理能力，支持 macOS、Linux 和 Windows 系统。
---

# Skill Installer

标准化安装、卸载、管理 Kimi CLI Skills 的工具。

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

- 如果 `status.configured` 为 `False`：需要引导用户完成初始配置
- 如果 `status.configured` 为 `True`：可以继续使用，或询问是否更换目录

### 第二步：初始配置（如需要）

如果未配置，向用户说明并询问管理目录：

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

用户选择后，保存配置：

```python
success, error = api.initialize_config(manager_dir)
```

### 第三步：执行用户请求

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

3. 向用户展示方案：
```
📦 安装方案：skill-pdf
═══════════════════════════════════════════════════════

【安装位置】
  原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
  软连接：  ~/.kimi/skills/skill-pdf

【选项】
  [A] 完全安装
  [B] 轻量安装
  [C] 仅克隆仓库
  [D] 取消
```

4. 用户确认后执行安装：
```python
result = api.install_skill(skill_name, option="full")
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

【将保留的内容】
  原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
  （如需删除，请手动执行：rm -rf '...'）
```

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

#### 系统检查

| 函数 | 用途 | 返回 |
|------|------|------|
| `check_windows_permission()` | 检查 Windows 权限 | `str` or `None` |
| `get_manual_symlink_command(name)` | 获取手动创建软连接命令 | `dict` |

### 数据类

```python
# 配置状态
@dataclass
class SetupStatus:
    configured: bool
    manager_dir: Optional[str]
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

# 安装方案
@dataclass
class InstallPlan:
    skill_name: str
    source_path: str
    symlink_path: str
    relative_path: str
    option: str  # "full", "light", "clone-only"
    pre_check_passed: bool
    pre_check_errors: List[str]

# 卸载方案
@dataclass
class UninstallPlan:
    skill_name: str
    source_path: str
    symlink_path: str
    delete_commands: dict
    pre_check_passed: bool
    pre_check_errors: List[str]
```

---

## CLI Mode (可选)

高级用户也可以直接通过命令行使用：

```bash
# 安装
python -m skill-installer install skill-name [--option full|light|clone-only]

# 卸载
python -m skill-installer uninstall skill-name

# 列出
python -m skill-installer list [--installed] [--available]

# 详情
python -m skill-installer info skill-name

# 配置
python -m skill-installer config [--show] [--reset]
```

---

## Directory Structure

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # 本文件（Kimi 交互指导）
│   ├── src/                        # 源代码
│   │   ├── __init__.py
│   │   ├── __main__.py             # CLI 入口点
│   │   ├── api.py                  # ★ Kimi API 层（核心）
│   │   ├── cli.py                  # CLI 命令解析
│   │   ├── cli_ui.py               # CLI 交互层
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

1. **分离交互与逻辑**：`api.py` 和 `core.py` 无交互代码，交互由 Kimi 或 `cli_ui.py` 处理
2. **方案先行**：执行操作前先生成方案（`generate_*_plan`），用户确认后再执行
3. **非侵入式**：卸载仅删除软连接，保留原始仓库
4. **跨平台**：支持 macOS、Linux、Windows（Windows 需管理员权限创建软连接）
5. **无外部依赖**：仅使用 Python 标准库

---

## Platform Notes

### Windows

- 创建软连接需要**管理员权限**
- 无管理员权限时，API 会返回提示信息，可提供手动创建指令
- 使用 `check_windows_permission()` 检查权限状态

### macOS / Linux

- 普通用户权限即可创建软连接
- 建议使用相对路径软连接，便于项目迁移

---

## License

MIT
