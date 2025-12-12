# Chrome 用户数据池管理系统

## 概述

Chrome 用户数据池管理系统允许你管理多个独立的 Chrome 用户数据目录（profile），支持：
- 多个并行爬虫实例，每个使用独立的 profile
- 从本地 Chrome 用户数据复制创建新 profile
- 自动管理 profile 的活跃状态
- Profile 的创建、删除、查询等操作

## 功能特性

- ✅ **多 Profile 管理**：支持创建、删除、查询多个 profile
- ✅ **从本地 Chrome 复制**：可以从你本地使用的 Chrome 用户数据创建 profile
- ✅ **活跃状态管理**：自动跟踪哪些 profile 正在使用
- ✅ **自动清理**：可以清理长时间未使用的 profile
- ✅ **线程安全**：支持多线程/多进程并发使用

## 快速开始

### 1. 基本使用

```python
from user_data_pool import get_user_data_pool

# 获取用户数据池实例
pool = get_user_data_pool()

# 从本地 Chrome 用户数据创建 profile
profile_dir = pool.create_profile_from_local()

# 或创建新的空 profile
profile_dir = pool.create_new_profile()

# 使用 profile 启动浏览器
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False
    )
    # 使用浏览器...
```

### 2. 在 save_cookie.py 中使用

```bash
# 使用用户数据池模式
python save_cookie.py --pool

# 从本地 Chrome 用户数据创建并使用
python save_cookie.py --pool --from-local

# 使用指定的 profile
python save_cookie.py --pool --profile-id my_profile

# 仅加载模式
python save_cookie.py load --pool
```

### 3. 使用 CLI 工具管理

```bash
# 列出所有 profile
python pool_manager.py list

# 创建新 profile
python pool_manager.py create

# 从本地 Chrome 创建
python pool_manager.py create --from-local

# 创建指定 ID 的 profile
python pool_manager.py create --profile-id my_profile

# 查看 profile 信息
python pool_manager.py info my_profile

# 删除 profile
python pool_manager.py delete my_profile

# 强制删除（即使正在使用）
python pool_manager.py delete my_profile --force

# 清理 7 天前创建的非活跃 profile
python pool_manager.py cleanup --days 7
```

## API 文档

### ChromeUserDataPool 类

#### 初始化

```python
pool = ChromeUserDataPool(pool_dir="user_data_pool", max_profiles=10)
```

- `pool_dir`: 用户数据池目录（默认: "user_data_pool"）
- `max_profiles`: 最大 profile 数量（默认: 10）

#### 主要方法

##### `create_profile_from_local(profile_id=None)`

从本地 Chrome 用户数据创建新的 profile。

```python
profile_dir = pool.create_profile_from_local()
# 或指定 ID
profile_dir = pool.create_profile_from_local("my_profile")
```

##### `create_new_profile(profile_id=None)`

创建新的空 profile。

```python
profile_dir = pool.create_new_profile()
```

##### `get_profile(profile_id)`

获取指定 profile 的路径。

```python
profile_dir = pool.get_profile("my_profile")
if profile_dir:
    print(f"Profile 路径: {profile_dir}")
```

##### `get_available_profile()`

获取一个可用的 profile（未被标记为活跃的）。

```python
profile_dir = pool.get_available_profile()
if profile_dir:
    print(f"可用 profile: {profile_dir.name}")
```

##### `mark_profile_active(profile_id)`

标记 profile 为活跃状态。

```python
pool.mark_profile_active("my_profile")
```

##### `mark_profile_inactive(profile_id)`

标记 profile 为非活跃状态。

```python
pool.mark_profile_inactive("my_profile")
```

##### `list_profiles()`

列出所有 profile。

```python
profiles = pool.list_profiles()
for profile in profiles:
    print(f"{profile['id']}: {profile['size_mb']} MB")
```

##### `delete_profile(profile_id, force=False)`

删除 profile。

```python
# 普通删除（如果正在使用会失败）
pool.delete_profile("my_profile")

# 强制删除
pool.delete_profile("my_profile", force=True)
```

##### `cleanup_inactive_profiles(days=7)`

清理非活跃的 profile。

```python
# 清理 7 天前创建的非活跃 profile
pool.cleanup_inactive_profiles(days=7)
```

##### `get_profile_info(profile_id)`

获取 profile 详细信息。

```python
info = pool.get_profile_info("my_profile")
print(f"大小: {info['size_mb']} MB")
print(f"创建时间: {info['created']}")
```

## 使用场景

### 场景 1: 并行爬虫

```python
import asyncio
from user_data_pool import get_user_data_pool

async def worker(worker_id):
    pool = get_user_data_pool()
    
    # 获取或创建 profile
    profile_dir = pool.get_available_profile()
    if not profile_dir:
        profile_dir = pool.create_new_profile(f"worker_{worker_id}")
    
    pool.mark_profile_active(profile_dir.name)
    
    try:
        # 使用 profile 进行爬虫操作
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir)
            )
            # 执行爬虫任务...
            await browser.close()
    finally:
        pool.mark_profile_inactive(profile_dir.name)

# 并行运行多个 worker
async def main():
    await asyncio.gather(*[worker(i) for i in range(5)])

asyncio.run(main())
```

### 场景 2: 使用本地 Chrome 配置

```python
from user_data_pool import get_user_data_pool

pool = get_user_data_pool()

# 从本地 Chrome 复制（包含你的扩展、设置等）
profile_dir = pool.create_profile_from_local("my_chrome_copy")

# 使用这个 profile，它会包含你本地 Chrome 的所有配置
```

### 场景 3: 定期清理

```python
from user_data_pool import get_user_data_pool

pool = get_user_data_pool()

# 清理 30 天前创建的非活跃 profile
pool.cleanup_inactive_profiles(days=30)
```

## 目录结构

```
user_data_pool/
├── metadata.json          # 元数据文件（记录活跃状态等）
├── profile_20241212_120000/  # Profile 1
│   ├── Default/
│   ├── ...
├── profile_20241212_120100/  # Profile 2
│   ├── Default/
│   ├── ...
└── ...
```

## 注意事项

1. **Chrome 用户数据路径**：
   - Windows: `C:\Users\用户名\AppData\Local\Google\Chrome\User Data`
   - macOS: `~/Library/Application Support/Google/Chrome`
   - Linux: `~/.config/google-chrome`

2. **并发安全**：系统使用线程锁保证并发安全，但建议在使用完 profile 后及时标记为非活跃。

3. **磁盘空间**：每个 profile 可能占用几百 MB 到几 GB 的空间，注意管理磁盘空间。

4. **Profile 锁定**：如果 Chrome 正在使用某个 profile，复制可能会失败。建议先关闭 Chrome。

5. **最大数量限制**：默认最大 profile 数量为 10，可以在初始化时调整。

## 故障排查

### 问题：无法从本地 Chrome 复制

**解决方案**：
1. 确保 Chrome 已完全关闭
2. 检查 Chrome 用户数据路径是否正确
3. 检查是否有足够的磁盘空间

### 问题：Profile 正在使用中，无法删除

**解决方案**：
- 使用 `--force` 参数强制删除
- 或先标记 profile 为非活跃状态

### 问题：达到最大 profile 数量

**解决方案**：
- 删除不需要的 profile
- 或增加 `max_profiles` 参数

## 示例代码

查看 `pool_example.py` 获取更多使用示例。

