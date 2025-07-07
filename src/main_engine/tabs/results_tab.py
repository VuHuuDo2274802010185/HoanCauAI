"""Tab xem và tải kết quả phân tích CV."""  # Mô tả chức năng của module

# Import các thư viện cần thiết
import os  # Thư viện để thao tác với file system và kiểm tra file tồn tại

import pandas as pd  # Thư viện xử lý dữ liệu dạng bảng (DataFrame)
import streamlit as st  # Framework tạo ứng dụng web

# Import các đường dẫn file từ cấu hình
from modules.config import ATTACHMENT_DIR, OUTPUT_CSV, OUTPUT_EXCEL


def render() -> None:
    """Render UI for viewing and downloading results."""  # Hàm hiển thị giao diện xem và tải kết quả
    st.subheader("Xem và tải kết quả")  # Hiển thị tiêu đề phụ
    
    # Kiểm tra xem file CSV kết quả có tồn tại hay không
    if os.path.exists(OUTPUT_CSV):
        # Đọc dữ liệu từ file CSV với encoding UTF-8 và giữ nguyên giá trị rỗng
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig", keep_default_na=False)
        df.fillna("", inplace=True)  # Thay thế các giá trị NaN bằng chuỗi rỗng để hiển thị

        # Hàm tạo link download an toàn cho các file CV
        def make_link(fname: str) -> str:
            """Create a safe link that works across browsers."""  # Tạo link download hoạt động trên các trình duyệt
            path = (ATTACHMENT_DIR / fname).resolve()  # Tạo đường dẫn tuyệt đối đến file
            if not path.exists():  # Kiểm tra file có tồn tại không
                return fname  # Trả về tên file nếu không tồn tại
            import base64  # Import thư viện mã hóa base64

            # Mã hóa nội dung file thành base64 để tạo data URL
            data = base64.b64encode(path.read_bytes()).decode()
            # Xác định MIME type dựa trên extension file
            mime = (
                "application/pdf"  # MIME type cho file PDF
                if path.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # MIME type cho file DOCX
            )
            # Tạo HTML link với data URL để download file
            return (
                f'<a download="{fname}" href="data:{mime};base64,{data}">{fname}</a>'
            )

        # Nếu có cột "Nguồn", chuyển đổi tên file thành link download
        if "Nguồn" in df.columns:
            df["Nguồn"] = df["Nguồn"].apply(make_link)

        # Wrap tất cả các cột để text dài có thể scroll được
        for col in df.columns:
            df[col] = df[col].apply(
                lambda v: f"<div class='cell-scroll'>{v}</div>" if pd.notna(v) else ""  # Wrap nội dung trong div có class scroll
            )

        # Chuyển DataFrame thành HTML table
        table_html = df.to_html(escape=False, index=False)  # Không escape HTML và không hiển thị index
        # Tạo container có scroll cho bảng kết quả
        styled_html = (
            "<div class='results-table-container' style='max-height: 60vh; overflow: auto;'>"
            f"{table_html}"
            "</div>"
        )
        st.markdown(styled_html, unsafe_allow_html=True)  # Hiển thị bảng với HTML
        
        # Tạo dữ liệu CSV để download
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        # Tạo nút download file CSV
        st.download_button(
            label="Tải xuống CSV",  # Nhãn nút
            data=csv_bytes,  # Dữ liệu file
            file_name=OUTPUT_CSV.name,  # Tên file khi download
            mime="text/csv",  # MIME type
            help="Lưu kết quả phân tích về máy",  # Tooltip hướng dẫn
        )
        
        # Kiểm tra và tạo nút download file Excel nếu tồn tại
        if os.path.exists(OUTPUT_EXCEL):
            # Đọc file Excel dưới dạng binary
            with open(OUTPUT_EXCEL, "rb") as f:
                # Tạo nút download file Excel
                st.download_button(
                    label="Tải xuống Excel",  # Nhãn nút
                    data=f.read(),  # Đọc toàn bộ dữ liệu file
                    file_name=OUTPUT_EXCEL.name,  # Tên file khi download
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # MIME type cho Excel
                    help="File Excel kèm link tới CV gốc",  # Tooltip hướng dẫn
                )
    else:
        # Hiển thị thông báo nếu chưa có kết quả
        st.info("Chưa có kết quả. Vui lòng chạy Batch hoặc Single.")
