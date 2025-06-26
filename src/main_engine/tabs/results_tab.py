"""Tab xem và tải kết quả phân tích CV."""

import os

import pandas as pd
import streamlit as st

from modules.config import ATTACHMENT_DIR, OUTPUT_CSV, OUTPUT_EXCEL


def render() -> None:
    """Render UI for viewing and downloading results."""
    st.subheader("Xem và tải kết quả")
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
            return (
                f'<a download="{fname}" href="data:{mime};base64,{data}">{fname}</a>'
            )

        if "Nguồn" in df.columns:
            df["Nguồn"] = df["Nguồn"].apply(make_link)

        # Wrap long text fields with a scrollable container
        for col in ["Học vấn", "Kinh nghiệm", "Kỹ năng"]:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda v: f"<div class='cell-scroll'>{v}</div>" if pd.notna(v) else ""
                )

        table_html = df.to_html(escape=False, index=False)
        styled_html = (
            "<div class='results-table-container' style='max-height: 60vh; overflow: auto;'>"
            f"{table_html}"
            "</div>"
        )
        st.markdown(styled_html, unsafe_allow_html=True)
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        st.download_button(
            label="Tải xuống CSV",
            data=csv_bytes,
            file_name=OUTPUT_CSV.name,
            mime="text/csv",
            help="Lưu kết quả phân tích về máy",
        )
        if os.path.exists(OUTPUT_EXCEL):
            with open(OUTPUT_EXCEL, "rb") as f:
                st.download_button(
                    label="Tải xuống Excel",
                    data=f.read(),
                    file_name=OUTPUT_EXCEL.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="File Excel kèm link tới CV gốc",
                )
    else:
        st.info("Chưa có kết quả. Vui lòng chạy Batch hoặc Single.")
