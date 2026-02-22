---
name: skill-installer
description: 标准化安装、卸载、管理 Kimi CLI Skills 的工具。提供跨平台的 skill 管理能力，支持 macOS、Linux 和 Windows 系统。
---

# Skill Installer

## Description

标准化安装、卸载、管理 Kimi CLI Skills 的工具。提供跨平台的 skill 管理能力，支持 macOS、Linux 和 Windows 系统。

## Features

- **标准化安装**：通过软连接将 skill 注册到 Kimi CLI
- **非侵入式卸载**：卸载时仅删除软连接，保留原始仓库
- **依赖管理**：分析 skill 依赖，提供安装选项
- **跨平台支持**：支持 macOS、Linux 和 Windows
- **配置持久化**：管理目录配置保存在 skill 内部

## Trigger

当用户想要：
- 安装新的 skill
- 卸载已安装的 skill
- 查看已安装/可安装的 skill 列表
- 配置 skill 管理目录

## Commands

### 安装 Skill

```bash
@skill-installer install <skill-name> [--option {full,light,clone-only}]
```

**安装选项**：
- `full` (默认): 完全安装，包括所有依赖
- `light`: 轻量安装，仅必要依赖
- `clone-only`: 仅创建软连接，不处理依赖

**示例**：
- `@skill-installer install skill-pdf` - 安装 skill-pdf
- `@skill-installer install skill-xlsx --option light` - 轻量安装

### 卸载 Skill

```bash
@skill-installer uninstall <skill-name>
```

**说明**：
- 仅删除软连接（`~/.kimi/skills/{skill-name}`）
- 保留原始仓库，提供手动删除命令

**示例**：
- `@skill-installer uninstall skill-pdf` - 卸载 skill-pdf

### 列出 Skills

```bash
@skill-installer list [--installed] [--available]
```

**选项**：
- `--installed`, `-i`: 仅显示已安装的 skills
- `--available`, `-a`: 仅显示可安装的 skills

**示例**：
- `@skill-installer list` - 显示所有 skills
- `@skill-installer list --available` - 显示可安装的 skills

### 查看 Skill 详情

```bash
@skill-installer info <skill-name>
```

**示例**：
- `@skill-installer info skill-pdf` - 查看 skill-pdf 的详细信息

### 配置管理

```bash
@skill-installer config [--show] [--reset]
```

**选项**：
- `--show`, `-s`: 显示当前配置
- `--reset`, `-r`: 重置配置

**配置说明**：
- **管理目录**：存放所有 skill 仓库的根目录
- **配置文件**：`skill-installer/data/config.json`

## Installation

### 首次使用

1. 运行任意命令触发初始配置：
   ```bash
   python -m skill-installer list
   ```

2. 选择管理目录：
   - 使用当前项目目录
   - 或自定义其他目录

3. 确认配置后即可使用

### 手动安装到 Kimi CLI

```bash
# 创建软连接（macOS/Linux）
ln -s /path/to/skill-install-project/skill-installer ~/.kimi/skills/skill-installer

# Windows（管理员权限 PowerShell）
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
  -Target "C:\path\to\skill-install-project\skill-installer"
```

## Directory Structure

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # 本文件
│   ├── src/                        # 源代码
│   │   ├── __init__.py
│   │   ├── __main__.py             # 入口点
│   │   ├── cli.py                  # 命令行接口
│   │   ├── core.py                 # 核心逻辑
│   │   ├── config.py               # 配置管理
│   │   ├── path_manager.py         # 路径管理
│   │   ├── platform_utils.py       # 跨平台工具
│   │   └── validator.py            # 安装验证
│   └── data/                       # 运行时数据
│       └── config.json             # 配置文件
├── skill-pdf/                      # 其他 skills...
├── skill-xlsx/
└── ...
```

## Requirements

- Python 3.7+
- 仅使用标准库，无需额外依赖

## Platform Notes

### Windows

- 创建软连接需要**管理员权限**
- 无管理员权限时，工具会提供手动创建指令
- 或使用目录拷贝代替（不推荐，占用双倍空间）

### macOS / Linux

- 普通用户权限即可创建软连接
- 建议使用相对路径软连接，便于项目迁移

## Principles

遵循 `install-principle.md` 中的六大原则：

1. **方案先行**：安装前展示完整方案，用户确认后执行
2. **依赖解释**：清晰列出依赖及其作用、大小
3. **路径规范**：使用相对路径软连接
4. **非侵入式**：卸载仅删除软连接，保留原始仓库
5. **双位置分离**：区分原始仓库和软连接位置
6. **可回滚**：安装失败自动回滚

## License

MIT
