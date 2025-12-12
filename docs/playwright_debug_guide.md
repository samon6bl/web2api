# Playwright 网页自动化开发调试指南

## 目录
1. [基础调试方法](#基础调试方法)
2. [慢速模式调试](#慢速模式调试)
3. [浏览器开发者工具](#浏览器开发者工具)
4. [截图和视频录制](#截图和视频录制)
5. [控制台日志](#控制台日志)
6. [网络请求监控](#网络请求监控)
7. [断点和暂停](#断点和暂停)
8. [调试技巧](#调试技巧)
9. [常见问题排查](#常见问题排查)

## 基础调试方法

### 1. 使用 `headless=False` 模式

```python
from playwright.async_api import async_playwright

async def debug_example():
    async with async_playwright() as p:
        # 使用 headless=False 可以看到浏览器操作过程
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("https://example.com")
        # 你的代码...
        
        # 保持浏览器打开，方便调试
        await page.pause()  # 暂停执行，等待调试
        await browser.close()
```

### 2. 使用 `slow_mo` 参数减慢操作速度

```python
# 减慢所有操作 1000 毫秒，方便观察
browser = await p.chromium.launch(
    headless=False,
    slow_mo=1000  # 每个操作延迟 1 秒
)
```

### 3. 使用 `devtools=True` 自动打开开发者工具

```python
browser = await p.chromium.launch(
    headless=False,
    devtools=True  # 自动打开 Chrome DevTools
)
```

## 慢速模式调试

### 完整示例

```python
async def slow_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500,  # 每个操作延迟 500ms
            devtools=True  # 打开开发者工具
        )
        page = await browser.new_page()
        
        # 设置超时时间（调试时可以设置更长）
        page.set_default_timeout(60000)  # 60 秒
        
        await page.goto("https://example.com")
        
        # 等待元素出现
        await page.wait_for_selector("button", timeout=10000)
        
        # 执行操作
        await page.click("button")
        
        # 暂停执行，手动检查
        await page.pause()
        
        await browser.close()
```

## 浏览器开发者工具

### 在代码中打开 DevTools

```python
# 方法 1: 启动时打开
browser = await p.chromium.launch(devtools=True)

# 方法 2: 使用 CDP 打开
cdp = await page.context.new_cdp_session(page)
await cdp.send("Runtime.enable")
```

### 在页面中执行调试代码

```python
# 在浏览器控制台执行代码
await page.evaluate("""
    console.log('页面标题:', document.title);
    console.log('当前 URL:', window.location.href);
    debugger;  // 触发断点
""")
```

## 截图和视频录制

### 截图调试

```python
# 保存截图
await page.screenshot(path="screenshot.png", full_page=True)

# 元素截图
element = await page.query_selector("button")
await element.screenshot(path="button.png")

# 失败时自动截图（在测试中很有用）
try:
    await page.click("button")
except Exception as e:
    await page.screenshot(path="error.png")
    raise
```

### 视频录制

```python
# 启动浏览器时启用视频录制
context = await browser.new_context(
    record_video_dir="videos/",
    record_video_size={"width": 1920, "height": 1080}
)

page = await context.new_page()
# 你的操作...

# 关闭时会自动保存视频
await context.close()
```

## 控制台日志

### 监听控制台消息

```python
# 监听 console.log
page.on("console", lambda msg: print(f"Console: {msg.text}"))

# 监听所有控制台事件
async def handle_console(msg):
    print(f"[{msg.type}] {msg.text}")
    if msg.type == "error":
        print(f"错误位置: {msg.location}")

page.on("console", handle_console)

# 监听页面错误
page.on("pageerror", lambda error: print(f"页面错误: {error}"))

# 监听请求失败
page.on("requestfailed", lambda request: print(f"请求失败: {request.url}"))
```

### 完整的日志监听示例

```python
async def debug_with_logs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 监听所有事件
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda error: print(f"Error: {error}"))
        page.on("request", lambda req: print(f"Request: {req.method} {req.url}"))
        page.on("response", lambda res: print(f"Response: {res.status} {res.url}"))
        
        await page.goto("https://example.com")
        await browser.close()
```

## 网络请求监控

### 拦截和修改请求

```python
# 拦截请求
async def handle_route(route):
    print(f"拦截请求: {route.request.url}")
    # 可以修改请求
    # await route.continue_(url="https://example.com")
    # 或者阻止请求
    # await route.abort()
    await route.continue_()

await page.route("**/*", handle_route)
```

### 监控网络活动

```python
# 记录所有网络请求
requests = []

def handle_request(request):
    requests.append({
        "url": request.url,
        "method": request.method,
        "headers": request.headers
    })
    print(f"{request.method} {request.url}")

page.on("request", handle_request)

# 等待所有请求完成
await page.goto("https://example.com", wait_until="networkidle")

# 查看所有请求
for req in requests:
    print(req)
```

## 断点和暂停

### 使用 `page.pause()`

```python
await page.goto("https://example.com")
await page.pause()  # 暂停执行，打开 Playwright Inspector

# 在 Inspector 中可以：
# - 查看页面
# - 执行命令
# - 检查元素
# - 继续执行
```

### 使用 `debugger` 语句

```python
# 在页面中触发断点
await page.evaluate("debugger")

# 或者使用 CDP
cdp = await page.context.new_cdp_session(page)
await cdp.send("Debugger.enable")
await cdp.send("Debugger.pause")
```

### 条件断点

```python
# 只在特定条件下暂停
if some_condition:
    await page.pause()
```

## 调试技巧

### 1. 等待策略

```python
# 等待元素可见
await page.wait_for_selector("button", state="visible")

# 等待元素隐藏
await page.wait_for_selector("loading", state="hidden")

# 等待网络空闲
await page.goto("https://example.com", wait_until="networkidle")

# 等待特定条件
await page.wait_for_function("document.querySelector('button') !== null")
```

### 2. 元素定位调试

```python
# 高亮元素（可视化定位）
await page.evaluate("""
    document.querySelector('button').style.border = '3px solid red';
""")

# 获取元素信息
element = await page.query_selector("button")
box = await element.bounding_box()
print(f"元素位置: {box}")

# 检查元素是否存在
is_visible = await page.is_visible("button")
print(f"按钮可见: {is_visible}")
```

### 3. 执行时间测量

```python
import time

start = time.time()
await page.goto("https://example.com")
print(f"页面加载时间: {time.time() - start:.2f}秒")
```

### 4. 状态检查

```python
# 检查页面状态
print(f"URL: {page.url}")
print(f"标题: {await page.title()}")

# 检查元素状态
text = await page.text_content("button")
print(f"按钮文本: {text}")

# 检查元素属性
value = await page.get_attribute("input", "value")
print(f"输入值: {value}")
```

## 常见问题排查

### 1. 元素找不到

```python
# 增加超时时间
await page.wait_for_selector("button", timeout=30000)

# 使用更宽松的选择器
# 从: await page.click("button.submit")
# 改为: await page.click("button")

# 等待元素可见
await page.wait_for_selector("button", state="visible")
```

### 2. 点击不生效

```python
# 方法 1: 强制点击
await page.click("button", force=True)

# 方法 2: 使用 JavaScript 点击
await page.evaluate("document.querySelector('button').click()")

# 方法 3: 滚动到元素
await page.evaluate("document.querySelector('button').scrollIntoView()")
await page.click("button")
```

### 3. 等待异步内容

```python
# 等待 API 响应
async with page.expect_response("**/api/data") as response_info:
    await page.click("button")
response = await response_info.value
print(f"响应: {await response.json()}")

# 等待导航
async with page.expect_navigation():
    await page.click("a")
```

### 4. 处理弹窗和对话框

```python
# 监听对话框
page.on("dialog", lambda dialog: dialog.accept())

# 或者等待对话框
async def handle_dialog(dialog):
    print(f"对话框消息: {dialog.message}")
    await dialog.accept("输入的值")

page.on("dialog", handle_dialog)
```

## 实用调试脚本模板

```python
"""
Playwright 调试模板
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_template():
    async with async_playwright() as p:
        # 启动浏览器（调试模式）
        browser = await p.chromium.launch(
            headless=False,      # 显示浏览器
            slow_mo=500,         # 慢速模式
            devtools=True        # 打开开发者工具
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # 可选：录制视频
            # record_video_dir="videos/"
        )
        
        page = await context.new_page()
        
        # 设置超时
        page.set_default_timeout(30000)
        
        # 监听事件
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda error: print(f"Error: {error}"))
        page.on("requestfailed", lambda req: print(f"Failed: {req.url}"))
        
        try:
            # 你的代码
            await page.goto("https://example.com")
            
            # 调试：暂停执行
            # await page.pause()
            
            # 调试：截图
            await page.screenshot(path="debug.png")
            
            # 你的操作...
            
        except Exception as e:
            # 错误时截图
            await page.screenshot(path="error.png")
            print(f"错误: {e}")
            raise
        finally:
            # 保持浏览器打开以便检查
            # await page.pause()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_template())
```

## Playwright Inspector

Playwright 提供了内置的 Inspector 工具：

```bash
# 使用 Inspector 运行脚本
playwright codegen https://example.com

# 或者设置环境变量
PWDEBUG=1 python your_script.py
```

## 最佳实践

1. **开发时使用 `headless=False`**：可以看到浏览器操作
2. **使用 `slow_mo`**：减慢操作速度，方便观察
3. **添加日志**：记录关键步骤和状态
4. **使用截图**：在关键步骤保存截图
5. **监听事件**：监听控制台、网络、错误等事件
6. **设置合理的超时**：避免等待时间过长或过短
7. **使用 `page.pause()`**：在需要的地方暂停，手动检查

## 调试工具推荐

1. **Playwright Inspector**：内置调试工具
2. **Chrome DevTools**：浏览器开发者工具
3. **VS Code Playwright Extension**：VS Code 插件
4. **Playwright Trace Viewer**：查看执行轨迹

```python
# 启用 Trace
context = await browser.new_context()
await context.tracing.start(screenshots=True, snapshots=True)

# 你的操作...

# 保存 Trace
await context.tracing.stop(path="trace.zip")

# 查看 Trace
# playwright show-trace trace.zip
```

