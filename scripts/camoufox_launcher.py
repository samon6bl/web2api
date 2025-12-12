"""
Camoufox 启动辅助脚本
用于在独立进程中启动 Camoufox 并输出 WebSocket 端点
"""
import sys
import json
import json as json_module
from pathlib import Path

# #region agent log
LOG_PATH = Path(r"c:\Users\samon\deepseek\.cursor\debug.log")
def _log(hypothesis_id, location, message, data=None):
    try:
        entry = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": __import__("time").time() * 1000
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json_module.dumps(entry, ensure_ascii=False) + "\n")
    except: pass
# #endregion

try:
    # 导入必要的模块
    # #region agent log
    _log("A", "camoufox_launcher.py:13", "开始导入模块", {"step": "import_start"})
    # #endregion
    
    # 导入 camoufox 模块
    import camoufox.server as camoufox_server
    
    # #region agent log
    _log("A", "camoufox_launcher.py:16", "camoufox.server 导入成功", {"module": "camoufox.server"})
    # #endregion
    
    # 创建补丁函数以修复 Node.js 路径获取问题
    def patched_get_nodejs():
        """修复 Node.js 路径获取的补丁版本 - 确保返回 node.exe 而不是 playwright.cmd"""
        # #region agent log
        _log("A", "camoufox_launcher.py:20", "patched_get_nodejs 被调用", {})
        # #endregion
        try:
            # #region agent log
            _log("A", "camoufox_launcher.py:23", "尝试从 playwright._impl._driver 导入 compute_driver_executable", {})
            # #endregion
            from playwright._impl._driver import compute_driver_executable
            # #region agent log
            _log("A", "camoufox_launcher.py:25", "从 playwright._impl._driver 导入成功", {})
            # #endregion
            
            # 获取 playwright 驱动路径（通常是 playwright.cmd）
            driver_path = compute_driver_executable()
            # #region agent log
            _log("A", "camoufox_launcher.py:27", "compute_driver_executable 调用成功", {"result_type": str(type(driver_path)), "result": str(driver_path)[:100]})
            # #endregion
            
            # 将结果转换为 Path 对象
            if isinstance(driver_path, (tuple, list)) and len(driver_path) > 0:
                driver_path = Path(driver_path[0])
            elif isinstance(driver_path, str):
                driver_path = Path(driver_path)
            elif isinstance(driver_path, Path):
                pass  # 已经是 Path 对象
            else:
                driver_path = Path(str(driver_path))
            
            # 在 playwright driver 目录中查找 node.exe
            # driver_path 通常是 playwright.cmd，node.exe 在同一目录
            node_exe = driver_path.parent / "node.exe"
            
            # #region agent log
            _log("A", "camoufox_launcher.py:45", "检查 node.exe 路径", {"node_exe": str(node_exe), "exists": node_exe.exists()})
            # #endregion
            
            if node_exe.exists():
                node_path = str(node_exe.resolve())
                # #region agent log
                _log("A", "camoufox_launcher.py:50", "找到 node.exe", {"path": node_path})
                # #endregion
                return node_path
            else:
                # 如果 node.exe 不存在，尝试使用系统 Node.js（从环境变量或 PATH）
                import shutil
                system_node = shutil.which("node")
                if system_node:
                    # #region agent log
                    _log("A", "camoufox_launcher.py:58", "使用系统 Node.js", {"path": system_node})
                    # #endregion
                    return system_node
                else:
                    # #region agent log
                    _log("E", "camoufox_launcher.py:63", "未找到 node.exe 或系统 Node.js", {"node_exe_path": str(node_exe)})
                    # #endregion
                    raise RuntimeError(f"无法找到 Node.js 可执行文件。预期路径: {node_exe}")
                    
        except ImportError as e:
            # #region agent log
            _log("A", "camoufox_launcher.py:68", "导入失败 - ImportError", {"error": str(e), "error_type": type(e).__name__})
            # #endregion
            # 尝试使用系统 Node.js
            try:
                import shutil
                system_node = shutil.which("node")
                if system_node:
                    # #region agent log
                    _log("C", "camoufox_launcher.py:74", "使用系统 Node.js（导入失败后）", {"path": system_node})
                    # #endregion
                    return system_node
                else:
                    raise RuntimeError("无法获取 Node.js 可执行文件路径。请确保 Camoufox 已正确安装或系统已安装 Node.js。")
            except Exception as e2:
                # #region agent log
                _log("C", "camoufox_launcher.py:81", "使用系统 Node.js 也失败", {"error": str(e2), "error_type": type(e2).__name__})
                # #endregion
                raise RuntimeError("无法获取 Node.js 可执行文件路径。请确保 Camoufox 已正确安装。")
        except Exception as e:
            # #region agent log
            _log("E", "camoufox_launcher.py:86", "其他异常", {"error": str(e), "error_type": type(e).__name__})
            # #endregion
            raise RuntimeError(f"无法获取 Node.js 可执行文件路径: {e}")
    
    # #region agent log
    _log("B", "camoufox_launcher.py:75", "检查原始 get_nodejs 函数", {"has_get_nodejs": hasattr(camoufox_server, "get_nodejs")})
    # #endregion
    
    # 总是应用补丁函数以确保返回正确的 node.exe 路径
    # 因为原始函数可能返回 playwright.cmd 而不是 node.exe
    camoufox_server.get_nodejs = patched_get_nodejs
    # #region agent log
    _log("B", "camoufox_launcher.py:81", "已应用补丁函数", {})
    # #endregion
    
    # 测试补丁后的 get_nodejs 是否可用
    try:
        # #region agent log
        _log("B", "camoufox_launcher.py:85", "测试补丁后的 get_nodejs", {})
        # #endregion
        test_result = camoufox_server.get_nodejs()
        # #region agent log
        _log("B", "camoufox_launcher.py:88", "补丁后的 get_nodejs 调用成功", {"result": str(test_result)[:100], "result_type": str(type(test_result))})
        # #endregion
    except Exception as e:
        # #region agent log
        _log("E", "camoufox_launcher.py:91", "补丁后的 get_nodejs 调用失败", {"error": str(e), "error_type": type(e).__name__})
        # #endregion
        # 如果补丁也失败，记录错误但继续（可能会在启动时失败）
        pass
    
    from camoufox.server import launch_server
    from camoufox import DefaultAddons
    
    # #region agent log
    _log("A", "camoufox_launcher.py:94", "所有导入完成", {})
    # #endregion
