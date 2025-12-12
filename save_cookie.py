"""
Playwright 脚本：打开 deepseek.com，等待登录后保存 cookie
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def save_deepseek_cookie():
    """打开 deepseek.com，等待用户登录后保存 cookie"""
    async with async_playwright() as p:
        # 启动浏览器（使用有头模式，方便用户登录）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 打开 deepseek.com
        print("正在打开 deepseek.com...")
        await page.goto("https://www.deepseek.com")
        
        # 等待用户登录
        print("\n请在浏览器中完成登录...")
        print("登录完成后，请按 Enter 键继续保存 cookie...")
        input()  # 等待用户按 Enter
        
        # 获取所有 cookie
        cookies = await context.cookies()
        
        # 保存 cookie 到文件
        cookie_file = "deepseek_cookies.json"
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"\nCookie 已保存到: {cookie_file}")
        print(f"共保存了 {len(cookies)} 个 cookie")
        
        # 关闭浏览器
        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_deepseek_cookie())

