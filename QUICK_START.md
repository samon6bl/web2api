# 快速开始指南

## 安装

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Playwright Firefox（用于连接 Camoufox）
playwright install firefox
```

## 基本使用

### 保存 Cookie

```bash
# 基本使用（使用 Camoufox，操作系统随机）
python scripts/save_cookie.py

# 指定操作系统
python scripts/save_cookie.py --os windows
python scripts/save_cookie.py --os "windows,macos,linux"  # 从列表随机

# 使用用户数据池
python scripts/save_cookie.py --pool

# 无头模式
python scripts/save_cookie.py --headless
```

### 仅加载 Cookie

```bash
# 加载最新的 cookie 并打开网站
python scripts/save_cookie.py load

# 使用用户数据池
python scripts/save_cookie.py load --pool
```

## 管理用户数据池

```bash
# 列出所有 profile
python scripts/pool_manager.py list

# 创建新 profile
python scripts/pool_manager.py create

# 查看 profile 信息
python scripts/pool_manager.py info profile_id

# 删除 profile
python scripts/pool_manager.py delete profile_id
```

## 项目结构

```
deepseek/
├── scripts/          # 可执行脚本
├── utils/            # 工具模块
├── examples/         # 示例代码
├── docs/             # 文档
└── cookies/         # Cookie 文件
```

## 更多信息

- 完整文档: `README.md`
- 项目结构: `PROJECT_STRUCTURE.md`
- 迁移指南: `docs/CAMOUFOX_MIGRATION.md`
- 调试指南: `docs/playwright_debug_guide.md`
- 用户数据池: `docs/USER_DATA_POOL_README.md`


