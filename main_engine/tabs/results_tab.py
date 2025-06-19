import os
import pandas as pd
import streamlit as st

from modules.config import OUTPUT_CSV


def render() -> None:
    """Render UI for viewing and downloading results."""
    st.subheader("Xem và tải kết quả")
    if os.path.exists(OUTPUT_CSV):
        df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode()
        st.download_button(
            label="Tải xuống CSV",
            data=csv_bytes,
            file_name=OUTPUT_CSV.name,
            mime="text/csv",
        )
    else:
        st.info("Chưa có kết quả. Vui lòng chạy Batch hoặc Single.")
