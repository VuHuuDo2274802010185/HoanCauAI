"""Tab xem và tải kết quả phân tích CV."""

import os

import pandas as pd
import streamlit as st

from modules.config import ATTACHMENT_DIR, OUTPUT_CSV, OUTPUT_EXCEL


def render() -> None:
    """Render UI for viewing and downloading results."""
    st.subheader("📊 Xem và tải kết quả")
    
    # Thêm thông tin hướng dẫn
    st.markdown("""
    💡 **Hướng dẫn sử dụng:**
    - 👁️ = Xem CV trực tiếp (PDF)  
    - 📥 = Tải CV về máy tính
    - Click vào tên file để xem chi tiết CV trong tab "Xem CV"
    """)
    
    if os.path.exists(OUTPUT_CSV):
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig", keep_default_na=False)
        df.fillna("", inplace=True)  # Replace NaN with empty strings for display

        def make_link(fname: str) -> str:
            """Create a safe link that works across browsers."""
            path = (ATTACHMENT_DIR / fname).resolve()
            if not path.exists():
                return fname
            import base64

            data = base64.b64encode(path.read_bytes()).decode()
            mime = (
                "application/pdf"
                if path.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            # Tạo link download và link xem (chỉ cho PDF)
            download_link = f'<a download="{fname}" href="data:{mime};base64,{data}" title="Tải xuống">📥</a>'
            
            if path.suffix.lower() == ".pdf":
                view_link = f'<a href="data:application/pdf;base64,{data}" target="_blank" title="Xem PDF">👁️</a>'
                return f'{fname} {view_link} {download_link}'
            else:
                return f'{fname} {download_link}'

        if "Nguồn" in df.columns:
            df["Nguồn"] = df["Nguồn"].apply(make_link)

        # Wrap all columns so long text becomes scrollable
        for col in df.columns:
            df[col] = df[col].apply(
                lambda v: f"<div class='cell-scroll'>{v}</div>" if pd.notna(v) else ""
            )

        # Hiển thị số lượng kết quả
        st.markdown(f"**📋 Tổng số CV đã phân tích:** {len(df)} file")
        
        table_html = df.to_html(escape=False, index=False)
        styled_html = (
            "<div class='results-table-container' style='max-height: 60vh; overflow: auto;'>"
            f"{table_html}"
            "</div>"
        )
        st.markdown(styled_html, unsafe_allow_html=True)
        
        # Buttons để tải xuống
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
            st.download_button(
                label="📊 Tải xuống CSV",
                data=csv_bytes,
                file_name=OUTPUT_CSV.name,
                mime="text/csv",
                help="Lưu kết quả phân tích về máy dạng CSV",
                use_container_width=True
            )
        
        with col2:
            if os.path.exists(OUTPUT_EXCEL):
                with open(OUTPUT_EXCEL, "rb") as f:
                    st.download_button(
                        label="📈 Tải xuống Excel",
                        data=f.read(),
                        file_name=OUTPUT_EXCEL.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="File Excel kèm link tới CV gốc",
                        use_container_width=True
                    )
        
        with col3:
            st.markdown("""
            <a href="javascript:window.location.reload()" style="text-decoration: none;">
            <button style="background-color: #ff9800; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">
            🔄 Tải lại kết quả
            </button></a>
            """, unsafe_allow_html=True)
            
        # Thêm quick stats
        if len(df) > 0:
            st.markdown("---")
            st.subheader("📈 Thống kê nhanh")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tổng CV", len(df))
            
            with col2:
                pdf_count = sum(1 for fname in df["Nguồn"] if ".pdf" in fname.lower())
                st.metric("File PDF", pdf_count)
            
            with col3:
                docx_count = len(df) - pdf_count
                st.metric("File DOCX", docx_count)
                
            with col4:
                # Đếm CV có email
                if "Email" in df.columns:
                    email_count = sum(1 for email in df["Email"] if email.strip())
                    st.metric("Có Email", email_count)
                else:
                    st.metric("Có Email", "N/A")
                    
    else:
        st.info("📭 Chưa có kết quả. Vui lòng chạy Batch hoặc Single.")
        st.markdown("""
        ### 🚀 Để bắt đầu:
        1. **Tab "Lấy & Xử lý CV"** - Tải CV từ email và phân tích hàng loạt
        2. **Tab "Single File"** - Tải lên và phân tích 1 file CV
        3. **Tab "Xem CV"** - Xem trực tiếp các CV đã tải (nếu có)
        """)
