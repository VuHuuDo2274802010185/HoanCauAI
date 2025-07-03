"""Tab quản lý cập nhật và backup."""

import streamlit as st
import logging
from pathlib import Path
from datetime import datetime
import json

from modules.update_manager import UpdateManager
from ..utils import safe_session_state_get, safe_session_state_set

logger = logging.getLogger(__name__)

def render():
    """Render UI cho quản lý cập nhật"""
    st.subheader("🔄 Quản lý cập nhật & Backup")
    
    # Khởi tạo UpdateManager
    try:
        app_root = Path(__file__).parent.parent.parent.parent
        update_manager = UpdateManager(app_root)
    except Exception as e:
        st.error(f"Lỗi khởi tạo UpdateManager: {e}")
        return
    
    # Hiển thị thông tin phiên bản hiện tại
    current_version = update_manager.get_current_version()
    
    st.markdown("### 📋 Thông tin phiên bản hiện tại")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Phiên bản:** {current_version.get('version', 'unknown')}")
        st.info(f"**Build:** {current_version.get('build', 'unknown')}")
    
    with col2:
        st.info(f"**Cập nhật lần cuối:** {current_version.get('updated_at', 'unknown')}")
        features = current_version.get('features', [])
        if features:
            st.info(f"**Tính năng:** {len(features)} tính năng")
    
    # Tabs con
    tab_update, tab_backup, tab_restore = st.tabs([
        "🔄 Cập nhật", 
        "💾 Tạo Backup", 
        "🔙 Khôi phục"
    ])
    
    with tab_update:
        render_update_tab(update_manager)
    
    with tab_backup:
        render_backup_tab(update_manager)
    
    with tab_restore:
        render_restore_tab(update_manager)

def render_update_tab(update_manager: UpdateManager):
    """Tab cập nhật"""
    st.markdown("### 🔍 Kiểm tra cập nhật")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Kiểm tra cập nhật", help="Kiểm tra phiên bản mới từ repository"):
            with st.spinner("Đang kiểm tra cập nhật..."):
                try:
                    has_update, update_info = update_manager.check_for_updates()
                    
                    if has_update:
                        st.success("🎉 Có phiên bản mới!")
                        st.json(update_info)
                        safe_session_state_set("update_available", True)
                        safe_session_state_set("update_info", update_info)
                    else:
                        st.info("✅ Bạn đang sử dụng phiên bản mới nhất.")
                        safe_session_state_set("update_available", False)
                
                except Exception as e:
                    st.error(f"Lỗi kiểm tra cập nhật: {e}")
    
    with col2:
        if st.button("💾 Tạo Backup trước khi cập nhật", help="Tạo backup để có thể rollback"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Đang tạo backup...")
                backup_path = update_manager.create_backup()
                progress_bar.progress(1.0)
                status_text.text("✅ Backup hoàn thành!")
                
                st.success(f"✅ Đã tạo backup: {backup_path.name}")
                
                # Cleanup progress
                import time
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"Lỗi tạo backup: {e}")
    
    # Hiển thị thông tin cập nhật nếu có
    if safe_session_state_get("update_available", False):
        update_info = safe_session_state_get("update_info", {})
        
        st.markdown("### 📦 Cập nhật có sẵn")
        st.info(f"**Phiên bản mới:** {update_info.get('version', 'unknown')}")
        st.info(f"**Commit:** {update_info.get('commit_sha', 'unknown')[:8]}")
        st.info(f"**Tin nhắn:** {update_info.get('message', 'No message')}")
        st.info(f"**Tác giả:** {update_info.get('author', 'unknown')}")
        
        st.warning("⚠️ **Lưu ý:** Hãy tạo backup trước khi cập nhật để có thể khôi phục nếu cần!")
        
        if st.button("🚀 Cập nhật ngay", type="primary", help="Tải và cài đặt phiên bản mới"):
            # Tạo progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(current, total, message):
                if total > 0:
                    progress_value = min(current / total, 1.0)
                    progress_bar.progress(progress_value)
                status_text.text(message)
            
            try:
                # Tạo backup tự động
                status_text.text("💾 Tạo backup tự động...")
                backup_path = update_manager.create_backup(f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                # Tải cập nhật
                update_zip = update_manager.download_update(progress_callback)
                
                # Áp dụng cập nhật
                success = update_manager.apply_update(update_zip, progress_callback)
                
                if success:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Cập nhật hoàn thành!")
                    
                    st.success("🎉 Cập nhật thành công! Vui lòng khởi động lại ứng dụng.")
                    st.balloons()
                    
                    # Reset update state
                    safe_session_state_set("update_available", False)
                    safe_session_state_set("update_info", {})
                else:
                    st.error("❌ Cập nhật thất bại. Vui lòng thử lại hoặc khôi phục từ backup.")
                
                # Cleanup progress
                import time
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"Lỗi trong quá trình cập nhật: {e}")

