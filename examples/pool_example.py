"""
Storage State 管理示例（基于 Camoufox 指纹随机化方案）
注意：Camoufox 会自动管理临时的 user_data_dir，我们只需要管理 storage_state.json 文件
"""
import asyncio
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.user_data_pool import get_user_data_pool

try:
    from camoufox.server import launch_server
    from camoufox import DefaultAddons
    from playwright.async_api import async_playwright
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False
    print("警告: Camoufox 未安装，部分示例无法运行")


async def example_use_pool():
    """示例：使用 Storage State 池（基于 Camoufox）"""
    if not CAMOUFOX_AVAILABLE:
        print("错误: Camoufox 未安装，无法运行此示例")
        return
    
    pool = get_user_data_pool()
    
    # 方式 1: 创建新的 storage_state
    print("=== 方式 1: 创建新 profile ===")
    try:
        storage_state_path = pool.create_new_profile()
        profile_id = pool.get_profile_id_from_path(storage_state_path)
        print(f"已创建 profile: {profile_id}")
        print(f"Storage state 路径: {storage_state_path}")
    except Exception as e:
        print(f"创建失败: {e}")
    
    # 方式 2: 获取可用的 storage_state
    print("\n=== 方式 2: 获取可用 profile ===")
    storage_state_path = pool.get_available_storage_state()
    if storage_state_path:
        profile_id = pool.get_profile_id_from_path(storage_state_path)
        print(f"使用 profile: {profile_id}")
        pool.mark_profile_active(profile_id)
        
        # 使用 Camoufox 启动浏览器（会自动管理临时 user_data_dir）
        print("正在启动 Camoufox...")
        import subprocess
        import threading
        import queue
        
        launcher_script = Path(__file__).parent.parent / "scripts" / "camoufox_launcher.py"
        camoufox_cmd = [
            sys.executable,
            str(launcher_script),
            "--port", "9222",
            "--os", "random",
            "--storage-state", storage_state_path,
        ]
        
        camoufox_proc = subprocess.Popen(
            camoufox_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待启动
        await asyncio.sleep(3)
        
        # 连接到 Camoufox
        async with async_playwright() as p:
            browser = await p.firefox.connect_over_cdp("ws://127.0.0.1:9222")
            
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            await page.goto("https://example.com")
            
            print("浏览器已打开，按 Enter 关闭...")
            input()
            
            # 保存 storage_state
            storage_state = await context.storage_state()
            with open(storage_state_path, "w", encoding="utf-8") as f:
                import json
                json.dump(storage_state, f, indent=2, ensure_ascii=False)
            print(f"Storage state 已保存到: {storage_state_path}")
            
            await browser.close()
        
        camoufox_proc.terminate()
        camoufox_proc.wait()
        
        # 标记为非活跃
        pool.mark_profile_inactive(profile_id)
    else:
        print("没有可用的 profile")


async def example_parallel_use():
    """示例：并行使用多个 profile（基于 Camoufox）"""
    if not CAMOUFOX_AVAILABLE:
        print("错误: Camoufox 未安装，无法运行此示例")
        return
    
    pool = get_user_data_pool()
    
    # 创建多个 storage_state
    storage_states = []
    for i in range(3):
        try:
            storage_state_path = pool.create_new_profile(f"worker_{i}")
            storage_states.append(storage_state_path)
            profile_id = pool.get_profile_id_from_path(storage_state_path)
            print(f"创建 profile: {profile_id}")
        except Exception as e:
            print(f"创建 profile worker_{i} 失败: {e}")
    
    # 并行使用（每个使用不同的端口）
    async def use_profile(storage_state_path, port):
        pool = get_user_data_pool()
        profile_id = pool.get_profile_id_from_path(storage_state_path)
        pool.mark_profile_active(profile_id)
        
        # 启动 Camoufox（每个使用不同端口）
        launcher_script = Path(__file__).parent.parent / "scripts" / "camoufox_launcher.py"
        camoufox_cmd = [
            sys.executable,
            str(launcher_script),
            "--port", str(port),
            "--os", "random",
            "--storage-state", storage_state_path,
            "--headless",
        ]
        
        camoufox_proc = subprocess.Popen(
            camoufox_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        await asyncio.sleep(2)
        
        async with async_playwright() as p:
            browser = await p.firefox.connect_over_cdp(f"ws://127.0.0.1:{port}")
            
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            
            await page.goto("https://example.com")
            
            print(f"Profile {profile_id} 已打开 (端口 {port})")
            await asyncio.sleep(2)
            
            await browser.close()
        
        camoufox_proc.terminate()
        camoufox_proc.wait()
        
        pool.mark_profile_inactive(profile_id)
        print(f"Profile {profile_id} 已关闭")
    
    # 并行执行（每个使用不同端口）
    import subprocess
    ports = [9222, 9223, 9224]
    await asyncio.gather(*[use_profile(ss, port) for ss, port in zip(storage_states, ports)])


def example_manage_profiles():
    """示例：管理 profile"""
    pool = get_user_data_pool()
    
    # 列出所有 profile
    print("=== 所有 profile ===")
    profiles = pool.list_profiles()
    for profile in profiles:
        print(f"  {profile['id']}: {'活跃' if profile['active'] else '空闲'}, {profile['size_mb']} MB")
    
    # 获取 profile 信息
    if profiles:
        profile_id = profiles[0]['id']
        print(f"\n=== Profile {profile_id} 详细信息 ===")
        info = pool.get_profile_info(profile_id)
        if info:
            print(f"  路径: {info['path']}")
            print(f"  大小: {info['size_mb']} MB")
            print(f"  状态: {'活跃' if info['active'] else '空闲'}")
            print(f"  创建时间: {info['created']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "parallel":
            asyncio.run(example_parallel_use())
        elif command == "manage":
            example_manage_profiles()
        else:
            print("可用命令: parallel, manage")
    else:
        asyncio.run(example_use_pool())

