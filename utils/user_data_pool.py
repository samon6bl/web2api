"""
用户数据池管理器
支持多个并行爬虫实例，每个实例使用独立的用户数据目录，避免冲突
支持 Camoufox 和 Chrome 浏览器
每个 profile 包含 storage_state.json 文件（用于 Camoufox）和用户数据目录
"""
import os
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import json
import threading


class ChromeUserDataPool:
    """
    用户数据池管理器
    支持 Camoufox 和 Chrome 浏览器
    """
    
    def __init__(self, pool_dir: str = "user_data_pool", max_profiles: int = 10):
        """
        初始化用户数据池
        
        Args:
            pool_dir: 用户数据池目录
            max_profiles: 最大 profile 数量
        """
        self.pool_dir = Path(pool_dir)
        self.pool_dir.mkdir(exist_ok=True)
        self.max_profiles = max_profiles
        self.lock = threading.Lock()
        self.active_profiles: Dict[str, bool] = {}  # profile_id -> is_active
        self.metadata_file = self.pool_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_profiles = data.get("active_profiles", {})
            except Exception as e:
                print(f"加载元数据失败: {e}")
                self.active_profiles = {}
        else:
            self.active_profiles = {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({
                    "active_profiles": self.active_profiles,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存元数据失败: {e}")
    
    def get_local_chrome_user_data_path(self) -> Optional[Path]:
        """
        获取本地 Chrome/Firefox 用户数据路径
        
        Returns:
            浏览器用户数据目录路径，如果不存在则返回 None
        """
        system = platform.system()
        home = Path.home()
        
        if system == "Windows":
            # Windows: C:\Users\用户名\AppData\Local\Google\Chrome\User Data
            chrome_path = home / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/Application Support/Google/Chrome
            chrome_path = home / "Library" / "Application Support" / "Google" / "Chrome"
        elif system == "Linux":
            # Linux: ~/.config/google-chrome
            chrome_path = home / ".config" / "google-chrome"
        else:
            return None
        
        if chrome_path.exists():
            return chrome_path
        return None
    
    def create_profile_from_local(self, profile_id: Optional[str] = None) -> Path:
        """
        从本地 Chrome 用户数据创建新的 profile
        
        Args:
            profile_id: 可选的 profile ID，如果不提供则自动生成
            
        Returns:
            新创建的 profile 目录路径
        """
        with self.lock:
            # 检查是否超过最大数量
            active_count = sum(1 for active in self.active_profiles.values() if active)
            if active_count >= self.max_profiles:
                raise RuntimeError(f"已达到最大 profile 数量: {self.max_profiles}")
            
            # 生成 profile ID
            if profile_id is None:
                profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 检查 profile 是否已存在
            profile_dir = self.pool_dir / profile_id
            if profile_dir.exists():
                raise ValueError(f"Profile {profile_id} 已存在")
            
            # 获取本地 Chrome 用户数据
            local_chrome_path = self.get_local_chrome_user_data_path()
            
            if local_chrome_path and local_chrome_path.exists():
                print(f"从本地 Chrome 用户数据复制: {local_chrome_path}")
                # 复制本地 Chrome 用户数据
                shutil.copytree(local_chrome_path, profile_dir, ignore=shutil.ignore_patterns(
                    "SingletonLock",
                    "SingletonSocket",
                    "SingletonCookie",
                    "lockfile",
                    "*.lock"
                ))
                print(f"已创建 profile: {profile_id}")
            else:
                # 创建新的空 profile
                print(f"本地 Chrome 用户数据不存在，创建新 profile: {profile_id}")
                profile_dir.mkdir(parents=True)
                # 创建必要的子目录结构
                (profile_dir / "Default").mkdir(exist_ok=True)
            
            # 标记为活跃
            self.active_profiles[profile_id] = True
            self._save_metadata()
            
            return profile_dir
    
    def create_new_profile(self, profile_id: Optional[str] = None) -> Path:
        """
        创建新的空 profile
        
        Args:
            profile_id: 可选的 profile ID，如果不提供则自动生成
            
        Returns:
            新创建的 profile 目录路径
        """
        with self.lock:
            # 检查是否超过最大数量
            active_count = sum(1 for active in self.active_profiles.values() if active)
            if active_count >= self.max_profiles:
                raise RuntimeError(f"已达到最大 profile 数量: {self.max_profiles}")
            
            # 生成 profile ID
            if profile_id is None:
                profile_id = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 检查 profile 是否已存在
            profile_dir = self.pool_dir / profile_id
            if profile_dir.exists():
                raise ValueError(f"Profile {profile_id} 已存在")
            
            # 创建新的空 profile
            profile_dir.mkdir(parents=True)
            (profile_dir / "Default").mkdir(exist_ok=True)
            
            # 标记为活跃
            self.active_profiles[profile_id] = True
            self._save_metadata()
            
            print(f"已创建新 profile: {profile_id}")
            return profile_dir
    
    def get_profile(self, profile_id: str) -> Optional[Path]:
        """
        获取指定 profile 的路径
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile 目录路径，如果不存在则返回 None
        """
        profile_dir = self.pool_dir / profile_id
        if profile_dir.exists():
            return profile_dir
        return None
    
    def get_available_profile(self) -> Optional[Path]:
        """
        获取一个可用的 profile（未被标记为活跃的）
        
        Returns:
            可用的 profile 目录路径，如果没有则返回 None
        """
        with self.lock:
            for profile_id, is_active in self.active_profiles.items():
                if not is_active:
                    profile_dir = self.pool_dir / profile_id
                    if profile_dir.exists():
                        self.active_profiles[profile_id] = True
                        self._save_metadata()
                        return profile_dir
        return None
    
    def mark_profile_active(self, profile_id: str):
        """标记 profile 为活跃状态"""
        with self.lock:
            self.active_profiles[profile_id] = True
            self._save_metadata()
    
    def mark_profile_inactive(self, profile_id: str):
        """标记 profile 为非活跃状态"""
        with self.lock:
            self.active_profiles[profile_id] = False
            self._save_metadata()
    
    def list_profiles(self) -> List[Dict[str, any]]:
        """
        列出所有 profile
        
        Returns:
            Profile 信息列表
        """
        profiles = []
        for profile_id in self.active_profiles.keys():
            profile_dir = self.pool_dir / profile_id
            if profile_dir.exists():
                profiles.append({
                    "id": profile_id,
                    "path": str(profile_dir),
                    "active": self.active_profiles.get(profile_id, False),
                    "size": self._get_dir_size(profile_dir),
                    "created": datetime.fromtimestamp(profile_dir.stat().st_ctime).isoformat()
                })
        return sorted(profiles, key=lambda x: x["created"], reverse=True)
    
    def _get_dir_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    def delete_profile(self, profile_id: str, force: bool = False):
        """
        删除 profile
        
        Args:
            profile_id: Profile ID
            force: 是否强制删除（即使标记为活跃）
        """
        with self.lock:
            if not force and self.active_profiles.get(profile_id, False):
                raise ValueError(f"Profile {profile_id} 正在使用中，无法删除。使用 force=True 强制删除")
            
            profile_dir = self.pool_dir / profile_id
            if profile_dir.exists():
                shutil.rmtree(profile_dir)
                print(f"已删除 profile: {profile_id}")
            
            if profile_id in self.active_profiles:
                del self.active_profiles[profile_id]
            self._save_metadata()
    
    def cleanup_inactive_profiles(self, days: int = 7):
        """
        清理非活跃的 profile（超过指定天数未使用）
        
        Args:
            days: 清理多少天前创建的非活跃 profile
        """
        with self.lock:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            to_delete = []
            
            for profile_id, is_active in self.active_profiles.items():
                if not is_active:
                    profile_dir = self.pool_dir / profile_id
                    if profile_dir.exists():
                        created_time = profile_dir.stat().st_ctime
                        if created_time < cutoff_date:
                            to_delete.append(profile_id)
            
            for profile_id in to_delete:
                self.delete_profile(profile_id, force=True)
            
            if to_delete:
                print(f"已清理 {len(to_delete)} 个非活跃 profile")
            else:
                print("没有需要清理的 profile")
    
    def get_profile_info(self, profile_id: str) -> Optional[Dict[str, any]]:
        """
        获取 profile 详细信息
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Profile 信息字典，如果不存在则返回 None
        """
        profile_dir = self.pool_dir / profile_id
        if not profile_dir.exists():
            return None
        
        return {
            "id": profile_id,
            "path": str(profile_dir),
            "active": self.active_profiles.get(profile_id, False),
            "size": self._get_dir_size(profile_dir),
            "size_mb": round(self._get_dir_size(profile_dir) / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(profile_dir.stat().st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(profile_dir.stat().st_mtime).isoformat()
        }


# 全局实例
_user_data_pool: Optional[ChromeUserDataPool] = None


def get_user_data_pool(pool_dir: str = "storage_states_pool", max_profiles: int = 10) -> ChromeUserDataPool:
    """
    获取全局用户数据池实例（单例模式）
    
    Args:
        pool_dir: 用户数据池目录
        max_profiles: 最大 profile 数量
        
    Returns:
        ChromeUserDataPool 实例
    """
    global _user_data_pool
    if _user_data_pool is None:
        _user_data_pool = ChromeUserDataPool(pool_dir, max_profiles)
    return _user_data_pool