def render_backup_tab(update_manager: UpdateManager):
    """Tab tạo backup"""
    st.markdown("### 💾 Tạo Backup thủ công")
    
    backup_name = st.text_input(
        "Tên backup (tùy chọn)", 
        placeholder="Để trống để tự động tạo tên",
        help="Tên backup sẽ được tự động tạo nếu để trống"
    )
    
    if st.button("💾 Tạo Backup", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Đang tạo backup...")
            progress_bar.progress(0.5)
            
            backup_path = update_manager.create_backup(backup_name if backup_name else None)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Backup hoàn thành!")
            
            st.success(f"✅ Đã tạo backup: {backup_path.name}")
            
            # Cleanup progress
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Lỗi tạo backup: {e}")
    
    # Hiển thị danh sách backup
    st.markdown("### 📁 Danh sách Backup")
    
    try:
        backups = update_manager.list_backups()
        
        if not backups:
            st.info("Chưa có backup nào.")
        else:
            for backup in backups:
                with st.expander(f"📦 {backup['name']} ({backup['size']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.text(f"Tạo lúc: {backup['created_at'][:19].replace('T', ' ')}")
                    
                    with col2:
                        version_info = backup['version']
                        st.text(f"Phiên bản: {version_info.get('version', 'unknown')}")
                    
                    with col3:
                        if st.button(f"🗑️ Xóa", key=f"delete_{backup['name']}", help="Xóa backup này"):
                            if update_manager.delete_backup(backup['name']):
                                st.success(f"Đã xóa backup: {backup['name']}")
                                st.rerun()
                            else:
                                st.error("Lỗi xóa backup")
            
            # Nút dọn dẹp
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                keep_count = st.number_input("Giữ lại số backup", min_value=1, max_value=20, value=5)
            
            with col2:
                if st.button("🧹 Dọn dẹp backup cũ"):
                    deleted_count = update_manager.cleanup_old_backups(keep_count)
                    if deleted_count > 0:
                        st.success(f"Đã xóa {deleted_count} backup cũ")
                        st.rerun()
                    else:
                        st.info("Không có backup nào cần xóa")
    
    except Exception as e:
        st.error(f"Lỗi liệt kê backup: {e}")

def render_restore_tab(update_manager: UpdateManager):
    """Tab khôi phục"""
    st.markdown("### 🔙 Khôi phục từ Backup")
    
    try:
        backups = update_manager.list_backups()
        
        if not backups:
            st.info("Chưa có backup nào để khôi phục.")
            return
        
        # Chọn backup để khôi phục
        backup_options = {f"{b['name']} ({b['created_at'][:19]})": b['name'] for b in backups}
        
        selected_display = st.selectbox(
            "Chọn backup để khôi phục:",
            options=list(backup_options.keys()),
            help="Chọn backup để khôi phục ứng dụng về phiên bản trước"
        )
        
        if selected_display:
            selected_backup = backup_options[selected_display]
            
            # Hiển thị thông tin backup được chọn
            backup_info = next(b for b in backups if b['name'] == selected_backup)
            
            st.markdown("#### 📋 Thông tin Backup")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Tên:** {backup_info['name']}")
                st.info(f"**Kích thước:** {backup_info['size']}")
            
            with col2:
                st.info(f"**Tạo lúc:** {backup_info['created_at'][:19].replace('T', ' ')}")
                version_info = backup_info['version']
                st.info(f"**Phiên bản:** {version_info.get('version', 'unknown')}")
            
            st.warning("⚠️ **Cảnh báo:** Khôi phục sẽ ghi đè toàn bộ ứng dụng hiện tại. Hãy tạo backup trước khi khôi phục!")
            
            # Checkbox xác nhận
            confirm = st.checkbox("Tôi hiểu rủi ro và muốn khôi phục", key="confirm_restore")
            
            if confirm and st.button("🔙 Khôi phục ngay", type="primary"):
                # Tạo progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total, message):
                    if total > 0:
                        progress_value = min(current / total, 1.0)
                        progress_bar.progress(progress_value)
                    status_text.text(message)
                
                try:
                    # Tạo backup trước khi khôi phục
                    status_text.text("💾 Tạo backup hiện tại...")
                    current_backup = update_manager.create_backup(f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    
                    # Khôi phục
                    success = update_manager.revert_to_backup(selected_backup, progress_callback)
                    
                    if success:
                        progress_bar.progress(1.0)
                        status_text.text("✅ Khôi phục hoàn thành!")
                        
                        st.success("🎉 Khôi phục thành công! Vui lòng khởi động lại ứng dụng.")
                        st.balloons()
                    else:
                        st.error("❌ Khôi phục thất bại.")
                    
                    # Cleanup progress
                    import time
                    time.sleep(2)
                    progress_bar.empty()
                    status_text.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Lỗi trong quá trình khôi phục: {e}")
    
    except Exception as e:
        st.error(f"Lỗi load danh sách backup: {e}")
