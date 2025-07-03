# main_engine/select_top5.py

import os
import sys
# Đưa thư mục gốc vào sys.path để import modules
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# Include both the project root and `src` directory for direct execution
# so that imports like `modules.*` resolve properly.
SRC_DIR = os.path.join(ROOT, "src")
for path in (ROOT, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import json
import re
import pandas as pd
from modules.dynamic_llm_client import DynamicLLMClient
from modules.config import OUTPUT_CSV, LLM_CONFIG, get_model_price

# Khởi tạo LLM client
llm = DynamicLLMClient()

def read_cv_summary(path: str) -> pd.DataFrame:
    """Đọc DataFrame từ CSV tóm tắt CV."""
    if not os.path.isfile(path):
        print(f"[ERROR] Không tìm thấy file: {path}")
        sys.exit(1)
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"[INFO] Đã đọc {len(df)} hồ sơ từ {path}")
    return df

def extract_json(text: str) -> str:
    """
    Trích JSON từ response của AI.
    Hỗ trợ block ```json ...``` hoặc mảng thuần.
    """
    m = re.search(r'```json\s*([\s\S]+?)\s*```', text)
    if m:
        return m.group(1)
    m2 = re.search(r'(\[\s*{[\s\S]+?}\s*\])', text)
    if m2:
        return m2.group(1)
    return text

def select_top5_sources(df: pd.DataFrame) -> list:
    """
    Dùng AI chọn TOP 5 dựa trên tóm tắt.
    In ra model/provider, báo trạng thái AI hay fallback.
    """
    # In thông tin LLM
    price = get_model_price(LLM_CONFIG['model'])
    label = f"{LLM_CONFIG['model']} ({price})" if price != 'unknown' else LLM_CONFIG['model']
    print(f"[INFO] Sử dụng LLM: {LLM_CONFIG['provider']} / {label}")

    # Gọi AI
    prompt = (
        "Bạn là trợ lý AI chuyên đánh giá hồ sơ xin việc. "
        "Chọn TOP 5 hồ sơ tốt nhất dựa trên danh sách dưới đây. "
        "Chỉ trả về JSON mảng các chuỗi 'Nguồn'. "
        f"Dữ liệu: {json.dumps(df.to_dict(orient='records'), ensure_ascii=False)}"
    )
    print("[INFO] Gửi prompt đến AI...")
    used_ai = False
    try:
        resp = llm.generate_content([prompt])
        arr = json.loads(extract_json(resp))
        if not isinstance(arr, list) or not arr:
            raise ValueError("Kết quả không phải list hợp lệ")
        used_ai = True
        print(f"[INFO] AI chọn TOP 5: {arr}")
        return arr
    except Exception as e:
        print(f"[WARNING] AI lỗi hoặc parse JSON thất bại: {e}")
        fallback = df["Nguồn"].head(5).tolist()
        print(f"[INFO] Fallback TOP 5: {fallback}")
        return fallback
    finally:
        print(f"[INFO] Kết thúc chọn, phương thức: {'AI' if used_ai else 'fallback'}")

def main():
    """Entry-point: đọc CSV và in TOP 5."""
    path = OUTPUT_CSV if os.path.isfile(OUTPUT_CSV) else "csv/cv_summary.csv"
    df = read_cv_summary(path)
    top5 = select_top5_sources(df)
    print("\n=== TOP 5 Hồ sơ ===")
    for i, src in enumerate(top5, 1):
        print(f"{i}. {src}")

if __name__ == "__main__":
    main()
