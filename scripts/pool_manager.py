"""
Chrome 用户数据池管理 CLI 工具
"""
import argparse
from user_data_pool import get_user_data_pool
from pathlib import Path


def list_profiles(pool_dir: str = "storage_states_pool"):
    """列出所有 profile"""
    pool = get_user_data_pool(pool_dir)
    profiles = pool.list_profiles()
    
    if not profiles:
        print("没有找到任何 profile")
        return
    
    print(f"\n找到 {len(profiles)} 个 profile:\n")
    print(f"{'ID':<30} {'状态':<10} {'大小 (MB)':<15} {'创建时间':<20}")
    print("-" * 80)
    
    for profile in profiles:
        status = "活跃" if profile["active"] else "空闲"
        size_mb = round(profile["size"] / (1024 * 1024), 2)
        created = profile["created"][:19].replace("T", " ")
        print(f"{profile['id']:<30} {status:<10} {size_mb:<15} {created:<20}")


def create_profile(pool_dir: str = "storage_states_pool", profile_id: str = None, from_local: bool = False):
    """创建新的 profile"""
    pool = get_user_data_pool(pool_dir)
    
    try:
        if from_local:
            print("\n✗ 从本地 Chrome 创建功能已移除（基于 Camoufox 指纹随机化方案）")
            return
        
        storage_state_path = pool.create_new_profile(profile_id)
        profile_id_from_path = pool.get_profile_id_from_path(storage_state_path)
        print(f"\n✓ 已创建新 profile: {profile_id_from_path}")
        
        info = pool.get_profile_info(profile_id_from_path)
        if info:
            print(f"  路径: {info['path']}")
            print(f"  大小: {info['size_mb']} MB")
    except Exception as e:
        print(f"\n✗ 创建失败: {e}")


def delete_profile(pool_dir: str = "storage_states_pool", profile_id: str = None, force: bool = False):
    """删除 profile"""
    pool = get_user_data_pool(pool_dir)
    
    if not profile_id:
        print("✗ 请指定要删除的 profile ID")
        return
    
    try:
        pool.delete_profile(profile_id, force=force)
        print(f"\n✓ 已删除 profile: {profile_id}")
    except Exception as e:
        print(f"\n✗ 删除失败: {e}")


def show_profile_info(pool_dir: str = "storage_states_pool", profile_id: str = None):
    """显示 profile 详细信息"""
    pool = get_user_data_pool(pool_dir)
    
    if not profile_id:
        print("✗ 请指定 profile ID")
        return
    
    info = pool.get_profile_info(profile_id)
    if not info:
        print(f"✗ Profile {profile_id} 不存在")
        return
    
    print(f"\nProfile 信息:")
    print(f"  ID: {info['id']}")
    print(f"  路径: {info['path']}")
    print(f"  状态: {'活跃' if info['active'] else '空闲'}")
    print(f"  大小: {info['size_mb']} MB ({info['size']} 字节)")
    print(f"  创建时间: {info['created']}")
    print(f"  修改时间: {info['modified']}")


def cleanup_profiles(pool_dir: str = "storage_states_pool", days: int = 7):
    """清理非活跃的 profile"""
    pool = get_user_data_pool(pool_dir)
    pool.cleanup_inactive_profiles(days)
    print(f"\n✓ 已清理 {days} 天前创建的非活跃 profile")


def main():
    parser = argparse.ArgumentParser(description="Storage State 管理工具（基于 Camoufox 指纹随机化方案）")
    parser.add_argument("--pool-dir", type=str, default="storage_states_pool",
                       help="Storage state 文件池目录（默认: storage_states_pool）")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有 profile")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建新 profile")
    create_parser.add_argument("--profile-id", type=str, help="Profile ID（可选）")
    create_parser.add_argument("--from-local", action="store_true",
                              help="从本地 Chrome 用户数据创建")
    
    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除 profile")
    delete_parser.add_argument("profile_id", type=str, help="要删除的 profile ID")
    delete_parser.add_argument("--force", action="store_true", help="强制删除（即使正在使用）")
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="显示 profile 信息")
    info_parser.add_argument("profile_id", type=str, help="Profile ID")
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser("cleanup", help="清理非活跃的 profile")
    cleanup_parser.add_argument("--days", type=int, default=7,
                               help="清理多少天前创建的非活跃 profile（默认: 7）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "list":
        list_profiles(args.pool_dir)
    elif args.command == "create":
        create_profile(args.pool_dir, args.profile_id, args.from_local)
    elif args.command == "delete":
        delete_profile(args.pool_dir, args.profile_id, args.force)
    elif args.command == "info":
        show_profile_info(args.pool_dir, args.profile_id)
    elif args.command == "cleanup":
        cleanup_profiles(args.pool_dir, args.days)


if __name__ == "__main__":
    main()

