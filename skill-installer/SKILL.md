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

执行脚本检查配置：

```bash
python scripts/check_config.py
```

解析 JSON 输出，获取配置状态：
- `configured`: bool - 是否已配置
- `manager_dir`: str | null - 管理目录路径
- `platform`: str - 平台标识 ('macos' | 'linux' | 'windows')
- `is_admin`: bool - 是否有管理员权限（Windows 关键）
- `error`: str | null - 错误信息

**根据结果判断下一步**：
- 如果 `configured: false` → 进入第二步（初始配置）
- 如果 `configured: true` → 进入第三步（执行用户请求）

---

### 第二步：初始配置（如需要）

如果 `configured: false`，引导用户完成初始配置。

**完整配置流程**：

1. **展示初始配置界面**：

```
⚙️ 初始配置
═══════════════════════════════════════════════════════

【说明】
skill-installer 需要一个管理目录来存放所有 skill 仓库。

【当前工作目录】
  {current_dir}

【选项】
  [A] 使用当前目录作为管理目录
  [B] 自定义其他目录
  [C] 取消操作

请选择 >
```

2. **处理用户选择**：

**如果用户选择 A**（使用当前目录）：
```python
import os
manager_dir = os.getcwd()
```

**如果用户选择 B**（自定义目录）：
```
请输入管理目录的完整路径 > {user_input}

【路径确认】
  {manager_dir}

是否确认使用此目录？ [Y/n] > Y
```

3. **验证并保存配置**：

```python
import os
from pathlib import Path

# 验证路径
path = Path(manager_dir).expanduser().resolve()
if not path.exists():
    print(f"错误：目录不存在: {path}")
    return
if not path.is_absolute():
    print(f"错误：必须是绝对路径: {path}")
    return
if not os.access(path, os.W_OK):
    print(f"错误：没有写入权限: {path}")
    return
```

执行保存：
```bash
python scripts/init_config.py --dir "{manager_dir}"
```

4. **验证配置成功**：

```bash
python scripts/check_config.py
```

确认 `configured: true` 后继续。

---

### 第三步：跨平台处理（重要）

#### Windows 权限检测

如果 `platform == 'windows'` 且 `is_admin == false`：

```
⚠️ Windows 权限提示
═══════════════════════════════════════════════════════

检测到 Windows，创建软连接需要管理员权限。

【选项】
  [A] 退出，以管理员身份重新运行 Kimi CLI
  [B] 获取手动创建软连接的指令
  [C] 取消操作

> B

═══════════════════════════════════════════════════════
手动创建软连接指令
═══════════════════════════════════════════════════════

请以管理员身份打开 PowerShell，执行：

New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\{skill-name}" `
  -Target "{source_path}"

完成后告诉我"已手动创建"，我继续记录配置。
```

**注意**：Windows 用户选择手动模式后，Kimi 应记录此情况，后续操作继续通过脚本管理配置，软连接由用户手动维护。

---

### 第四步：执行用户请求

根据用户意图调用相应脚本：

#### 列出 Skills

**已安装的 skills**：
```bash
python scripts/list_skills.py --installed
```

**可安装的 skills**：
```bash
python scripts/list_skills.py --available
```

**展示格式**：
```
📋 Skill 列表
═══════════════════════════════════════════════════════

【已安装】(2)
  ✅ skill-pdf     ~/.kimi/skills/skill-pdf
  ✅ skill-xlsx    ~/.kimi/skills/skill-xlsx

【可安装】(3)
  ⭕ skill-youtube  {manager_dir}/skill-youtube/
  ⭕ skill-git      {manager_dir}/skill-git/
  ⭕ skill-web      {manager_dir}/skill-web/
```

---

#### 安装 Skill

1. **生成安装方案**：
```bash
python scripts/generate_plan.py --skill {skill_name} --action install --option full
```

解析返回的 JSON：
- `skill_name`: skill 名称
- `source_path`: 原始仓库路径
- `symlink_path`: 软连接目标路径
- `requires_admin`: 是否需要管理员权限（Windows）
- `windows_manual_command`: 手动创建命令（如需要）
- `pre_check_passed`: 预检查是否通过
- `pre_check_errors`: 错误信息列表

2. **Windows 特殊处理**：
如果 `requires_admin: true` 且用户选择手动模式，展示 `windows_manual_command`。

3. **展示方案并确认**：
```
📦 安装方案：{skill_name}
═══════════════════════════════════════════════════════

【安装位置】
  原始仓库：{source_path}
  软连接：  {symlink_path}

