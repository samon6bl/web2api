"""
Camoufox 启动辅助脚本
用于在独立进程中启动 Camoufox 并输出 WebSocket 端点
"""
import sys
import json

try:
    from camoufox.server import launch_server
    from camoufox import DefaultAddons
except ImportError:
    print("错误: Camoufox 未安装", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    # 从命令行参数读取配置
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--os", type=str, default="random")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--storage-state", type=str, default=None)
    parser.add_argument("--window-width", type=int, default=1920)
    parser.add_argument("--window-height", type=int, default=1080)
    
    args = parser.parse_args()
    
    # 配置 OS
    if "," in args.os:
        os_config = [s.strip().lower() for s in args.os.split(",")]
    else:
        os_config = args.os.lower()
    
    # 构建启动参数
    launch_args = {
        "headless": args.headless,
        "port": args.port,
        "os": os_config,
        "window": (args.window_width, args.window_height),
        "addons": [],
        "exclude_addons": [DefaultAddons.UBO] if DefaultAddons else [],
    }
    
    if args.storage_state:
        launch_args["storage_state"] = args.storage_state
    
    # 输出 WebSocket 端点（在启动前）
    ws_endpoint = f"ws://127.0.0.1:{args.port}"
    print(f"CAMOUFOX_WS_ENDPOINT={ws_endpoint}", flush=True)
    print(f"正在启动 Camoufox (端口: {args.port}, OS: {os_config})...", flush=True)
    
    # 启动 Camoufox（会阻塞）
    try:
        launch_server(**launch_args)
    except KeyboardInterrupt:
        print("Camoufox 已停止", flush=True)
    except Exception as e:
        print(f"启动 Camoufox 失败: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

