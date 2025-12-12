# 项目结构说明

## 目录结构

```
deepseek/
├── scripts/                    # 可执行脚本
│   ├── save_cookie.py         # 主脚本：使用 Camoufox 保存/加载 cookie
│   └── pool_manager.py        # 用户数据池管理 CLI 工具
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   └── user_data_pool.py     # 用户数据池管理器
│
├── examples/                  # 示例代码
│   ├── debug_example.py      # Playwright 调试示例
│   └── pool_example.py       # 用户数据池使用示例
│
├── docs/                      # 文档
│   ├── playwright_debug_guide.md      # Playwright 调试完整指南
│   ├── DEBUG_QUICK_REFERENCE.md       # 调试快速参考
│   ├── USER_DATA_POOL_README.md      # 用户数据池使用文档
│   └── CAMOUFOX_MIGRATION.md         # Chrome 到 Camoufox 迁移指南
│
├── cookies/                   # Cookie 文件存储目录
│   └── deepseek_cookies_*.json
│
├── browser_profile/           # 浏览器 profile（不使用 pool 时）
│   └── storage_state.json
│
├── user_data_pool/            # 用户数据池目录（使用 pool 时）
│   ├── metadata.json
│   └── profile_*/
│       └── storage_state.json
│
├── AIstudioProxyAPI-main/     # 参考项目（不修改）
│   └── ...
│
├── requirements.txt           # Python 依赖
├── README.md                  # 项目主文档
├── PROJECT_STRUCTURE.md       # 本文件
└── .gitignore                # Git 忽略配置
```

## 文件说明

### 脚本文件 (scripts/)

#### `save_cookie.py`
主脚本，使用 Camoufox 浏览器打开 deepseek.com 并保存 cookie。

**功能**:
- 使用 Camoufox 提供反指纹检测
- 支持 cookie 保存和加载
- 支持用户数据池管理
- 支持操作系统随机化

**使用**:
```bash
python scripts/save_cookie.py
python scripts/save_cookie.py --pool --os random
```

#### `pool_manager.py`
用户数据池管理 CLI 工具。

**功能**:
- 列出所有 profile
- 创建/删除 profile
- 查看 profile 信息
- 清理非活跃 profile

**使用**:
```bash
python scripts/pool_manager.py list
python scripts/pool_manager.py create
```

### 工具模块 (utils/)

#### `user_data_pool.py`
用户数据池管理器，支持多个独立的浏览器 profile。

**功能**:
- Profile 创建和管理
- 活跃状态跟踪
- 自动清理
- 线程安全

### 示例代码 (examples/)

#### `debug_example.py`
Playwright 调试示例，演示各种调试技巧。

#### `pool_example.py`
用户数据池使用示例，演示如何并行使用多个 profile。

### 文档 (docs/)

#### `playwright_debug_guide.md`
完整的 Playwright 调试指南，包含所有调试方法和技巧。

#### `DEBUG_QUICK_REFERENCE.md`
调试快速参考，常用命令速查。

#### `USER_DATA_POOL_README.md`
用户数据池完整文档，包含 API 文档和使用场景。

#### `CAMOUFOX_MIGRATION.md`
从 Chrome 迁移到 Camoufox 的指南。

## 数据目录

### `cookies/`
存储所有保存的 cookie 文件，按时间戳命名。

### `browser_profile/`
单一浏览器 profile 目录（不使用 pool 时）。

### `user_data_pool/`
用户数据池目录，包含多个独立的 profile。

## 参考项目

### `AIstudioProxyAPI-main/`
参考项目，不进行修改。用于学习和参考 Camoufox 的使用方式。

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   playwright install firefox
   ```

2. **运行脚本**
   ```bash
   python scripts/save_cookie.py
   ```

3. **查看文档**
   - 主文档: `README.md`
   - 调试指南: `docs/playwright_debug_guide.md`
   - 用户数据池: `docs/USER_DATA_POOL_README.md`

