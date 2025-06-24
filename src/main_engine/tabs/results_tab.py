import os

import pandas as pd
import streamlit as st

from modules.config import ATTACHMENT_DIR, OUTPUT_CSV, OUTPUT_EXCEL


def render() -> None:
    """Render UI for viewing and downloading results."""
    st.subheader("Xem và tải kết quả")
    if os.path.exists(OUTPUT_CSV):
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")

        def make_link(fname: str) -> str:
            path = (ATTACHMENT_DIR / fname).resolve()
            return f'<a href="file://{path}" target="_blank">{fname}</a>'

        if "Nguồn" in df.columns:
            df["Nguồn"] = df["Nguồn"].apply(make_link)

        st.markdown(
            df.to_html(escape=False, index=False),
            unsafe_allow_html=True,
        )
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
