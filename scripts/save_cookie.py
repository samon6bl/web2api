"""
DeepSeek Cookie 保存工具 - 使用 Camoufox 浏览器
使用 Camoufox 提供增强的反指纹检测能力
支持 cookie 文件夹管理，自动加载最新的 cookie
支持用户数据池管理
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from camoufox.server import launch_server
    from camoufox import DefaultAddons
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False
    print("警告: Camoufox 未安装，请运行: pip install camoufox")

from playwright.async_api import async_playwright

# 添加父目录到路径，以便导入 utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.user_data_pool import get_user_data_pool


# Cookie 文件夹
COOKIES_DIR = Path("cookies")
COOKIES_DIR.mkdir(exist_ok=True)


def get_sorted_cookie_files():
    """获取排序后的 cookie 文件列表（按文件名排序）"""
    cookie_files = sorted(COOKIES_DIR.glob("*.json"))
    return cookie_files


def get_latest_cookie_file():
    """获取最新的 cookie 文件（按文件名排序后的最后一个）"""
    cookie_files = get_sorted_cookie_files()
    if cookie_files:
        return cookie_files[-1]  # 返回最新的文件（排序后的最后一个）
    return None


def load_cookies_from_file(cookie_file):
    """从文件加载 cookie"""
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        return cookies
    except Exception as e:
        print(f"加载 cookie 文件失败 {cookie_file}: {e}")
        return None


async def load_latest_cookie_to_browser(browser, page=None):
    """加载最新的 cookie 文件到浏览器"""
    cookie_file = get_latest_cookie_file()
    
    if not cookie_file:
        print("没有找到 cookie 文件，跳过加载")
        return
    
    # 如果提供了页面，先导航到目标网站（添加 cookie 需要先访问域名）
    if page:
        try:
            await page.goto("https://chat.deepseek.com", wait_until="domcontentloaded", timeout=10000)
        except:
            pass  # 如果导航失败，继续尝试添加 cookie
    
    print(f"\n找到最新的 cookie 文件: {cookie_file.name}")
    cookies = load_cookies_from_file(cookie_file)
    
    if cookies:
        try:
            # 添加 cookie 到浏览器上下文
            # 需要先访问域名才能添加 cookie
            if page:
                await page.goto("https://chat.deepseek.com", wait_until="domcontentloaded", timeout=5000)
            await browser.add_cookies(cookies)
            print(f"  ✓ 成功加载 {len(cookies)} 个 cookie")
            print("Cookie 加载完成！\n")
        except Exception as e:
            print(f"  ✗ 加载失败: {e}\n")
    else:
        print("  ✗ 无法读取 cookie 文件\n")


async def save_deepseek_cookie(
    use_pool: bool = False, 
    profile_id: Optional[str] = None, 
    os_simulation: str = "random",
    headless: bool = False
):
    """
    打开 deepseek.com，等待用户登录后保存 cookie
    
    Args:
        use_pool: 是否使用用户数据池
        profile_id: 指定的 profile ID（仅在使用 pool 时有效）
        os_simulation: 操作系统模拟 ("random", "windows", "macos", "linux" 或逗号分隔的列表)
        headless: 是否使用无头模式
    """
    if not CAMOUFOX_AVAILABLE:
        print("错误: Camoufox 未安装，无法继续")
        print("请运行: pip install camoufox")
        return
    
    # 用户 profile 目录
    if use_pool:
        pool = get_user_data_pool()
        if profile_id:
            # 使用指定的 profile
            user_data_dir = pool.get_profile(profile_id)
            if user_data_dir is None:
                user_data_dir = pool.create_new_profile(profile_id)
            else:
                pool.mark_profile_active(profile_id)
        else:
            # 获取可用的 profile 或创建新的
            user_data_dir = pool.get_available_profile()
            if user_data_dir is None:
                user_data_dir = pool.create_new_profile()
            profile_id = user_data_dir.name
            print(f"使用 profile: {profile_id}")
        storage_state_path = str(user_data_dir / "storage_state.json") if (user_data_dir / "storage_state.json").exists() else None
    else:
        # 使用传统的单一 profile
        user_data_dir = Path("browser_profile")
        user_data_dir.mkdir(exist_ok=True)
        profile_id = None
        storage_state_path = str(user_data_dir / "storage_state.json") if (user_data_dir / "storage_state.json").exists() else None
    
    # 启动 Camoufox 服务器
    print("正在启动 Camoufox 浏览器...")
    
    # 配置 OS 模拟
    if "," in os_simulation:
        os_list = [s.strip().lower() for s in os_simulation.split(",")]
        valid_os = ["windows", "macos", "linux"]
        if not all(os_val in valid_os for os_val in os_list):
            print(f"错误: 无效的 OS 列表: {os_list}")
            return
        os_config = os_list
    elif os_simulation.lower() in ["windows", "macos", "linux", "random"]:
        os_config = os_simulation.lower()
    else:
        print(f"错误: 无效的 OS 配置: {os_simulation}")
        return
    
    # 启动 Camoufox
    launch_args = {
        "headless": headless,
        "port": 9222,  # 固定端口，便于连接
        "os": os_config,
        "window": (1920, 1080),
        "addons": [],
        "exclude_addons": [DefaultAddons.UBO] if DefaultAddons else [],
    }
    
    if storage_state_path:
        launch_args["storage_state"] = storage_state_path
        print(f"使用 storage_state: {storage_state_path}")
    
    print(f"Camoufox 配置: OS={os_config}, 窗口={launch_args['window']}, 无头模式={headless}")
    
    # 使用子进程启动 Camoufox 服务器
    import subprocess
    import sys
    import socket
    import threading
    import queue
    
    # 使用辅助脚本启动 Camoufox
    launcher_script = Path(__file__).parent / "camoufox_launcher.py"
    
    camoufox_cmd = [
        sys.executable,
        str(launcher_script),
        "--port", "9222",
        "--os", os_simulation,
        "--window-width", "1920",
        "--window-height", "1080",
    ]
    
    if headless:
        camoufox_cmd.append("--headless")
    
    if storage_state_path:
        camoufox_cmd.extend(["--storage-state", storage_state_path])
    
    print("正在启动 Camoufox 服务器...")
    camoufox_proc = subprocess.Popen(
        camoufox_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # 读取输出以获取 WebSocket 端点
    output_queue = queue.Queue()
    
    def read_output(stream, stream_name):
        for line in iter(stream.readline, ''):
            if line:
                output_queue.put((stream_name, line))
        stream.close()
    
    stdout_thread = threading.Thread(target=read_output, args=(camoufox_proc.stdout, "stdout"), daemon=True)
    stderr_thread = threading.Thread(target=read_output, args=(camoufox_proc.stderr, "stderr"), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    
    # 等待并捕获 WebSocket 端点
    print("等待 Camoufox 启动...")
    ws_endpoint = None
    timeout = 30
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        if camoufox_proc.poll() is not None:
            # 进程已退出
            print("Camoufox 进程意外退出")
            return
        
        try:
            stream_name, line = output_queue.get(timeout=0.5)
            if "CAMOUFOX_WS_ENDPOINT=" in line:
                ws_endpoint = line.split("=")[1].strip()
                print(f"捕获到 WebSocket 端点: {ws_endpoint}")
                break
        except queue.Empty:
            pass
        
        # 检查端口是否可用
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            if result == 0:
                ws_endpoint = "ws://127.0.0.1:9222"
                break
        except:
            pass
        
        await asyncio.sleep(0.5)
    
    if not ws_endpoint:
        print("警告: 未能捕获 WebSocket 端点，使用默认端口 9222")
        ws_endpoint = "ws://127.0.0.1:9222"
    
    # 使用 Playwright 连接到 Camoufox
    try:
        async with async_playwright() as p:
            try:
                browser = await p.firefox.connect_over_cdp(ws_endpoint)
                print(f"✓ 已连接到 Camoufox: {ws_endpoint}")
            except Exception as e:
                print(f"✗ 连接 Camoufox 失败: {e}")
                print("提示: 请确保 Camoufox 已正确启动")
                return
        
        # 获取或创建页面
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
        else:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            page = await context.new_page()
        
        # 检查是否有已保存的 cookie 文件，加载最新的
        latest_cookie = get_latest_cookie_file()
        if latest_cookie:
            cookie_files = get_sorted_cookie_files()
            print(f"发现 {len(cookie_files)} 个已保存的 cookie 文件")
            print(f"最新文件: {latest_cookie.name}")
            load_choice = input("是否加载最新的 cookie？(y/n，默认y): ").strip().lower()
            if load_choice != 'n':
                await load_latest_cookie_to_browser(browser, page)
        
        # 打开 deepseek.com
        print("正在打开 deepseek.com...")
        await page.goto("https://chat.deepseek.com", wait_until="networkidle")
        
        # 等待用户登录
        print("\n请在浏览器中完成登录...")
        print("登录完成后，请按 Enter 键继续保存 cookie...")
        input()  # 等待用户按 Enter
        
        # 获取所有 cookie
        cookies = await context.cookies()
        
        # 保存 cookie 到文件（按时间戳命名，便于排序）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cookie_file = COOKIES_DIR / f"deepseek_cookies_{timestamp}.json"
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"\nCookie 已保存到: {cookie_file}")
        print(f"共保存了 {len(cookies)} 个 cookie")
        
        # 保存 storage_state（包含 cookies 和 localStorage）
        if use_pool and profile_id:
            storage_state_path = user_data_dir / "storage_state.json"
        else:
            storage_state_path = user_data_dir / "storage_state.json"
        
        storage_state = await context.storage_state()
        with open(storage_state_path, "w", encoding="utf-8") as f:
            json.dump(storage_state, f, indent=2, ensure_ascii=False)
        print(f"Storage state 已保存到: {storage_state_path}")
        
        print(f"\nCookie 文件列表（按时间排序）:")
        cookie_files = get_sorted_cookie_files()
        for idx, cf in enumerate(cookie_files, 1):
            print(f"  {idx}. {cf.name}")
        
            # 关闭浏览器
            await browser.close()
    finally:
        # 关闭 Camoufox 进程
        if 'camoufox_proc' in locals() and camoufox_proc and camoufox_proc.poll() is None:
            print("正在关闭 Camoufox...")
            camoufox_proc.terminate()
            try:
                camoufox_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                camoufox_proc.kill()
        
        # 如果使用 pool，标记 profile 为非活跃
        if use_pool and profile_id:
            pool = get_user_data_pool()
            pool.mark_profile_inactive(profile_id)


async def load_and_open(
    use_pool: bool = False, 
    profile_id: Optional[str] = None,
    os_simulation: str = "random",
    headless: bool = False
):
    """
    仅加载 cookie 并打开网站（不保存新 cookie）
    
    Args:
        use_pool: 是否使用用户数据池
        profile_id: 指定的 profile ID（仅在使用 pool 时有效）
        os_simulation: 操作系统模拟
        headless: 是否使用无头模式
    """
    if not CAMOUFOX_AVAILABLE:
        print("错误: Camoufox 未安装，无法继续")
        return
    
    # 管理 storage_state 文件（Camoufox 会自动管理临时 user_data_dir，无需手动管理）
    if use_pool:
        pool = get_user_data_pool()
        if profile_id:
            storage_state_path = pool.get_storage_state_path(profile_id)
            if storage_state_path is None:
                raise ValueError(f"Profile {profile_id} 不存在")
            pool.mark_profile_active(profile_id)
        else:
            storage_state_path = pool.get_available_storage_state()
            if storage_state_path is None:
                raise ValueError("没有可用的 profile，请先创建一个")
            profile_id = pool.get_profile_id_from_path(storage_state_path)
            print(f"使用 profile: {profile_id}")
    else:
        storage_state_dir = Path("storage_states")
        storage_state_dir.mkdir(exist_ok=True)
        profile_id = None
        storage_state_path = str(storage_state_dir / "default_storage_state.json") if (storage_state_dir / "default_storage_state.json").exists() else None
    
    # 启动 Camoufox
    print("正在启动 Camoufox 浏览器...")
    
    if "," in os_simulation:
        os_config = [s.strip().lower() for s in os_simulation.split(",")]
    elif os_simulation.lower() in ["windows", "macos", "linux", "random"]:
        os_config = os_simulation.lower()
    else:
        os_config = "random"
    
    launch_args = {
        "headless": headless,
        "port": 9222,
        "os": os_config,
        "window": (1920, 1080),
        "addons": [],
        "exclude_addons": [DefaultAddons.UBO] if DefaultAddons else [],
    }
    
    if storage_state_path:
        launch_args["storage_state"] = storage_state_path
    
    import subprocess
    import sys
    import socket
    import threading
    import queue
    
    # 使用辅助脚本启动 Camoufox
    launcher_script = Path(__file__).parent / "camoufox_launcher.py"
    
    camoufox_cmd = [
        sys.executable,
        str(launcher_script),
        "--port", "9222",
        "--os", os_simulation,
        "--window-width", "1920",
        "--window-height", "1080",
    ]
    
    if headless:
        camoufox_cmd.append("--headless")
    
    if storage_state_path:
        camoufox_cmd.extend(["--storage-state", storage_state_path])
    
    print("正在启动 Camoufox 服务器...")
    camoufox_proc = subprocess.Popen(
        camoufox_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # 读取输出
    output_queue = queue.Queue()
    
    def read_output(stream, stream_name):
        for line in iter(stream.readline, ''):
            if line:
                output_queue.put((stream_name, line))
        stream.close()
    
    stdout_thread = threading.Thread(target=read_output, args=(camoufox_proc.stdout, "stdout"), daemon=True)
    stderr_thread = threading.Thread(target=read_output, args=(camoufox_proc.stderr, "stderr"), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    
    # 等待并捕获 WebSocket 端点
    print("等待 Camoufox 启动...")
    ws_endpoint = None
    timeout = 30
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        if camoufox_proc.poll() is not None:
            print("Camoufox 进程意外退出")
            return
        
        try:
            stream_name, line = output_queue.get(timeout=0.5)
            if "CAMOUFOX_WS_ENDPOINT=" in line:
                ws_endpoint = line.split("=")[1].strip()
                break
        except queue.Empty:
            pass
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            if result == 0:
                ws_endpoint = "ws://127.0.0.1:9222"
                break
        except:
            pass
        
        await asyncio.sleep(0.5)
    
    if not ws_endpoint:
        ws_endpoint = "ws://127.0.0.1:9222"
    
    try:
        async with async_playwright() as p:
            try:
                browser = await p.firefox.connect_over_cdp(ws_endpoint)
                print(f"✓ 已连接到 Camoufox: {ws_endpoint}")
            except Exception as e:
                print(f"✗ 连接 Camoufox 失败: {e}")
                return
            
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                if pages:
                    page = pages[0]
                else:
                    page = await context.new_page()
            else:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                )
                page = await context.new_page()
            
            # 先打开网站
            print("正在打开 deepseek.com...")
            await page.goto("https://chat.deepseek.com", wait_until="domcontentloaded")
            
            # 加载最新的 cookie
            await load_latest_cookie_to_browser(browser, page)
            
            # 刷新页面以应用 cookie
            await page.reload(wait_until="networkidle")
            
            print("\n浏览器已打开，按 Enter 键关闭...")
            input()
            
            await browser.close()
    finally:
        # 关闭 Camoufox 进程
        if 'camoufox_proc' in locals() and camoufox_proc and camoufox_proc.poll() is None:
            print("正在关闭 Camoufox...")
            camoufox_proc.terminate()
            try:
                camoufox_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                camoufox_proc.kill()
        
        # 如果使用 pool，标记 profile 为非活跃
        if use_pool and profile_id:
            pool = get_user_data_pool()
            pool.mark_profile_inactive(profile_id)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepSeek Cookie 保存工具 (使用 Camoufox)")
    parser.add_argument("mode", nargs="?", choices=["save", "load"], default="save",
                       help="运行模式: save (保存cookie) 或 load (仅加载cookie)")
    parser.add_argument("--pool", action="store_true", help="使用用户数据池")
    parser.add_argument("--profile-id", type=str, help="指定 profile ID（仅在使用 pool 时有效）")
    parser.add_argument("--os", type=str, default="random",
                       help="操作系统模拟: random, windows, macos, linux 或逗号分隔的列表 (默认: random)")
    parser.add_argument("--headless", action="store_true", help="使用无头模式")
    
    args = parser.parse_args()
    
    if args.mode == "load":
        asyncio.run(load_and_open(
            use_pool=args.pool, 
            profile_id=args.profile_id,
            os_simulation=args.os,
            headless=args.headless
        ))
    else:
        asyncio.run(save_deepseek_cookie(
            use_pool=args.pool, 
            profile_id=args.profile_id,
            os_simulation=args.os,
            headless=args.headless
        ))

