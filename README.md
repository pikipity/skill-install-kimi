# Skill Installer

标准化安装、卸载、管理 Kimi CLI Skills 的工具。

## 功能特性

- **标准化安装**：通过软连接将 skill 注册到 Kimi CLI
- **非侵入式卸载**：卸载时仅删除软连接，保留原始仓库
- **跨平台支持**：支持 macOS、Linux 和 Windows
- **配置管理**：管理目录配置保存在 skill 内部，随项目迁移

## 快速开始

### 安装本 Skill

```bash
# macOS / Linux
ln -s /path/to/skill-install-project/skill-installer ~/.kimi/skills/skill-installer

# Windows（管理员 PowerShell）
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
  -Target "C:\path\to\skill-install-project\skill-installer"
```

### 首次使用

运行任意命令触发初始配置：

```bash
@skill-installer list
```

按提示选择管理目录后即可使用。

## 命令参考

### 安装 Skill

```bash
@skill-installer install <skill-name>
```

**选项**：
- `--option full` - 完全安装（默认）
- `--option light` - 轻量安装
- `--option clone-only` - 仅克隆

### 卸载 Skill

```bash
@skill-installer uninstall <skill-name>
```

仅删除软连接，保留原始仓库。

### 列出 Skills

```bash
# 列出所有
@skill-installer list

# 仅列出已安装
@skill-installer list --installed

# 仅列出可安装
@skill-installer list --available
```

### 查看详情

```bash
@skill-installer info <skill-name>
```

### 配置管理

```bash
# 显示配置
@skill-installer config --show

# 重置配置
@skill-installer config --reset
```

## 目录结构

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # Skill 定义
│   ├── src/                        # 源代码
│   │   ├── cli.py                  # 命令行接口
│   │   ├── core.py                 # 核心逻辑
│   │   ├── config.py               # 配置管理
│   │   ├── path_manager.py         # 路径管理
│   │   ├── platform_utils.py       # 跨平台工具
│   │   └── validator.py            # 安装验证
│   └── data/                       # 运行时数据
│       └── config.json             # 配置文件
└── ...                             # 其他 skills
```

## 设计原则

遵循六大原则：

1. **方案先行**：安装前展示完整方案，用户确认后执行
2. **依赖解释**：清晰列出依赖及其作用、大小
3. **路径规范**：使用相对路径软连接
4. **非侵入式**：卸载仅删除软连接，保留原始仓库
5. **双位置分离**：区分原始仓库和软连接位置
6. **可回滚**：安装失败自动回滚

## 平台说明

### Windows

- 创建软连接需要**管理员权限**
- 无权限时工具会提供手动创建指令

### macOS / Linux

- 普通用户权限即可创建软连接
- 建议使用相对路径，便于项目迁移

## 开发

### 项目结构

```
skill-installer/
├── src/
│   ├── __init__.py
│   ├── __main__.py         # 入口点
│   ├── cli.py              # CLI 接口
│   ├── core.py             # 核心逻辑
│   ├── config.py           # 配置管理
│   ├── dependency.py       # 依赖分析
│   ├── path_manager.py     # 路径管理
│   ├── platform_utils.py   # 跨平台工具
│   └── validator.py        # 验证器
├── data/                   # 运行时数据（.gitignore）
├── SKILL.md                # Skill 定义
└── README.md               # 本文件
```

### 本地测试

```bash
# 运行
python -m skill-installer list

# 安装 skill
python -m skill-installer install some-skill

# 卸载 skill
python -m skill-installer uninstall some-skill
```

## 许可证

MIT
