"""
Playwright 调试示例脚本
演示各种调试技巧和最佳实践
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_example():
    """基础调试示例"""
    async with async_playwright() as p:
        # 1. 启动浏览器（调试模式）
        browser = await p.chromium.launch(
            headless=False,      # 显示浏览器窗口
            slow_mo=500,         # 每个操作延迟 500ms，方便观察
            devtools=True        # 自动打开 Chrome DevTools
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # 可选：录制视频用于调试
            # record_video_dir="videos/",
            # record_video_size={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        # 2. 设置超时时间（调试时可以设置更长）
        page.set_default_timeout(30000)  # 30 秒
        
        # 3. 监听各种事件
        print("=== 设置事件监听器 ===")
        
        # 监听控制台消息
        page.on("console", lambda msg: print(f"[Console {msg.type}] {msg.text}"))
        
        # 监听页面错误
        page.on("pageerror", lambda error: print(f"[Page Error] {error}"))
        
        # 监听请求
        page.on("request", lambda req: print(f"[Request] {req.method} {req.url}"))
        
        # 监听响应
        page.on("response", lambda res: print(f"[Response] {res.status} {res.url}"))
        
        # 监听请求失败
        page.on("requestfailed", lambda req: print(f"[Request Failed] {req.url} - {req.failure}"))
        
        try:
            # 4. 访问页面
            print("\n=== 访问页面 ===")
            await page.goto("https://chat.deepseek.com", wait_until="networkidle")
            
            # 5. 保存截图（调试用）
            await page.screenshot(path="debug_step1.png", full_page=True)
            print("已保存截图: debug_step1.png")
            
            # 6. 检查页面状态
            print(f"\n=== 页面信息 ===")
            print(f"URL: {page.url}")
            print(f"标题: {await page.title()}")
            
            # 7. 等待元素出现
            print("\n=== 等待元素 ===")
            try:
                # 等待按钮出现（最多等待 10 秒）
                await page.wait_for_selector("button", timeout=10000, state="visible")
                print("按钮已出现")
            except Exception as e:
                print(f"等待元素超时: {e}")
                # 保存当前页面状态
                await page.screenshot(path="timeout_error.png")
            
            # 8. 高亮元素（可视化调试）
            print("\n=== 高亮元素 ===")
            await page.evaluate("""
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => {
                    btn.style.border = '3px solid red';
                    btn.style.backgroundColor = 'yellow';
                });
            """)
            await page.screenshot(path="debug_highlighted.png")
            print("已高亮按钮并保存截图")
            
            # 9. 获取元素信息
            print("\n=== 元素信息 ===")
            buttons = await page.query_selector_all("button")
            for i, button in enumerate(buttons):
                text = await button.text_content()
                box = await button.bounding_box()
                is_visible = await button.is_visible()
                print(f"按钮 {i+1}: 文本='{text}', 可见={is_visible}, 位置={box}")
            
            # 10. 执行 JavaScript 调试
            print("\n=== JavaScript 调试 ===")
            result = await page.evaluate("""
                () => {
                    console.log('在页面中执行调试代码');
                    return {
                        url: window.location.href,
                        title: document.title,
                        buttonCount: document.querySelectorAll('button').length
                    };
                }
            """)
            print(f"页面信息: {result}")
            
            # 11. 暂停执行（手动调试）
            print("\n=== 暂停执行，等待手动检查 ===")
            print("浏览器已暂停，你可以在浏览器中手动操作")
            print("在 Playwright Inspector 中可以继续执行")
            # await page.pause()  # 取消注释以启用暂停
            
            # 12. 监控网络请求
            print("\n=== 监控网络请求 ===")
            requests_log = []
            
            def log_request(request):
                requests_log.append({
                    "url": request.url,
                    "method": request.method,
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            page.on("request", log_request)
            
            # 执行一些操作触发请求
            # await page.click("button")
            
            # 等待请求完成
            await asyncio.sleep(2)
            print(f"捕获到 {len(requests_log)} 个请求")
            for req in requests_log[:5]:  # 只显示前 5 个
                print(f"  {req['method']} {req['url']}")
            
            # 13. 测量执行时间
            print("\n=== 性能测量 ===")
            import time
            start = time.time()
            await page.reload(wait_until="networkidle")
            load_time = time.time() - start
            print(f"页面重新加载时间: {load_time:.2f}秒")
            
            # 14. 保存最终状态
            await page.screenshot(path="debug_final.png", full_page=True)
            print("\n=== 调试完成 ===")
            print("所有截图已保存")
            
        except Exception as e:
            # 错误处理
            print(f"\n=== 发生错误 ===")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            
            # 保存错误时的截图
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("已保存错误截图: error_screenshot.png")
            
            # 保存页面 HTML（用于调试）
            html = await page.content()
            with open("error_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("已保存页面 HTML: error_page.html")
            
            raise
        
        finally:
            # 保持浏览器打开以便检查（可选）
            print("\n按 Enter 键关闭浏览器...")
            # input()  # 取消注释以保持浏览器打开
            
            await browser.close()


async def debug_with_trace():
    """使用 Trace 进行调试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # 启动 Trace 录制
        await context.tracing.start(
            screenshots=True,    # 录制截图
            snapshots=True,     # 录制 DOM 快照
            sources=True        # 录制源代码
        )
        
        page = await context.new_page()
        
        try:
            await page.goto("https://chat.deepseek.com")
            # 你的操作...
            
        finally:
            # 停止并保存 Trace
            await context.tracing.stop(path="trace.zip")
            print("Trace 已保存到 trace.zip")
            print("使用以下命令查看: playwright show-trace trace.zip")
            
            await browser.close()


async def debug_with_video():
    """使用视频录制进行调试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        try:
            await page.goto("https://chat.deepseek.com")
            # 你的操作...
            
        finally:
            await context.close()
            print("视频已保存到 videos/ 目录")


async def debug_network():
    """网络请求调试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 拦截和记录所有请求
        requests_data = []
        responses_data = []
        
        def handle_request(request):
            requests_data.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data
            })
            print(f"📤 {request.method} {request.url}")
        
        def handle_response(response):
            responses_data.append({
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers)
            })
            print(f"📥 {response.status} {response.url}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        await page.goto("https://chat.deepseek.com", wait_until="networkidle")
        
        # 等待 API 响应
        async with page.expect_response("**/api/**") as response_info:
            # 触发 API 请求的操作
            pass
        
        response = await response_info.value
        print(f"\nAPI 响应状态: {response.status}")
        print(f"API 响应数据: {await response.json()}")
        
        await browser.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "trace":
            asyncio.run(debug_with_trace())
        elif mode == "video":
            asyncio.run(debug_with_video())
        elif mode == "network":
            asyncio.run(debug_network())
        else:
            print("可用模式: trace, video, network")
    else:
        # 默认运行基础调试示例
        asyncio.run(debug_example())

