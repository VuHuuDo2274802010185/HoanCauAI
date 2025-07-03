#!/usr/bin/env python3
"""CLI tool cho update và backup management"""

import argparse
import sys
from pathlib import Path
import logging

# Add src to path
HERE = Path(__file__).parent
ROOT = HERE.parent
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from modules.update_manager import UpdateManager

def setup_logging():
    """Setup logging for CLI"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_updates(args):
    """Kiểm tra cập nhật"""
    update_manager = UpdateManager()
    
    print("🔍 Kiểm tra cập nhật...")
    has_update, update_info = update_manager.check_for_updates()
    
    if has_update:
        print("🎉 Có phiên bản mới!")
        print(f"  📦 Phiên bản: {update_info.get('version', 'unknown')}")
        print(f"  💬 Message: {update_info.get('message', 'No message')}")
        print(f"  👤 Author: {update_info.get('author', 'unknown')}")
        print(f"  📅 Date: {update_info.get('commit_date', 'unknown')}")
        return True
    else:
        print("✅ Bạn đang sử dụng phiên bản mới nhất.")
        return False

def create_backup(args):
    """Tạo backup"""
    update_manager = UpdateManager()
    
    print("💾 Tạo backup...")
    try:
        backup_path = update_manager.create_backup(args.name)
        print(f"✅ Backup hoàn thành: {backup_path}")
    except Exception as e:
        print(f"❌ Lỗi tạo backup: {e}")
        sys.exit(1)

def list_backups(args):
    """Liệt kê backup"""
    update_manager = UpdateManager()
    
    backups = update_manager.list_backups()
    
    if not backups:
        print("📁 Chưa có backup nào.")
        return
    
    print("📁 Danh sách backup:")
    print("-" * 80)
    print(f"{'Tên':<30} {'Phiên bản':<15} {'Kích thước':<10} {'Tạo lúc'}")
    print("-" * 80)
    
    for backup in backups:
        name = backup['name']
        version = backup['version'].get('version', 'unknown')
        size = backup['size']
        created = backup['created_at'][:19].replace('T', ' ')
        print(f"{name:<30} {version:<15} {size:<10} {created}")

def restore_backup(args):
    """Khôi phục backup"""
    update_manager = UpdateManager()
    
    # Kiểm tra backup tồn tại
    backups = update_manager.list_backups()
    backup_names = [b['name'] for b in backups]
    
    if args.backup_name not in backup_names:
        print(f"❌ Không tìm thấy backup: {args.backup_name}")
        print("📁 Backup có sẵn:")
        for name in backup_names:
            print(f"  - {name}")
        sys.exit(1)
    
    # Xác nhận
    if not args.force:
        response = input(f"⚠️ Bạn có chắc muốn khôi phục '{args.backup_name}'? (y/N): ")
        if response.lower() != 'y':
            print("❌ Đã hủy khôi phục.")
            return
    
    print(f"🔙 Khôi phục từ backup: {args.backup_name}")
    
    def progress_callback(current, total, message):
        if total > 0:
            percent = current / total * 100
            print(f"[{percent:5.1f}%] {message}")
        else:
            print(f"[INFO] {message}")
    
    try:
        success = update_manager.revert_to_backup(args.backup_name, progress_callback)
        if success:
            print("✅ Khôi phục thành công!")
        else:
            print("❌ Khôi phục thất bại.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi khôi phục: {e}")
        sys.exit(1)

def update_app(args):
    """Cập nhật ứng dụng"""
    update_manager = UpdateManager()
    
    # Kiểm tra cập nhật
    print("🔍 Kiểm tra cập nhật...")
    has_update, update_info = update_manager.check_for_updates()
    
    if not has_update:
        print("✅ Bạn đang sử dụng phiên bản mới nhất.")
        return
    
    print("🎉 Có phiên bản mới!")
    print(f"  📦 Phiên bản: {update_info.get('version', 'unknown')}")
    print(f"  💬 Message: {update_info.get('message', 'No message')}")
    
    # Xác nhận
    if not args.force:
        response = input("⚠️ Bạn có muốn cập nhật? (y/N): ")
        if response.lower() != 'y':
            print("❌ Đã hủy cập nhật.")
            return
    
    def progress_callback(current, total, message):
        if total > 0:
            percent = current / total * 100
            print(f"[{percent:5.1f}%] {message}")
        else:
            print(f"[INFO] {message}")
    
    try:
        # Tạo backup tự động nếu không có --no-backup
        if not args.no_backup:
            print("💾 Tạo backup tự động...")
            from datetime import datetime
            backup_name = f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            update_manager.create_backup(backup_name)
            print(f"✅ Đã tạo backup: {backup_name}")
        
        # Tải và cập nhật
        print("📥 Tải cập nhật...")
        update_zip = update_manager.download_update(progress_callback)
        
        print("🔄 Áp dụng cập nhật...")
        success = update_manager.apply_update(update_zip, progress_callback)
        
        if success:
            print("🎉 Cập nhật thành công!")
            print("🔄 Vui lòng khởi động lại ứng dụng để áp dụng thay đổi.")
        else:
            print("❌ Cập nhật thất bại.")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Lỗi cập nhật: {e}")
        sys.exit(1)

def delete_backup(args):
    """Xóa backup"""
    update_manager = UpdateManager()
    
    backups = update_manager.list_backups()
    backup_names = [b['name'] for b in backups]
    
    if args.backup_name not in backup_names:
        print(f"❌ Không tìm thấy backup: {args.backup_name}")
        return
    
    # Xác nhận
    if not args.force:
        response = input(f"⚠️ Bạn có chắc muốn xóa '{args.backup_name}'? (y/N): ")
        if response.lower() != 'y':
            print("❌ Đã hủy xóa.")
            return
    
    if update_manager.delete_backup(args.backup_name):
        print(f"✅ Đã xóa backup: {args.backup_name}")
    else:
        print(f"❌ Lỗi xóa backup: {args.backup_name}")

def cleanup_backups(args):
    """Dọn dẹp backup cũ"""
    update_manager = UpdateManager()
    
    print(f"🧹 Dọn dẹp backup, giữ lại {args.keep} backup mới nhất...")
    deleted_count = update_manager.cleanup_old_backups(args.keep)
    
    if deleted_count > 0:
        print(f"✅ Đã xóa {deleted_count} backup cũ.")
    else:
        print("✅ Không có backup nào cần xóa.")

def main():
    parser = argparse.ArgumentParser(
        description="HoanCau AI Update Manager - Quản lý cập nhật và backup"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check updates
    check_parser = subparsers.add_parser('check', help='Kiểm tra cập nhật')
    
    # Update
    update_parser = subparsers.add_parser('update', help='Cập nhật ứng dụng')
    update_parser.add_argument('--force', action='store_true', help='Cập nhật mà không hỏi xác nhận')
    update_parser.add_argument('--no-backup', action='store_true', help='Không tạo backup tự động')
    
    # Backup
    backup_parser = subparsers.add_parser('backup', help='Tạo backup')
    backup_parser.add_argument('--name', help='Tên backup (tùy chọn)')
    
    # List backups
    list_parser = subparsers.add_parser('list', help='Liệt kê backup')
    
    # Restore
    restore_parser = subparsers.add_parser('restore', help='Khôi phục từ backup')
    restore_parser.add_argument('backup_name', help='Tên backup để khôi phục')
    restore_parser.add_argument('--force', action='store_true', help='Khôi phục mà không hỏi xác nhận')
    
    # Delete backup
    delete_parser = subparsers.add_parser('delete', help='Xóa backup')
    delete_parser.add_argument('backup_name', help='Tên backup để xóa')
    delete_parser.add_argument('--force', action='store_true', help='Xóa mà không hỏi xác nhận')
    
    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Dọn dẹp backup cũ')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Số backup giữ lại (mặc định: 5)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging()
    
    try:
        if args.command == 'check':
            check_updates(args)
        elif args.command == 'update':
            update_app(args)
        elif args.command == 'backup':
            create_backup(args)
        elif args.command == 'list':
            list_backups(args)
        elif args.command == 'restore':
            restore_backup(args)
        elif args.command == 'delete':
            delete_backup(args)
        elif args.command == 'cleanup':
            cleanup_backups(args)
    except KeyboardInterrupt:
        print("\n❌ Đã hủy bỏ.")
        sys.exit(1)

if __name__ == "__main__":
    main()
