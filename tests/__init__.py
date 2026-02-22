# skill-installer 测试包
"""
测试目录结构：

tests/                          # 项目根目录下的测试目录（不在 skill-installer 内）
├── __init__.py
├── test_import_helper.py       # 方案 D：动态导入辅助
├── test_platform_utils.py      # 跨平台工具测试
├── test_config.py              # 配置管理测试
├── test_path_manager.py        # 路径管理测试
├── test_validator.py           # 验证器测试
├── test_core.py                # 核心逻辑测试
└── test_isolated.py            # L2 隔离功能测试

导入方式（方案 D）：
所有测试文件开头必须先导入 helper：
    import test_import_helper
    from skill_installer.src.xxx import Xxx

这样无需符号链接，也无需修改源代码。

测试原则：
1. 零侵入：不修改现有的 ~/.kimi/ 目录
2. 零依赖：不使用已安装的 skill
3. 自包含：测试用的 skill 临时创建，测试完删除
4. 可还原：测试结束后系统状态与测试前完全一致
5. 目录隔离：测试目录必须在项目根目录，不在 skill-installer 内
"""
