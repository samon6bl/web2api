# Playwright 调试快速参考

## 🚀 快速开始

### 基础调试模式
```python
browser = await p.chromium.launch(
    headless=False,    # 显示浏览器
    slow_mo=500,       # 慢速模式
    devtools=True      # 打开 DevTools
)
```

### 暂停执行
```python
await page.pause()  # 打开 Playwright Inspector
```

## 📸 截图调试

```python
# 全页面截图
await page.screenshot(path="debug.png", full_page=True)

# 元素截图
element = await page.query_selector("button")
await element.screenshot(path="button.png")
```

## 🎥 视频录制

```python
context = await browser.new_context(
    record_video_dir="videos/",
    record_video_size={"width": 1920, "height": 1080}
)
```

## 📊 Trace 录制

```python
await context.tracing.start(screenshots=True, snapshots=True)
# 你的操作...
await context.tracing.stop(path="trace.zip")
# 查看: playwright show-trace trace.zip
```

## 📝 日志监听

```python
# 控制台日志
page.on("console", lambda msg: print(f"Console: {msg.text}"))

# 页面错误
page.on("pageerror", lambda error: print(f"Error: {error}"))

# 请求失败
page.on("requestfailed", lambda req: print(f"Failed: {req.url}"))
```

## 🔍 元素调试

```python
# 高亮元素
await page.evaluate("""
    document.querySelector('button').style.border = '3px solid red';
""")

# 获取元素信息
element = await page.query_selector("button")
box = await element.bounding_box()
text = await element.text_content()
```

## ⏱️ 性能测量

```python
import time
start = time.time()
await page.goto("https://example.com")
print(f"加载时间: {time.time() - start:.2f}秒")
```

## 🌐 网络监控

```python
# 监听请求
page.on("request", lambda req: print(f"Request: {req.url}"))

# 等待 API 响应
async with page.expect_response("**/api/**") as response_info:
    await page.click("button")
response = await response_info.value
```

## 🐛 常见问题

### 元素找不到
```python
# 增加超时
await page.wait_for_selector("button", timeout=30000)

# 等待可见
await page.wait_for_selector("button", state="visible")
```

### 点击不生效
```python
# 强制点击
await page.click("button", force=True)

# JavaScript 点击
await page.evaluate("document.querySelector('button').click()")
```

## 🛠️ 环境变量

```bash
# 使用 Inspector
PWDEBUG=1 python your_script.py

# 使用 codegen
playwright codegen https://example.com
```

## 📚 完整文档

查看 `playwright_debug_guide.md` 获取完整指南
运行 `python debug_example.py` 查看示例

