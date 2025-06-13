# mcp_server.py
import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import Dict

from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.config import (
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, 
    OUTPUT_CSV, ATTACHMENT_DIR
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Khởi tạo FastAPI app
app = FastAPI(
    title="Trình Trích Xuất CV AI - MCP Server",
    description="API để điều khiển việc trích xuất thông tin từ CV cho AI Agent.",
    version="1.0.0",
)

@app.post("/run-full-process", summary="Chạy toàn bộ quy trình")
async def run_full_process():
    """
    Kích hoạt quy trình hoàn chỉnh:
    1. Kết nối email.
    2. Tải về các file CV mới.
    3. Dùng AI trích xuất thông tin.
    4. Lưu kết quả vào file cv_summary.csv.
    """
    if not all([EMAIL_USER, EMAIL_PASS]):
        raise HTTPException(status_code=400, detail="EMAIL_USER và EMAIL_PASS chưa được cấu hình trong .env")

    try:
        logging.info("Bắt đầu quy trình xử lý đầy đủ...")
        fetcher = EmailFetcher(host=EMAIL_HOST, port=EMAIL_PORT, user=EMAIL_USER, password=EMAIL_PASS)
        fetcher.connect()

        processor = CVProcessor(fetcher)
        df = processor.process()

        if not df.empty:
            processor.save_to_csv(df, OUTPUT_CSV)
            message = f"Hoàn tất! Đã xử lý và lưu {len(df)} hồ sơ."
        else:
            message = "Hoàn tất! Không có hồ sơ mới nào được xử lý."
        
        logging.info(message)
        return {"status": "success", "message": message, "records_processed": len(df) if not df.empty else 0}

    except Exception as e:
        logging.error(f"Lỗi trong quá trình xử lý: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-single-cv", summary="Xử lý một file CV duy nhất")
async def process_single_cv(file: UploadFile = File(...)) -> Dict:
    """
    Tải lên một file CV (.pdf, .docx) và nhận lại ngay kết quả trích xuất.
    File không được lưu lại trên server.
    """
    # Lưu file tạm thời
    temp_path = os.path.join(ATTACHMENT_DIR, f"temp_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Xử lý file
        processor = CVProcessor() # Không cần fetcher
        text = processor.extract_text(temp_path)
        if not text:
             raise HTTPException(status_code=400, detail="Không thể trích xuất văn bản từ file.")
        
        info = processor.extract_info_with_llm(text)
        return info

    except Exception as e:
        logging.error(f"Lỗi khi xử lý file đơn lẻ: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Xóa file tạm
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/results", summary="Tải file kết quả CSV")
async def get_results():
    """
    Tải về file `cv_summary.csv` chứa tất cả các kết quả đã được xử lý.
    """
    if not os.path.exists(OUTPUT_CSV):
        raise HTTPException(status_code=404, detail=f"File kết quả '{OUTPUT_CSV}' không tìm thấy. Hãy chạy quy trình xử lý trước.")
    
    return FileResponse(path=OUTPUT_CSV, media_type='text/csv', filename=os.path.basename(OUTPUT_CSV))

@app.get("/", summary="Health Check")
async def root():
    return {"message": "MCP Server for CV Extractor is running."}