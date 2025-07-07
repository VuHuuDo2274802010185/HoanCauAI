"""Tab kết hợp lấy và xử lý CV từ email."""  # Mô tả chức năng của module

# Import các thư viện cơ bản
import logging  # Thư viện ghi log để theo dõi hoạt động của ứng dụng
from typing import List  # Type hints cho danh sách
from pathlib import Path  # Thư viện xử lý đường dẫn file/folder hiện đại
from datetime import datetime, time, timezone, date  # Thư viện xử lý ngày tháng và thời gian
import base64  # Thư viện mã hóa/giải mã base64 cho file download

# Import module quản lý thanh tiến trình
from modules.progress_manager import StreamlitProgressBar

# Import thư viện xử lý dữ liệu và giao diện
import pandas as pd  # Thư viện xử lý dữ liệu dạng bảng
import streamlit as st  # Framework tạo ứng dụng web

# Import các module cấu hình và hằng số
from modules.config import (
    ATTACHMENT_DIR,  # Thư mục lưu file đính kèm
    EMAIL_HOST,  # Host server email
    EMAIL_PORT,  # Port kết nối email
    OUTPUT_CSV,  # Đường dẫn file CSV output
    OUTPUT_EXCEL,  # Đường dẫn file Excel output
    SENT_TIME_FILE,  # File lưu thời gian gửi email
    EMAIL_UNSEEN_ONLY,  # Cờ chỉ xử lý email chưa đọc
    get_model_price,  # Hàm lấy giá của model AI
)
# Import các module xử lý chính
from modules.email_fetcher import EmailFetcher  # Module lấy email và file đính kèm
from modules.cv_processor import CVProcessor, format_sent_time_display  # Module xử lý CV và format thời gian
from modules.dynamic_llm_client import DynamicLLMClient  # Client kết nối với các LLM khác nhau
from modules.sent_time_store import load_sent_times  # Module lưu trữ thời gian gửi email
from ..utils import safe_session_state_get  # Utility để lấy session state an toàn


