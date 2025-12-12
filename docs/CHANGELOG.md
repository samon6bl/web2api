# 更新日志

## 2024-12-12 - 迁移到 Camoufox 并整理项目结构

### 主要变更

1. **浏览器引擎迁移**
   - 从 Chrome/Chromium 迁移到 Camoufox
   - 使用 Camoufox 的内置反指纹检测能力
   - 支持操作系统随机化

2. **项目结构重组**
   - 创建了清晰的目录结构：
     - `scripts/` - 可执行脚本
     - `utils/` - 工具模块
     - `examples/` - 示例代码
     - `docs/` - 文档
   - 所有文件按功能分类整理

3. **功能增强**
   - 支持操作系统随机化（random/windows/macos/linux）
   - 改进的 Camoufox 启动方式
   - 更好的进程管理（自动关闭）

4. **文档更新**
   - 更新 README 说明使用 Camoufox
   - 添加迁移指南
   - 添加项目结构说明

### 文件变更

#### 新增文件
- `scripts/save_cookie.py` - 使用 Camoufox 的主脚本
- `scripts/camoufox_launcher.py` - Camoufox 启动辅助脚本
- `scripts/pool_manager.py` - 用户数据池管理工具（移动）
- `utils/user_data_pool.py` - 用户数据池管理器（移动）
- `examples/debug_example.py` - 调试示例（移动）
- `examples/pool_example.py` - 用户数据池示例（移动）
- `docs/CAMOUFOX_MIGRATION.md` - 迁移指南
- `docs/playwright_debug_guide.md` - 调试指南（移动）
- `docs/DEBUG_QUICK_REFERENCE.md` - 快速参考（移动）
- `docs/USER_DATA_POOL_README.md` - 用户数据池文档（移动）
- `PROJECT_STRUCTURE.md` - 项目结构说明

#### 删除文件
- `save_cookie.py` - 已迁移到 `scripts/save_cookie.py`

#### 更新文件
- `requirements.txt` - 添加 camoufox 依赖
- `README.md` - 更新为 Camoufox 版本说明
- `.gitignore` - 更新忽略规则

### 使用方式变化

#### 旧版本（Chrome）
```bash
python save_cookie.py
python save_cookie.py --pool
```

#### 新版本（Camoufox）
```bash
python scripts/save_cookie.py
python scripts/save_cookie.py --pool
python scripts/save_cookie.py --os random
python scripts/save_cookie.py --os "windows,macos,linux"
```

### 依赖变化

新增依赖：
- `camoufox>=0.1.0`

安装命令：
```bash
pip install -r requirements.txt
playwright install firefox  # 不再需要 chromium
```

### 注意事项

- 旧的 Chrome profile 数据不会被自动迁移
- Cookie 文件格式兼容，可以直接使用
- 如果遇到问题，可以查看 `docs/CAMOUFOX_MIGRATION.md`