except ImportError as e:
    # #region agent log
    _log("A", "camoufox_launcher.py:97", "ImportError 异常", {"error": str(e), "error_type": type(e).__name__})
    # #endregion
    print("错误: Camoufox 未安装", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    # #region agent log
    _log("A", "camoufox_launcher.py:102", "其他异常", {"error": str(e), "error_type": type(e).__name__})
    # #endregion
    raise

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
    # Camoufox 不支持 "random" 作为 OS 值，需要处理
    if "," in args.os:
        # 逗号分隔的 OS 列表
        os_config = [s.strip().lower() for s in args.os.split(",")]
        valid_os = ["windows", "macos", "linux"]
        if not all(os_val in valid_os for os_val in os_config):
            print(f"错误: 无效的 OS 列表: {os_config}", file=sys.stderr, flush=True)
            print(f"有效的 OS 值: {valid_os}", file=sys.stderr, flush=True)
            sys.exit(1)
        os_display = os_config
    elif args.os.lower() in ["windows", "macos", "linux"]:
        # 单个有效的 OS
        os_config = args.os.lower()
        os_display = os_config
    elif args.os.lower() == "random":
        # "random" 时不传递 os 参数，让 Camoufox 自动选择
        os_config = None
        os_display = "random (自动选择)"
    else:
        print(f"错误: 无效的 OS 值: '{args.os}'", file=sys.stderr, flush=True)
        print(f"有效的 OS 值: windows, macos, linux, random", file=sys.stderr, flush=True)
        sys.exit(1)
    
    # 构建启动参数
    launch_args = {
        "headless": args.headless,
        "port": args.port,
        "window": (args.window_width, args.window_height),
        "addons": [],
        "exclude_addons": [DefaultAddons.UBO] if DefaultAddons else [],
    }
    
    # 只有当 os_config 不为 None 时才添加 os 参数
    if os_config is not None:
        launch_args["os"] = os_config
    
    if args.storage_state:
        launch_args["storage_state"] = args.storage_state
    
    # 提示：真实的 wsEndpoint 会由 Playwright server 启动脚本打印（包含随机 wsPath）。
    # 这里不要提前打印一个“猜测的 ws://127.0.0.1:<port>”，否则上层脚本会拿到错误端点并连接失败。
    print(f"正在启动 Camoufox (端口: {args.port}, OS: {os_display})...", flush=True)
    
    # 启动 Camoufox（会阻塞）
    try:
        launch_server(**launch_args)
    except KeyboardInterrupt:
        print("Camoufox 已停止", flush=True)
    except Exception as e:
        import traceback
        error_msg = f"启动 Camoufox 失败: {e}"
        print(error_msg, file=sys.stderr, flush=True)
        print("\n详细错误信息:", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

