# Kimi CLI Skill 安装原则

> 本文档记录了安装 Kimi CLI Skill 的完整原则和规范。
> 
> 文件位置：`{管理目录}/skill-install-project/install-principle.md`

---

## 原则 1：方案先行，确认后执行

### 说明
在任何安装操作之前，必须向用户提供完整的安装方案，经用户明确确认后方可执行。

### 方案内容必须包含
| 项目 | 说明 |
|------|------|
| **安装位置** | 原始文件位置 + 软连接位置 |
| **依赖清单** | 需要安装的所有依赖及其用途 |
| **操作步骤** | 详细的执行步骤 |
| **预估时间** | 大约需要多长时间 |
| **磁盘占用** | 下载大小 + 安装后大小 |
| **风险提示** | 可能影响现有配置的操作 |

### 执行流程
```
用户请求安装 skill
    ↓
提供完整方案（包含上述所有信息）
    ↓
用户确认 / 提出修改意见
    ↓
确认后执行
    ↓
每步验证并汇报
```

### 禁止行为
- ❌ 未经用户确认直接执行任何安装命令
- ❌ 隐瞒可能的风险或副作用
- ❌ 不提供预估时间和磁盘占用

---

## 原则 2：依赖解释 + 确认原则

### 说明
如需安装额外依赖（系统包、Python 包、Node.js 包等），必须先向用户详细解释，征得同意后再纳入方案。

### 解释内容清单
| 项目 | 必须说明 | 示例 |
|------|---------|------|
| **是什么** | 依赖名称和作用 | "Tectonic 是一个现代化的 LaTeX 编译器" |
| **为什么需要** | 哪个 skill 依赖它，缺少会怎样 | "kimi-pdf skill 使用 Tectonic 编译 LaTeX" |
| **多大** | 下载大小和安装后占用 | "下载约 50MB，安装后约 150MB" |
| **有无可替代** | 是否可用已有工具替代 | "您已有 MacTeX，但 skill 官方推荐 Tectonic" |
| **安装方式** | 官方推荐的安装命令 | "curl 安装脚本" |

### 用户选择权
- **选项 A**：安装官方推荐依赖 ✅（兼容性最好）
- **选项 B**：使用已有替代工具 ⚠️（需说明可能的功能差异）
- **选项 C**：跳过该 skill ❌（如果用户不想安装依赖）

### 示例对话
```
用户：我想安装 kimi-pdf skill

系统：安装此 skill 需要以下依赖：
  1. Playwright + Chromium（约 100MB）
     - 作用：HTML 转 PDF 渲染引擎
  2. Tectonic（约 50MB）
     - 作用：LaTeX 编译器
     - 注意：您已有 MacTeX，但 skill 官方推荐使用 Tectonic 以保证兼容性
     - 两者可共存，是否安装 Tectonic？

用户：安装 Tectonic
```

---

## 原则 3：临时文件分类处理

### 处理策略

| 类型 | 处理方式 | 示例 | 原因 |
|------|---------|------|------|
| **下载的安装包** | ❌ 立即清理 | `.zip`、`.tar.gz`、`.pkg` | 已解压/安装，无保留价值 |
| **中间目录** | ❌ 立即清理 | `kimi-skills-main/`（解压后的临时目录）| 已重命名/整理 |
| **下载日志** | ✅ 保留 | `/tmp/clone.log` | 便于排查网络问题 |
| **包管理器缓存** | ✅ 保留 | Homebrew、npm、pip 缓存 | 加速后续安装/更新 |
| **浏览器二进制** | ✅ 保留 | Playwright Chromium | 复用，避免重复下载 |
| **一次性脚本** | ❌ 清理 | 临时安装脚本 | 执行完毕即失效 |

### 原则
- **清理**：只针对"一次性安装介质"
- **保留**：可复用的依赖缓存（后续更新会用到）

---

## 原则 4：Skill 安装路径规范

### 核心设计

```
┌─────────────────────────────────────────────────────────────┐
│                    双位置分离设计                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   原始仓库（管理）        软连接（使用）                      │
│   ├─ 位置：当前工作目录    ├─ 位置：~/.kimi/skills/          │
│   ├─ 完整 git 仓库         ├─ 全局可用                       │
│   ├─ 便于 git pull 更新    ├─ Kimi CLI 读取入口              │
│   └─ 用户可手动修改        └─ 删除即卸载                     │
│                                                             │
│   示例：                                                     │
│   ./kimi-skills/  ──软连接──>  ~/.kimi/skills/kimi-docx      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 路径定义

| 变量 | 说明 | 示例 |
|------|------|------|
| `{管理目录}` | 本文件所在目录的父目录 | `/Users/{username}/Documents/kimi/` |
| `{项目目录}` | 当前工作目录（skill 仓库放在这里） | `{管理目录}/skill/` |
| `{全局配置}` | Kimi CLI 全局配置目录 | `~/.kimi/` 或 `%USERPROFILE%\.kimi\` |

### 安装规范

```
原始仓库位置：{项目目录}/[skill-repo-name]/
              ↓
