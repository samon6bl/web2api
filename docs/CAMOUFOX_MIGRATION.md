# 从 Chrome 迁移到 Camoufox

本项目已从 Chrome 浏览器迁移到 Camoufox 浏览器，以获得更强的反指纹检测能力。

## 主要变化

### 1. 浏览器引擎

- **之前**: Chromium (Chrome)
- **现在**: Camoufox (基于 Firefox，增强反指纹)

### 2. 反指纹策略

#### Chrome 版本（旧）
- 手动配置 User-Agent
- JavaScript 注入反检测脚本
- 手动设置浏览器参数
- 固定的指纹特征

#### Camoufox 版本（新）
- 自动生成真实的 User-Agent
- 底层 C++ 修改，无需 JavaScript 注入
- 自动指纹随机化（操作系统、屏幕、WebGL、字体等）
- 基于真实设备指纹数据库

### 3. 文件结构变化

```
旧结构:
├── save_cookie.py
├── user_data_pool.py
├── pool_manager.py
└── ...

新结构:
├── scripts/
│   ├── save_cookie.py      # 使用 Camoufox
│   └── pool_manager.py
├── utils/
│   └── user_data_pool.py
├── examples/
│   ├── debug_example.py
│   └── pool_example.py
└── docs/
    ├── playwright_debug_guide.md
    └── ...
```

### 4. 使用方法变化

#### 旧版本（Chrome）
```bash
python save_cookie.py
python save_cookie.py --pool
```

#### 新版本（Camoufox）
```bash
python scripts/save_cookie.py
python scripts/save_cookie.py --pool
python scripts/save_cookie.py --os random  # 操作系统随机化
python scripts/save_cookie.py --os "windows,macos,linux"  # 从列表随机
```

### 5. 依赖变化

#### 旧版本
```txt
playwright==1.40.0
```

#### 新版本
```txt
playwright==1.40.0
camoufox>=0.1.0
```

需要安装：
```bash
pip install camoufox
playwright install firefox  # 不再需要 chromium
```

### 6. 数据存储变化

#### Chrome 版本
- 使用 `browser_profile/` 目录存储完整的 Chrome 用户数据
- 包含所有 Chrome 配置、扩展等

#### Camoufox 版本
- 使用 `storage_state.json` 文件存储 cookies 和 localStorage
- 更轻量级，只保存必要的数据
- 仍然支持用户数据池管理

## 迁移步骤

1. **安装新依赖**
   ```bash
   pip install -r requirements.txt
   playwright install firefox
   ```

2. **更新脚本调用**
   - 将 `python save_cookie.py` 改为 `python scripts/save_cookie.py`
   - 将 `python pool_manager.py` 改为 `python scripts/pool_manager.py`

3. **数据迁移（可选）**
   - 旧的 `browser_profile/` 目录可以保留，但不被新版本使用
   - Cookie 文件（`cookies/`）可以直接使用，无需迁移
   - 如果需要，可以从旧的 profile 中提取 cookies

## 优势

1. **更强的反检测能力**
   - 底层 C++ 修改比 JavaScript 注入更难检测
   - 自动指纹随机化，每次启动可能不同

2. **更真实的浏览器指纹**
   - 基于真实设备指纹数据库
   - 操作系统、屏幕、WebGL、字体等自动匹配

3. **更简单的配置**
   - 无需手动设置 User-Agent
   - 无需手动注入反检测脚本
   - 只需指定操作系统模拟策略

4. **更好的性能**
   - 更轻量级的数据存储
   - 更快的启动速度

## 注意事项

- Camoufox 基于 Firefox，某些 Chrome 特定的功能可能不可用
- 如果遇到兼容性问题，可以查看 Camoufox 官方文档
- 旧的 Chrome profile 数据不会被自动迁移，需要手动处理

## 故障排查

### Camoufox 未安装
```bash
pip install camoufox
```

### 连接失败
确保 Camoufox 已正确启动，检查端口 9222 是否被占用。

### 兼容性问题
如果遇到网站兼容性问题，可以尝试：
1. 调整操作系统模拟设置
2. 检查 Camoufox 版本是否最新
3. 查看 Camoufox 官方文档