【选项】
  [A] 完全安装
  [B] 轻量安装
  [C] 仅克隆仓库
  [D] 取消

> A

是否确认执行安装？ [Y/n]：Y
```

4. **执行安装**：
```bash
python scripts/install.py --skill {skill_name} --option full
```

5. **展示结果**：
```
✅ 安装成功：{skill_name}

【安装位置】
  原始仓库：{source_path}
  软连接：  {symlink_path}

【使用方式】
  现在可以直接使用：@{skill_name} <指令>
```

---

#### 卸载 Skill

1. **生成卸载方案**：
```bash
python scripts/generate_plan.py --skill {skill_name} --action uninstall
```

解析返回的 JSON：
- `skill_name`: skill 名称
- `source_path`: 原始仓库路径
- `symlink_path`: 软连接路径
- `delete_commands`: 各平台的删除命令
- `pre_check_passed`: 预检查是否通过

2. **展示方案并确认**：
```
🗑️ 卸载方案：{skill_name}
═══════════════════════════════════════════════════════

【将执行的操作】
  ✅ 删除软连接：{symlink_path}

【将保留的内容】（如需删除，请手动执行）

  1. Skill 原始仓库
     位置：{source_path}
     删除命令：
       macOS/Linux: rm -rf '{source_path}'
       Windows:     Remove-Item -Recurse -Force "{source_path}"

═══════════════════════════════════════════════════════

是否确认删除软连接？ [Y/n]：Y
```

3. **执行卸载**：
```bash
python scripts/uninstall.py --skill {skill_name}
```

4. **展示结果**：
```
✅ 已卸载：{skill_name}

【操作结果】
  已删除软连接：{symlink_path}
  原始仓库保留：{source_path}
```

---

## Available Tools

### 命令行脚本

所有功能通过 `scripts/` 目录下的脚本提供：

#### 配置管理

| 脚本 | 用途 | 参数 | 输出 |
|------|------|------|------|
| `check_config.py` | 检查配置状态 | 无 | JSON 配置状态 |
| `init_config.py` | 初始化配置 | `--dir <路径>` | JSON 结果 |

#### Skill 查询

| 脚本 | 用途 | 参数 | 输出 |
|------|------|------|------|
| `list_skills.py` | 列出 skills | `--installed` / `--available` | JSON skill 列表 |

#### 方案生成

| 脚本 | 用途 | 参数 | 输出 |
|------|------|------|------|
| `generate_plan.py` | 生成安装/卸载方案 | `--skill <name> --action <install\|uninstall>` | JSON 方案 |

#### 执行操作

| 脚本 | 用途 | 参数 | 输出 |
|------|------|------|------|
| `install.py` | 安装 skill | `--skill <name> [--option <full\|light\|clone>]` | JSON 结果 |
| `uninstall.py` | 卸载 skill | `--skill <name>` | JSON 结果 |

---

## Directory Structure

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # 本文件（Kimi 交互指导）
│   ├── scripts/                    # ★ 可执行脚本（核心）
│   │   ├── check_config.py         # 检查配置
│   │   ├── init_config.py          # 初始化配置
│   │   ├── list_skills.py          # 列出 skills
│   │   ├── generate_plan.py        # 生成方案
│   │   ├── install.py              # 执行安装
│   │   ├── uninstall.py            # 执行卸载
│   │   └── lib/                    # 共享库
│   │       ├── config.py
│   │       ├── core.py
│   │       ├── path_manager.py
│   │       └── platform_utils.py
│   ├── src/                        # 旧代码（保留不使用）
│   └── data/                       # 运行时数据
│       └── config.json
└── ...                             # 其他 skills
```

---

## Design Principles

1. **脚本调用**：所有功能通过命令行脚本实现，无包导入问题
2. **Kimi 控制交互**：脚本只返回 JSON 数据，Kimi 负责所有展示和交互
3. **方案先行**：执行操作前先生成方案，用户确认后再执行
4. **非侵入式**：卸载仅删除软连接，保留原始仓库
5. **跨平台**：支持 macOS、Linux、Windows（Windows 需管理员权限创建软连接）
6. **无外部依赖**：仅使用 Python 标准库

---

## Platform Notes

### Windows

- 创建软连接需要**管理员权限**
- 无管理员权限时，通过 `--requires_admin` 字段检测，提供手动命令
- **Kimi 处理流程**：检测到 `platform='windows'` 且 `is_admin=false` 时，提供三选项

### macOS / Linux

- 普通用户权限即可创建软连接
- 建议使用相对路径软连接，便于项目迁移

---

## License

MIT
