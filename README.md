# Skill Installer（Kimi 交互式）

标准化安装、卸载、管理 Kimi CLI Skills 的**Kimi 交互式**工具。

通过自然语言与 Kimi 对话，完成 skill 的安装、卸载和管理。

---

## ⚠️ 安装注意（必读）

本项目采用**子目录结构**，安装时必须软连接 `skill-installer` 子目录，**不要**软连接项目根目录。

```
skill-install-kimi/              ← 项目根目录（管理目录）
├── skill-installer/             ← ★ 创建软连接指向这里
│   ├── SKILL.md                 # Kimi 读取的入口
│   ├── src/                     # 源代码
│   └── data/                    # 配置文件
├── tests/                       # 测试代码
├── README.md                    # 用户文档
└── AGENTS.md                    # 开发文档
```

### 安装步骤

**Step 1**: 克隆仓库
```bash
git clone <repository-url> skill-install-kimi
cd skill-install-kimi
```

**Step 2**: 创建软连接（指向 `skill-installer` 子目录）

macOS / Linux:
```bash
ln -s $(pwd)/skill-installer ~/.kimi/skills/skill-installer
```

Windows（管理员 PowerShell）:
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.kimi\skills\skill-installer" `
  -Target "$(pwd)\skill-installer"
```

**Step 3**: 验证安装
```bash
kimi
# 然后输入：
@skill-installer list
# 或对话方式：
列出我的 skills
```

### 常见错误

❌ **错误**：软连接整个项目根目录
```bash
ln -s /path/to/skill-install-kimi ~/.kimi/skills/skill-installer  # 错误！
```

✅ **正确**：软连接 `skill-installer` 子目录
```bash
ln -s /path/to/skill-install-kimi/skill-installer ~/.kimi/skills/skill-installer
```

### 为什么没有 skill-installer 也能安装？

如果你还没有 skill-installer，需要**手动创建软连接**（见上方 Step 2）。

安装完成后，就可以通过 Kimi 对话管理其他 skills 了。

---

## 快速开始

直接告诉 Kimi 你的需求：

```
帮我安装 skill-pdf
```

```
列出我安装的所有 skills
```

```
卸载 skill-xxx
```

```
更改 skill 管理目录
```

Kimi 会：
1. 展示安装/卸载方案
2. 询问你的确认 `[Y/n]`
3. 执行操作并反馈结果

---

## 跨平台支持

| 平台 | 支持状态 | 说明 |
|------|----------|------|
| macOS | ✅ 完全支持 | 原生软连接，普通用户权限 |
| Linux | ✅ 完全支持 | 原生软连接，普通用户权限 |
| Windows | ⚠️ 需要管理员权限 | 提供降级方案（手动命令）|

### Windows 用户特别提示

由于 Windows 创建软连接需要管理员权限，Kimi 会：

1. **自动检测权限**：判断是否有管理员权限
2. **提供选项**：
   - [A] 退出，以管理员身份重新运行 Kimi CLI
   - [B] 获取手动创建软连接的 PowerShell/CMD 命令
   - [C] 取消操作
3. **引导完成**：如选择手动创建，提供详细命令并继续后续配置

---

## 交互示例

### 安装 Skill

```
用户：安装 skill-pdf

Kimi：📦 安装方案：skill-pdf
      ═══════════════════════════════════════════════════════
      
      【安装位置】
        原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
        软连接：  ~/.kimi/skills/skill-pdf
      
      【选项】
        [A] 完全安装  [B] 轻量安装  [C] 仅克隆  [D] 取消
      
      > A
      
      是否确认执行安装？ [Y/n]：Y
      
      ✅ 安装成功！
```

### Windows 权限处理

```
用户：安装 skill-pdf

Kimi：⚠️ 检测到 Windows，创建软连接需要管理员权限
      
      【选项】
        [A] 退出以管理员重开  
        [B] 获取手动创建软连接的命令  
        [C] 取消
      
      > B
      
      ═══════════════════════════════════════════════════════
      手动创建软连接指令
      ═══════════════════════════════════════════════════════
      
      请以管理员身份打开 PowerShell，执行：
      
      New-Item -ItemType SymbolicLink `
        -Path "$env:USERPROFILE\.kimi\skills\skill-pdf" `
        -Target "C:\Users\{username}\Documents\kimi\skills\skill-pdf"
      
      完成后告诉我"已手动创建"，我继续完成配置记录。
```

### 卸载 Skill

```
用户：卸载 skill-pdf

Kimi：🗑️ 卸载方案：skill-pdf
      ═══════════════════════════════════════════════════════
      
      【将执行的操作】
        ✅ 删除软连接：~/.kimi/skills/skill-pdf
      
      【将保留的内容】（如需删除，请手动执行）
        📁 原始仓库：/Users/{username}/Documents/kimi/skills/skill-pdf/
           删除命令：rm -rf '/Users/{username}/Documents/kimi/skills/skill-pdf/'
      
      是否确认删除软连接？ [Y/n]：Y
      
      ✅ 已删除软连接
```

---

## 目录结构

```
skill-install-project/              # 管理目录
├── skill-installer/                # 本 skill
│   ├── SKILL.md                    # Skill 定义（Kimi 读取）
│   ├── src/                        # 源代码
│   │   ├── api.py                  # ★ Kimi API 层（核心）
│   │   ├── core.py                 # 核心逻辑
│   │   ├── config.py               # 配置管理
│   │   ├── path_manager.py         # 路径管理
│   │   ├── platform_utils.py       # 跨平台工具
│   │   └── validator.py            # 安装验证
│   └── data/                       # 运行时数据
│       └── config.json             # 配置文件
└── ...                             # 其他 skills
```

---

## 设计原则

遵循六大原则：

1. **方案先行**：安装/卸载前展示完整方案，用户确认后执行
2. **依赖解释**：清晰列出依赖及其作用、大小
3. **路径规范**：使用相对路径软连接
4. **非侵入式**：卸载仅删除软连接，保留原始仓库
5. **双位置分离**：区分原始仓库和软连接位置
6. **可回滚**：安装失败自动回滚

---

## 技术说明

### CLI 模式（保留备用）

项目保留了 CLI 模式代码（`src/cli.py`, `src/cli_ui.py`），但不作为默认使用方式。

如需使用 CLI 模式，可直接运行：

```bash
python -m skill-installer install <skill-name>
python -m skill-installer uninstall <skill-name>
python -m skill-installer list
```

### API 层

Kimi 通过 `skill_installer.api` 模块调用功能：

```python
from skill_installer import api

# 检查配置
status = api.validate_setup()

# 生成安装方案
plan = api.generate_install_plan("skill-pdf", option="full")

# 执行安装
result = api.install_skill("skill-pdf", option="full")
```

---

## 开发

### 项目结构

```
skill-installer/
├── src/
│   ├── __init__.py
│   ├── api.py              # ★ Kimi API 层（主入口）
│   ├── cli.py              # CLI 入口（保留不使用）
│   ├── cli_ui.py           # CLI 交互层（保留不使用）
│   ├── core.py             # 核心逻辑
│   ├── config.py           # 配置管理
│   ├── dependency.py       # 依赖分析
│   ├── path_manager.py     # 路径管理
│   ├── platform_utils.py   # 跨平台工具
│   └── validator.py        # 验证器
├── data/                   # 运行时数据（.gitignore）
├── SKILL.md                # Skill 定义（Kimi 读取）
└── README.md               # 本文件
```

### 本地测试

```bash
# 运行测试
python -m unittest discover -s tests -v
```

---

## 许可证

MIT
