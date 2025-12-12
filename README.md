# DeepSeek Cookie 保存工具

使用 **Camoufox** 浏览器打开 deepseek.com，等待你登录后自动保存 cookie。Camoufox 提供增强的反指纹检测能力，比普通浏览器更难被检测。

## 功能特性

- ✅ **使用 Camoufox 浏览器**：基于 Firefox，内置反指纹检测，通过底层 C++ 修改伪装设备指纹
- ✅ **Cookie 文件夹管理**：所有 cookie 保存在 `cookies/` 文件夹中，便于管理
- ✅ **自动加载最新 Cookie**：自动识别并加载最新的 cookie 文件（按时间戳排序）
- ✅ **时间戳命名**：Cookie 文件按时间戳命名（`deepseek_cookies_YYYYMMDD_HHMMSS.json`），便于识别最新文件
- ✅ **持久化用户 Profile**：自动保存浏览器配置和登录状态，下次运行无需重新登录
- ✅ **用户数据池管理**：支持多个独立的用户数据目录，避免并发冲突
- ✅ **操作系统随机化**：支持随机或指定操作系统模拟（Windows/macOS/Linux）
- ✅ **自动保存 Cookie**：登录后自动保存所有 cookie 到 JSON 文件

## 关于 Camoufox

本项目使用 [Camoufox](https://camoufox.com/) 来提供具有增强反指纹检测能力的浏览器实例。

- **核心目标**: 模拟真实用户流量，避免被网站识别为自动化脚本或机器人
- **实现方式**: Camoufox 基于 Firefox，通过修改浏览器底层 C++ 实现来伪装设备指纹（如屏幕、操作系统、WebGL、字体等），而不是通过容易被检测到的 JavaScript 注入
- **指纹随机化**: 支持操作系统、屏幕分辨率、WebGL、字体等指纹的自动随机化
- **Playwright 兼容**: Camoufox 提供了与 Playwright 兼容的接口

## 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（Firefox，用于连接 Camoufox）
playwright install firefox
```

## 使用方法

### 模式 1：登录并保存 Cookie（默认）

```bash
# 基本使用
python scripts/save_cookie.py

# 使用用户数据池
python scripts/save_cookie.py --pool

# 指定操作系统模拟
python scripts/save_cookie.py --os windows
python scripts/save_cookie.py --os "windows,macos,linux"  # 从列表中随机选择

# 无头模式
python scripts/save_cookie.py --headless
```

### 模式 2：仅加载 Cookie 并打开网站

```bash
# 基本使用
python scripts/save_cookie.py load

# 使用用户数据池
python scripts/save_cookie.py load --pool

# 指定 profile
python scripts/save_cookie.py load --pool --profile-id my_profile
```

## 命令行参数

- `mode`: 运行模式，`save`（保存cookie）或 `load`（仅加载cookie），默认 `save`
- `--pool`: 使用用户数据池
- `--profile-id`: 指定 profile ID（仅在使用 pool 时有效）
- `--os`: 操作系统模拟，可选值：
  - `random` - 随机选择（默认）
  - `windows` - 模拟 Windows
  - `macos` - 模拟 macOS
  - `linux` - 模拟 Linux
  - `"windows,macos,linux"` - 从列表中随机选择
- `--headless`: 使用无头模式

## Cookie 管理

- **Cookie 文件夹**：所有 cookie 文件保存在 `cookies/` 目录中
- **文件命名**：按时间戳命名，格式为 `deepseek_cookies_YYYYMMDD_HHMMSS.json`
- **自动识别最新文件**：按文件名自动排序，自动识别最新的 cookie 文件
- **只加载最新**：脚本只会加载最新的 cookie 文件（按时间戳排序后的最后一个），确保使用最新的登录状态

## 用户数据池管理

使用 `scripts/pool_manager.py` 管理用户数据池：

```bash
# 列出所有 profile
python scripts/pool_manager.py list

# 创建新 profile
python scripts/pool_manager.py create

# 查看 profile 信息
python scripts/pool_manager.py info profile_id

# 删除 profile
python scripts/pool_manager.py delete profile_id

# 清理非活跃 profile
python scripts/pool_manager.py cleanup --days 7
```

详细文档请查看 `docs/USER_DATA_POOL_README.md`

## 项目结构

```
deepseek/
├── scripts/              # 脚本文件
│   ├── save_cookie.py   # 主脚本（使用 Camoufox）
│   └── pool_manager.py  # 用户数据池管理工具
├── utils/                # 工具模块
│   ├── __init__.py
│   └── user_data_pool.py # 用户数据池管理器
├── examples/             # 示例代码
│   ├── debug_example.py  # Playwright 调试示例
│   └── pool_example.py   # 用户数据池使用示例
├── docs/                 # 文档
│   ├── playwright_debug_guide.md
│   ├── DEBUG_QUICK_REFERENCE.md
│   └── USER_DATA_POOL_README.md
├── cookies/              # Cookie 文件目录
├── browser_profile/      # 浏览器 profile 目录（不使用 pool 时）
├── user_data_pool/       # 用户数据池目录（使用 pool 时）
├── requirements.txt      # Python 依赖
└── README.md            # 本文件
```

## 注意事项

- 确保已安装 Python 3.7+
- 首次运行需要安装 Camoufox：`pip install camoufox`
- 需要安装 Playwright Firefox：`playwright install firefox`
- Cookie 和 profile 文件包含敏感信息，请妥善保管
- 如需清除登录状态，删除对应的 profile 目录即可
- 如需清除所有 cookie，删除 `cookies/` 目录即可

## 与 Chrome 版本的区别

本项目已从 Chrome 迁移到 Camoufox，主要优势：

1. **更强的反指纹能力**：通过底层 C++ 修改，比 JavaScript 注入更难检测
2. **自动指纹随机化**：操作系统、屏幕、WebGL、字体等自动随机化
3. **更真实的浏览器指纹**：基于真实设备指纹数据库
4. **无需手动配置**：不需要手动设置 User-Agent、反检测脚本等

## 故障排查

### Camoufox 未安装

```bash
pip install camoufox
```

### 连接 Camoufox 失败

确保 Camoufox 已正确启动。如果使用自定义端口，需要修改脚本中的 WebSocket 端点。

### 查看调试指南

详细调试方法请查看 `docs/playwright_debug_guide.md` 和 `docs/DEBUG_QUICK_REFERENCE.md`