软连接位置：  {全局配置}/skills/[skill-name]/
```

### 软连接必须使用相对路径

**正确**（相对路径）：
```bash
# 从 ~/.kimi/skills/ 指向 ../../Documents/kimi/skill/kimi-skills/skills/kimi-docx
ln -s ../../Documents/kimi/skill/kimi-skills/skills/kimi-docx kimi-docx
```

**错误**（绝对路径）：
```bash
ln -s /Users/{username}/Documents/kimi/skill/kimi-skills/skills/kimi-docx kimi-docx
# 项目移动后软连接会断裂
```

### 跨平台差异

| 平台 | 家目录变量 | 全局配置路径 | 软连接命令 |
|------|-----------|-------------|-----------|
| macOS/Linux | `~` 或 `$HOME` | `~/.kimi/` | `ln -s [源] [目标]` |
| Windows | `%USERPROFILE%` | `%USERPROFILE%\.kimi\` | `mklink [目标] [源]`（需管理员）|

---

## 原则 5：非侵入式安装

### 要求

| 项目 | 规范 | 说明 |
|------|------|------|
| **系统 PATH** | 不修改 | 不要将二进制文件安装到 `/usr/local/bin` 等系统目录 |
| **现有配置** | 不覆盖 | 不覆盖用户已有的 `.bashrc`、`.zshrc` 等配置文件 |
| **可回滚** | 必须可卸载 | 删除软连接和二进制文件即可完全卸载，不留残留 |

### 推荐做法

```bash
# Tectonic 安装到用户目录，不修改系统 PATH
~/tectonic

# 软连接放在 ~/.kimi/skills/，不影响其他工具
~/.kimi/skills/kimi-docx -> ../../Documents/kimi/skill/kimi-skills/skills/kimi-docx

# 卸载方式：删除软连接即可
rm ~/.kimi/skills/kimi-docx
```

---

## 原则 6：AGENTS.md 的双位置部署

### 说明
本原则文档（AGENTS.md）本身也需要遵循"双位置分离"设计。

### 部署结构

```
{管理目录}/                                    # 你指定的管理位置
├── AGENTS.md                                  # 原始文件（你编辑这里）
├── skill-install-project/                     # 本文件所在目录
│   └── install-principle.md                   # 详细原则说明
└── skill/                                     # skill 仓库放在这里
    └── kimi-skills/

{家目录}/                                      # Kimi CLI 读取位置
└── .kimi/
    ├── skills/                                # skill 软连接
    └── AGENTS.md -> {管理目录}/AGENTS.md      # 软连接（全局配置入口）
```

### 部署步骤

**步骤 1：创建原始文件**
```bash
# 将 AGENTS.md 放在管理目录
cat > {管理目录}/AGENTS.md << 'ENDOFFILE'
[原则内容]
ENDOFFILE
```

**步骤 2：创建软连接（macOS/Linux）**
```bash
mkdir -p ~/.kimi

# 计算相对路径：从 ~/.kimi/ 到 {管理目录}
# 示例：如果管理目录是 ~/Documents/kimi/
ln -s ../Documents/kimi/AGENTS.md ~/.kimi/AGENTS.md
```

**步骤 3：验证**
```bash
ls -la ~/.kimi/AGENTS.md
# 预期：AGENTS.md -> ../Documents/kimi/AGENTS.md

head ~/.kimi/AGENTS.md
# 预期：显示原则内容
```

### Windows 部署（用户手动执行）

用户需要在 Windows 上以管理员身份执行：

**PowerShell（管理员）**：
```powershell
$manageDir = "$env:USERPROFILE\Documents\kimi"  # 根据实际修改
$globalDir = "$env:USERPROFILE\.kimi"

New-Item -ItemType Directory -Path $globalDir -Force
New-Item -ItemType SymbolicLink -Path "$globalDir\AGENTS.md" -Target "$manageDir\AGENTS.md"
```

**CMD（管理员）**：
```cmd
mklink %USERPROFILE%\.kimi\AGENTS.md %USERPROFILE%\Documents\kimi\AGENTS.md
```

---

## 附录：安装检查清单

每次安装 skill 前，检查以下事项：

- [ ] 已向用户提供完整方案（路径、依赖、时间、空间）
- [ ] 用户已明确确认方案
- [ ] 所有依赖已向用户解释（是什么、为什么、多大、有无替代）
- [ ] 用户已确认依赖安装
- [ ] 已说明临时文件处理策略（清理哪些、保留哪些）
- [ ] 使用相对路径创建软连接
- [ ] 验证软连接可读
- [ ] 每步执行后立即验证
- [ ] 最终提供卸载方法

---

## 修订记录

| 日期 | 版本 | 修订内容 |
|------|------|---------|
| 2026-02-21 | v1.0 | 初始版本，确立六大原则 |