def render(
    provider: str,  # Nhà cung cấp AI (OpenAI, Anthropic, etc.)
    model: str,  # Tên model AI sử dụng
    api_key: str,  # API key để xác thực
    email_user: str = "",  # Tài khoản email (mặc định rỗng)
    email_pass: str = "",  # Mật khẩu email (mặc định rỗng)
) -> None:
    """Render UI for fetching and processing CVs."""  # Hàm hiển thị giao diện lấy và xử lý CV
    st.subheader("Lấy & Xử lý CV")  # Hiển thị tiêu đề phụ
    
    # Lấy giá của model và tạo label hiển thị
    price = get_model_price(model)
    label = f"{model} ({price})" if price != "unknown" else model  # Thêm giá vào label nếu có
    st.markdown(f"**LLM:** `{provider}` / `{label}`")  # Hiển thị thông tin LLM đang sử dụng
    
    # Kiểm tra thông tin đăng nhập email
    if not email_user or not email_pass:
        st.warning("Cần nhập Gmail và mật khẩu trong sidebar để fetch CV.")  # Cảnh báo nếu thiếu thông tin
        fetcher = None  # Không khởi tạo fetcher
    else:
        # Khởi tạo email fetcher với thông tin đăng nhập
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, email_user, email_pass)
        fetcher.connect()  # Kết nối đến server email
        
        # Hiển thị trạng thái UID hiện tại
        if fetcher:
            last_uid = fetcher.get_last_processed_uid()  # Lấy UID email cuối cùng đã xử lý
            if last_uid:
                st.info(f"📧 Last processed UID: {last_uid}")  # Hiển thị UID cuối cùng
            else:
                st.info("📧 No previous UID found - will process all emails")  # Thông báo chưa có UID

    # Tạo 2 cột để nhập khoảng thời gian tìm kiếm
    col1, col2 = st.columns(2)
    today_str = date.today().strftime("%d/%m/%Y")  # Lấy ngày hôm nay dạng string
    
    # Cột 1: Ngày bắt đầu
    with col1:
        from_date_str = st.text_input("From (DD/MM/YYYY)", value="")  # Ô nhập ngày bắt đầu
    
    # Cột 2: Ngày kết thúc
    with col2:
        to_date_str = st.text_input("To (DD/MM/YYYY)", value="", placeholder=today_str)  # Ô nhập ngày kết thúc

    # Checkbox chọn chỉ quét email chưa đọc
    unseen_only = st.checkbox(
        "👁️ Chỉ quét email chưa đọc",
        value=safe_session_state_get("unseen_only", EMAIL_UNSEEN_ONLY),  # Lấy giá trị từ session state hoặc config
        key="unseen_only",
        help="Nếu bỏ chọn, hệ thống sẽ quét toàn bộ hộp thư",
    )
    
    # Checkbox bỏ qua UID đã lưu
    ignore_last_uid = st.checkbox(
        "🔄 Bỏ qua UID đã lưu (xử lý lại tất cả email)",
        value=False,  # Mặc định là False
        key="ignore_last_uid",
        help="Bỏ qua UID đã lưu và xử lý lại tất cả email từ đầu",
    )
    
    st.divider()  # Tạo đường phân cách
    
    # Tạo 3 cột cho các nút bấm
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
    
    # Cột 3: Nút Reset UID
    with col_btn3:
        if st.button("🗑️ Reset UID", help="Xóa UID đã lưu để xử lý lại từ đầu"):
            if fetcher:  # Kiểm tra nếu có kết nối email
                fetcher.reset_uid_store()  # Reset UID store
                st.success("✅ Đã reset UID store!")  # Thông báo thành công
                st.rerun()  # Refresh trang
            else:
                st.error("❌ Cần kết nối email trước")  # Lỗi nếu chưa kết nối
    
    # Cột 1: Nút Fetch
    with col_btn1:
        fetch_button = st.button("📥 Fetch", help="Tải email CV từ hộp thư")
    
    # Cột 2: Nút Process
    with col_btn2:
        process_button = st.button("⚙️ Process", help="Phân tích CV đã tải về")
    
    st.markdown("---")  # Tạo đường phân cách

    # Xử lý khi nhấn nút Fetch
    if fetch_button:
        if not fetcher:  # Kiểm tra nếu chưa có kết nối email
            st.error("❌ Cần kết nối email trước khi fetch")
        else:
            logging.info("Bắt đầu fetch CV từ email")  # Ghi log bắt đầu fetch
            
            # Chuyển đổi string ngày thành datetime object với timezone UTC
            from_dt = (
                datetime.combine(
                    datetime.strptime(from_date_str, "%d/%m/%Y"),  # Parse string thành datetime
                    time.min,  # Đặt thời gian là 00:00:00
                    tzinfo=timezone.utc,  # Đặt timezone UTC
                )
                if from_date_str  # Chỉ thực hiện nếu có nhập ngày bắt đầu
                else None
            )
            to_dt = (
                datetime.combine(
                    datetime.strptime(to_date_str, "%d/%m/%Y"),  # Parse string thành datetime
                    time.max,  # Đặt thời gian là 23:59:59
                    tzinfo=timezone.utc,  # Đặt timezone UTC
                )
                if to_date_str  # Chỉ thực hiện nếu có nhập ngày kết thúc
                else None
            )
            # Chuyển datetime thành date object để truyền vào hàm fetch
            since = from_dt.date() if from_dt else None
            before = to_dt.date() if to_dt else None
            
            status_placeholder = st.empty()  # Tạo placeholder để hiển thị trạng thái
            with st.spinner("📥 Đang tải email..."):  # Hiển thị spinner loading
                try:
                    status_placeholder.info("🔍 Đang tìm kiếm email...")  # Cập nhật trạng thái
                    # Gọi hàm fetch CV attachments từ email
                    new_files = fetcher.fetch_cv_attachments(
                        since=since,  # Ngày bắt đầu
                        before=before,  # Ngày kết thúc
                        unseen_only=unseen_only,  # Chỉ email chưa đọc
                        ignore_last_uid=ignore_last_uid,  # Bỏ qua UID đã lưu
                    )
                    status_placeholder.empty()  # Xóa placeholder trạng thái
                    
                    # Kiểm tra kết quả fetch
                    if new_files:
                        st.success(f"✅ Đã tải xuống {len(new_files)} file CV mới:")  # Thông báo thành công
                        # Hiển thị danh sách file đã tải
                        for file_path in new_files:
                            st.write(f"- {Path(file_path).name}")
                        
                        # Hiển thị UID mới sau khi fetch
                        new_uid = fetcher.get_last_processed_uid()
                        if new_uid:
                            st.info(f"📧 Updated last processed UID: {new_uid}")
                    else:
                        st.info("📧 Không tìm thấy CV mới để tải về")  # Thông báo không có file mới
                        
                except Exception as e:  # Xử lý ngoại lệ
                    status_placeholder.empty()  # Xóa placeholder
                    st.error(f"❌ Lỗi khi fetch email: {e}")  # Hiển thị lỗi
                    logging.error(f"Fetch error: {e}")  # Ghi log lỗi

    # Xử lý khi nhấn nút Process
    if process_button:
        logging.info("Bắt đầu process CV đã tải về")  # Ghi log bắt đầu xử lý
        
        # Chuyển đổi string ngày thành datetime object (tương tự phần fetch)
        from_dt = (
            datetime.combine(
                datetime.strptime(from_date_str, "%d/%m/%Y"),
                time.min,
                tzinfo=timezone.utc,
            )
            if from_date_str
            else None
        )
        to_dt = (
            datetime.combine(
                datetime.strptime(to_date_str, "%d/%m/%Y"),
                time.max,
                tzinfo=timezone.utc,
            )
            if to_date_str
            else None
        )
        
        # Tạo container cho thanh tiến trình
        progress_container = st.container()
        with progress_container:
            # Khởi tạo thanh tiến trình
            progress_bar = StreamlitProgressBar(progress_container)
            progress_bar.initialize(100, "⚙️ Đang khởi tạo xử lý CV...")

            # Khởi tạo CV processor
            processor = CVProcessor(
                fetcher=None,  # Không fetch, chỉ xử lý file có sẵn
                llm_client=DynamicLLMClient(provider=provider, model=model, api_key=api_key),  # Client LLM
            )

            # Định nghĩa callback function để cập nhật tiến trình
            def progress_callback(current, message):
                progress_bar.update(current, message)

            # Gọi hàm xử lý CV
            df = processor.process(
                unseen_only=False,  # Xử lý tất cả file trong thư mục
                since=None,  # Không lọc theo ngày email khi xử lý file có sẵn
                before=None,
                from_time=from_dt,  # Thời gian bắt đầu để lọc
                to_time=to_dt,  # Thời gian kết thúc để lọc
                progress_callback=progress_callback,  # Callback cập nhật tiến trình
                ignore_last_uid=False,  # Không liên quan khi fetcher là None
            )

            progress_bar.finish("✅ Xử lý CV hoàn tất!")  # Hoàn thành thanh tiến trình

        # Kiểm tra kết quả xử lý
        if df.empty:
            st.info("📁 Không có CV nào trong thư mục attachments để xử lý.")  # Thông báo không có CV
        else:
            # Lưu kết quả vào file CSV và Excel
            processor.save_to_csv(df, str(OUTPUT_CSV))
            processor.save_to_excel(df, str(OUTPUT_EXCEL))
            logging.info("Đã xử lý %s CV và lưu kết quả", len(df))  # Ghi log kết quả
            st.success(
                f"✅ Đã xử lý {len(df)} CV và lưu vào `{OUTPUT_CSV.name}` và `{OUTPUT_EXCEL.name}`."
            )

    # Lấy danh sách file attachments
    attachments = [
        p  # Đường dẫn file
        for p in ATTACHMENT_DIR.glob("*")  # Quét tất cả file trong thư mục attachments
        if p.is_file()  # Chỉ lấy file (không phải thư mục)
        and p != SENT_TIME_FILE  # Loại trừ file lưu thời gian gửi
        and p.suffix.lower() in (".pdf", ".docx")  # Chỉ lấy file PDF và DOCX
    ]
    
    # Nếu có file attachments
    if attachments:
        sent_map = load_sent_times()  # Load map thời gian gửi từ file

        # Hàm tạo key để sắp xếp file theo thời gian
        def sort_key(p: Path) -> float:
            ts = sent_map.get(p.name)  # Lấy timestamp từ map
            if ts:
                try:
                    # Chuyển đổi ISO string thành timestamp
                    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                except Exception:
                    pass
            # Nếu không có thời gian gửi, dùng thời gian modify file
            return p.stat().st_mtime

        # Sắp xếp file theo thời gian giảm dần (mới nhất trước)
        attachments.sort(key=sort_key, reverse=True)

        # Hàm tạo link download cho file
        def make_link(path: Path) -> str:
            data = base64.b64encode(path.read_bytes()).decode()  # Mã hóa file thành base64
            # Xác định MIME type theo extension
            mime = (
                "application/pdf"
                if path.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            # Tạo link download HTML
            return f'<a download="{path.name}" href="data:{mime};base64,{data}">{path.name}</a>'

        # Tạo danh sách dữ liệu cho bảng
        rows = []
        for p in attachments:
            sent = format_sent_time_display(sent_map.get(p.name, ""))  # Format thời gian gửi
            size_kb = p.stat().st_size / 1024  # Tính kích thước file (KB)
            rows.append({
                "File": make_link(p),  # Link download
                "Dung lượng": f"{size_kb:.1f} KB",  # Kích thước file
                "Gửi lúc": sent,  # Thời gian gửi
            })

        # Tạo DataFrame và chuyển thành HTML table
        df = pd.DataFrame(rows, columns=["File", "Dung lượng", "Gửi lúc"])
        table_html = df.to_html(escape=False, index=False)  # Không escape HTML để link hoạt động
        # Tạo container có scroll cho bảng
        styled_html = (
            "<div class='attachments-table-container' style='max-height: 400px; overflow:auto;'>"
            f"{table_html}"
            "</div>"
        )
        st.markdown(styled_html, unsafe_allow_html=True)  # Hiển thị bảng
    else:
        st.info("Chưa có CV nào được tải về.")  # Thông báo nếu chưa có file

    # Nút xóa toàn bộ attachments
    if st.button("Xóa toàn bộ attachments", help="Xoá tất cả file đã tải"):
        st.session_state.confirm_delete = True  # Đặt flag confirm delete
    
    # Xử lý xác nhận xóa file
    if st.session_state.get("confirm_delete"):
        st.warning("Bạn có chắc muốn xoá toàn bộ attachments? Thao tác không thể hoàn tác.")  # Cảnh báo
        col1, col2 = st.columns(2)  # Tạo 2 cột cho nút xác nhận và hủy
        
        # Cột 1: Nút xác nhận xóa
        with col1:
            if st.button("Xác nhận xoá", key="confirm_delete_btn"):
                attachments = list(ATTACHMENT_DIR.iterdir())  # Lấy danh sách tất cả file trong thư mục
                count = sum(1 for f in attachments if f.is_file())  # Đếm số file
                # Xóa từng file
                for f in attachments:
                    try:
                        f.unlink()  # Xóa file
                    except Exception:
                        pass  # Bỏ qua nếu có lỗi
                logging.info(f"Đã xóa {count} file trong attachments")  # Ghi log
                st.success(f"Đã xóa {count} file trong thư mục attachments.")  # Thông báo thành công
                st.session_state.confirm_delete = False  # Reset flag
        
        # Cột 2: Nút hủy
        with col2:
            if st.button("Huỷ", key="cancel_delete_btn"):
                st.session_state.confirm_delete = False  # Reset flag để hủy thao tác
