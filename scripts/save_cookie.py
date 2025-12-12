"""
DeepSeek Cookie 保存工具 - 使用 Camoufox 浏览器
使用 Camoufox 提供增强的反指纹检测能力
支持 cookie 文件夹管理，自动加载最新的 cookie
支持用户数据池管理
"""
from __future__ import annotations

import asyncio
import json
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from collections import deque
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
from utils.anti_fingerprint import AntiFingerprintManager


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


async def load_latest_cookie_to_browser(context, page=None):
    """加载最新的 cookie 文件到浏览器上下文（BrowserContext）"""
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
            if page:
                await page.goto("https://chat.deepseek.com", wait_until="domcontentloaded", timeout=5000)
            await context.add_cookies(cookies)
            print(f"  ✓ 成功加载 {len(cookies)} 个 cookie")
            print("Cookie 加载完成！\n")
        except Exception as e:
            print(f"  ✗ 加载失败: {e}\n")
    else:
        print("  ✗ 无法读取 cookie 文件\n")


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
_WS_URL_RE = re.compile(r"ws://[^\s]+", re.IGNORECASE)


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text)


def _extract_playwright_ws_endpoint(line: str) -> Optional[str]:
    """
    从 Camoufox/Playwright server 输出中提取 wsEndpoint。

    Camoufox 底层会通过 Node 脚本打印类似：
      "Websocket endpoint: ws://127.0.0.1:12345/<randomPath>"
    """
    if not line:
        return None
    clean = _strip_ansi(line).strip()

    # 兼容旧格式（如果未来 launcher 再次提供机器可读行）
    if "CAMOUFOX_WS_ENDPOINT=" in clean:
        _, rhs = clean.split("CAMOUFOX_WS_ENDPOINT=", 1)
        m = _WS_URL_RE.search(rhs.strip())
        return m.group(0) if m else rhs.strip() or None

    # Playwright server 的标准输出
    if "websocket endpoint" in clean.lower():
        m = _WS_URL_RE.search(clean)
        return m.group(0) if m else None

    return None


def _pick_free_port(preferred: int = 9222) -> int:
    """
    尝试使用 preferred；如果已被占用则自动选择一个空闲端口。
    """
    for port in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    # 理论上不会走到这里
    raise RuntimeError("无法选择可用端口")


def _build_camoufox_cmd(
    *,
    port: int,
    os_simulation: str,
    headless: bool,
    storage_state_path: Optional[str],
    window_width: int = 1920,
    window_height: int = 1080,
) -> list[str]:
    launcher_script = Path(__file__).parent / "camoufox_launcher.py"
    cmd = [
        sys.executable,
        str(launcher_script),
        "--port",
        str(port),
        "--os",
        os_simulation,
        "--window-width",
        str(window_width),
        "--window-height",
        str(window_height),
    ]
    if headless:
        cmd.append("--headless")
    if storage_state_path:
        cmd.extend(["--storage-state", storage_state_path])
    return cmd


def _start_output_reader_threads(proc: subprocess.Popen, output_queue: "queue.Queue[tuple[str, str]]") -> None:
    def read_output(stream, stream_name: str):
        for line in iter(stream.readline, ""):
            if line:
                output_queue.put((stream_name, line))
        stream.close()

    threading.Thread(target=read_output, args=(proc.stdout, "stdout"), daemon=True).start()
    threading.Thread(target=read_output, args=(proc.stderr, "stderr"), daemon=True).start()


def _terminate_process_tree(proc: subprocess.Popen, *, timeout_sec: float = 5) -> None:
    """
    尽量干净地结束 Camoufox launcher 进程（并在 Windows 上连带杀掉子进程树）。
    """
    if not proc or proc.poll() is not None:
        return

    if sys.platform.startswith("win"):
        # /T: 终止指定 PID 及其子进程；/F: 强制
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    try:
        proc.terminate()
        proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()


async def _launch_camoufox_server(
    *,
    os_simulation: str,
    headless: bool,
    storage_state_path: Optional[str],
    preferred_port: int = 9222,
    timeout_sec: float = 60,
) -> tuple[subprocess.Popen, str]:
    port = _pick_free_port(preferred=preferred_port)
    if port != preferred_port:
        print(f"提示: 端口 {preferred_port} 已被占用，改用空闲端口 {port}")

    cmd = _build_camoufox_cmd(
        port=port,
        os_simulation=os_simulation,
        headless=headless,
        storage_state_path=storage_state_path,
    )

    print("正在启动 Camoufox 服务器...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )

    output_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
    _start_output_reader_threads(proc, output_queue)

    print("等待 Camoufox 启动...")
    start = time.monotonic()
    tail: deque[str] = deque(maxlen=200)

    try:
        while (time.monotonic() - start) < timeout_sec:
            if proc.poll() is not None:
                # 进程已退出：输出尾部日志便于排查
                while True:
                    try:
                        stream_name, line = output_queue.get_nowait()
                        tail.append(f"[{stream_name}] {line.rstrip()}")
                    except queue.Empty:
                        break
                raise RuntimeError("Camoufox 进程意外退出\n" + "\n".join(tail))

            try:
                stream_name, line = output_queue.get(timeout=0.5)
                if line:
                    tail.append(f"[{stream_name}] {line.rstrip()}")
                    ws_endpoint = _extract_playwright_ws_endpoint(line)
                    if ws_endpoint:
                        print(f"捕获到 WebSocket 端点: {ws_endpoint}")
                        return proc, ws_endpoint
            except queue.Empty:
                await asyncio.sleep(0.1)

        raise TimeoutError("等待 Camoufox wsEndpoint 超时\n" + "\n".join(tail))
    except Exception:
        # 如果启动阶段失败，尽量回收残留进程，避免下次运行端口被占用
        _terminate_process_tree(proc)
        raise


async def save_deepseek_cookie(
    use_pool: bool = False, 
    profile_id: Optional[str] = None, 
    os_simulation: str = "random",
    headless: bool = False,
    enable_anti_fingerprint: bool = True,
):
    """
    打开 deepseek.com，等待用户登录后保存 cookie
    
    Args:
        use_pool: 是否使用用户数据池
        profile_id: 指定的 profile ID（仅在使用 pool 时有效）
        os_simulation: 操作系统模拟 ("random", "windows", "macos", "linux" 或逗号分隔的列表)
        headless: 是否使用无头模式
        enable_anti_fingerprint: 是否启用反指纹检测功能
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
        # 用于反指纹管理器，选择第一个 OS
        os_family = os_list[0] if os_list else None
        os_display = os_list
    elif os_simulation.lower() in ["windows", "macos", "linux"]:
        os_config = os_simulation.lower()
        os_family = os_simulation.lower()
        os_display = os_config
    elif os_simulation.lower() == "random":
        # "random" 时不设置 os_config，让 Camoufox 自动选择
        os_config = None
        os_family = None
        os_display = "random (自动选择)"
    else:
        print(f"错误: 无效的 OS 配置: {os_simulation}")
        return
    
    # 初始化反指纹管理器
    anti_fp_manager = None
    if enable_anti_fingerprint:
        anti_fp_manager = AntiFingerprintManager(
            enable_behavior_simulation=True,
            enable_interaction_simulation=True,
            enable_frequency_control=False,  # 单次操作不需要频率控制
            enable_header_management=True,
            os_family=os_family,
        )
        print("✓ 反指纹检测功能已启用")
    
    # 启动 Camoufox server 并获取真实的 Playwright wsEndpoint（包含随机 wsPath）
    camoufox_proc = None
    ws_endpoint = None

    if storage_state_path:
        print(f"使用 storage_state: {storage_state_path}")

    print(f"Camoufox 配置: OS={os_display}, 窗口=(1920, 1080), 无头模式={headless}")

    try:
        camoufox_proc, ws_endpoint = await _launch_camoufox_server(
            os_simulation=os_simulation,
            headless=headless,
            storage_state_path=storage_state_path,
            preferred_port=9222,
            timeout_sec=60,
        )
    except Exception as e:
        print(f"✗ 启动 Camoufox 失败: {e}")
        print("提示: 可尝试单独运行 scripts\\camoufox_launcher.py 查看详细输出")
        return
    
    # 使用 Playwright 连接到 Camoufox（带重试机制）
    max_retries = 5
    retry_delay = 2
    
    try:
        async with async_playwright() as p:
            browser = None
            
            # 重试连接
            for attempt in range(max_retries):
                try:
                    browser = await p.firefox.connect(ws_endpoint, timeout=30000)
                    print(f"✓ 已连接到 Camoufox: {ws_endpoint}")
                    break  # 连接成功，退出重试循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"连接尝试 {attempt + 1}/{max_retries} 失败: {e}")
                        print(f"等待 {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)
                    else:
                        print(f"✗ 连接 Camoufox 失败（已重试 {max_retries} 次）: {e}")
                        print("提示: 请确保 Camoufox 已正确启动")
                        return
            
            if browser is None:
                print("✗ 无法连接到 Camoufox")
                return
            
            # 获取或创建页面
            try:
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    if pages:
                        page = pages[0]
                    else:
                        page = await context.new_page()
                else:
                    # 准备 context 选项
                    context_options = {
                        "viewport": {"width": 1920, "height": 1080},
                        "locale": "zh-CN",
                        "timezone_id": "Asia/Shanghai",
                    }
                    
                    # 应用反指纹检测 HTTP 头
                    if anti_fp_manager and anti_fp_manager.enable_header_management:
                        headers = anti_fp_manager.get_headers()
                        if headers:
                            context_options["extra_http_headers"] = headers
                            print("✓ 已应用反指纹检测 HTTP 头")
                    
                    context = await browser.new_context(**context_options)
                    page = await context.new_page()
            except Exception as e:
                # 兜底：如果获取现有上下文失败，重新创建
                print(f"获取或创建浏览器上下文失败，尝试新建: {e}")
                context_options = {
                    "viewport": {"width": 1920, "height": 1080},
                    "locale": "zh-CN",
                    "timezone_id": "Asia/Shanghai",
                }
                if anti_fp_manager and anti_fp_manager.enable_header_management:
                    headers = anti_fp_manager.get_headers()
                    if headers:
                        context_options["extra_http_headers"] = headers
                        print("✓ 已应用反指纹检测 HTTP 头")
                context = await browser.new_context(**context_options)
                page = await context.new_page()
            
            # 检查是否有已保存的 cookie 文件，加载最新的
            latest_cookie = get_latest_cookie_file()
            if latest_cookie:
                cookie_files = get_sorted_cookie_files()
                print(f"发现 {len(cookie_files)} 个已保存的 cookie 文件")
                print(f"最新文件: {latest_cookie.name}")
                load_choice = input("是否加载最新的 cookie？(y/n，默认y): ").strip().lower()
                if load_choice != 'n':
                    await load_latest_cookie_to_browser(context, page)
            
            # 打开 deepseek.com
            print("正在打开 deepseek.com...")
            await page.goto("https://chat.deepseek.com", wait_until="networkidle")
            
            # 页面加载后应用交互模拟
            if anti_fp_manager:
                await anti_fp_manager.on_page_loaded(page)
            
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
            if browser:
                await browser.close()
    finally:
        # 关闭 Camoufox 进程
        if camoufox_proc and camoufox_proc.poll() is None:
            print("正在关闭 Camoufox...")
            _terminate_process_tree(camoufox_proc)
        
        # 如果使用 pool，标记 profile 为非活跃
        if use_pool and profile_id:
            pool = get_user_data_pool()
            pool.mark_profile_inactive(profile_id)


async def load_and_open(
    use_pool: bool = False, 
    profile_id: Optional[str] = None,
    os_simulation: str = "random",
    headless: bool = False,
    enable_anti_fingerprint: bool = True,
):
    """
    仅加载 cookie 并打开网站（不保存新 cookie）
    
    Args:
        use_pool: 是否使用用户数据池
        profile_id: 指定的 profile ID（仅在使用 pool 时有效）
        os_simulation: 操作系统模拟
        headless: 是否使用无头模式
        enable_anti_fingerprint: 是否启用反指纹检测功能
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
        os_family = os_config[0] if os_config else None
    elif os_simulation.lower() in ["windows", "macos", "linux"]:
        os_config = os_simulation.lower()
        os_family = os_simulation.lower()
    elif os_simulation.lower() == "random":
        # "random" 时让 launcher 脚本处理
        os_config = None
        os_family = None
    else:
        # 默认使用 random
        os_simulation = "random"
        os_config = None
        os_family = None
    
    # 初始化反指纹管理器
    anti_fp_manager = None
    if enable_anti_fingerprint:
        anti_fp_manager = AntiFingerprintManager(
            enable_behavior_simulation=True,
            enable_interaction_simulation=True,
            enable_frequency_control=False,
            enable_header_management=True,
            os_family=os_family,
        )
        print("✓ 反指纹检测功能已启用")
    
    # 启动 Camoufox server 并获取真实的 Playwright wsEndpoint（包含随机 wsPath）
    camoufox_proc = None
    ws_endpoint = None

    if storage_state_path:
        print(f"使用 storage_state: {storage_state_path}")

    print(f"Camoufox 配置: OS={os_simulation}, 窗口=(1920, 1080), 无头模式={headless}")

    try:
        camoufox_proc, ws_endpoint = await _launch_camoufox_server(
            os_simulation=os_simulation,
            headless=headless,
            storage_state_path=storage_state_path,
            preferred_port=9222,
            timeout_sec=60,
        )
    except Exception as e:
        print(f"✗ 启动 Camoufox 失败: {e}")
        print("提示: 可尝试单独运行 scripts\\camoufox_launcher.py 查看详细输出")
        return
    
    # 使用 Playwright 连接到 Camoufox（带重试机制）
    max_retries = 5
    retry_delay = 2
    
    try:
        async with async_playwright() as p:
            browser = None
            
            # 重试连接
            for attempt in range(max_retries):
                try:
                    browser = await p.firefox.connect(ws_endpoint, timeout=30000)
                    print(f"✓ 已连接到 Camoufox: {ws_endpoint}")
                    break  # 连接成功，退出重试循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"连接尝试 {attempt + 1}/{max_retries} 失败: {e}")
                        print(f"等待 {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)
                    else:
                        print(f"✗ 连接 Camoufox 失败（已重试 {max_retries} 次）: {e}")
                        return
            
            if browser is None:
                print("✗ 无法连接到 Camoufox")
                return
            
            try:
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    if pages:
                        page = pages[0]
                    else:
                        page = await context.new_page()
                else:
                    # 准备 context 选项
                    context_options = {
                        "viewport": {"width": 1920, "height": 1080},
                        "locale": "zh-CN",
                        "timezone_id": "Asia/Shanghai",
                    }
                    
                    # 应用反指纹检测 HTTP 头
                    if anti_fp_manager and anti_fp_manager.enable_header_management:
                        headers = anti_fp_manager.get_headers()
                        if headers:
                            context_options["extra_http_headers"] = headers
                            print("✓ 已应用反指纹检测 HTTP 头")
                    
                    context = await browser.new_context(**context_options)
                    page = await context.new_page()
                
                # 先打开网站
                print("正在打开 deepseek.com...")
                await page.goto("https://chat.deepseek.com", wait_until="domcontentloaded")
                
                # 页面加载后应用交互模拟
                if anti_fp_manager:
                    await anti_fp_manager.on_page_loaded(page)
                
                # 加载最新的 cookie
                await load_latest_cookie_to_browser(context, page)
                
                # 刷新页面以应用 cookie
                await page.reload(wait_until="networkidle")
                
                print("\n浏览器已打开，按 Enter 键关闭...")
                input()
            finally:
                # 确保浏览器关闭
                if browser:
                    await browser.close()
    finally:
        # 关闭 Camoufox 进程
        if camoufox_proc and camoufox_proc.poll() is None:
            print("正在关闭 Camoufox...")
            _terminate_process_tree(camoufox_proc)
        
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
    parser.add_argument("--disable-anti-fingerprint", action="store_true",
                       help="禁用反指纹检测功能")
    
    args = parser.parse_args()
    
    enable_anti_fingerprint = not args.disable_anti_fingerprint
    
    if args.mode == "load":
        asyncio.run(load_and_open(
            use_pool=args.pool, 
            profile_id=args.profile_id,
            os_simulation=args.os,
            headless=args.headless,
            enable_anti_fingerprint=enable_anti_fingerprint
        ))
    else:
        asyncio.run(save_deepseek_cookie(
            use_pool=args.pool, 
            profile_id=args.profile_id,
            os_simulation=args.os,
            headless=args.headless,
            enable_anti_fingerprint=enable_anti_fingerprint
        ))

