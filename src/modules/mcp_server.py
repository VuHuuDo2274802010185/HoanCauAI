# modules/mcp_server.py

import shutil                    # sao chép luồng dữ liệu nhị phân
import logging                   # ghi log hoạt động ứng dụng
from pathlib import Path         # thao tác đường dẫn hướng đối tượng

from fastapi import FastAPI, UploadFile, File, HTTPException  # framework API và xử lý upload
from datetime import date, datetime
from fastapi.responses import FileResponse    # trả về file như response
from pydantic_settings import BaseSettings, SettingsConfigDict      # sử dụng BaseSettings với cấu hình cho Pydantic v2


from .cv_processor import CVProcessor    # lớp xử lý CV thành DataFrame
from .email_fetcher import EmailFetcher  # lớp fetch email và tải đính kèm
from .llm_client import LLMClient


class Settings(BaseSettings):
    """
    Lớp cấu hình ứng dụng, tự động load từ file .env
    """
    # Cho phép ignore các biến môi trường không định nghĩa trong model
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    email_host: str        # địa chỉ IMAP server
    email_port: int        # cổng IMAP SSL
    email_user: str        # tên đăng nhập email
    email_pass: str        # mật khẩu/app-password email
    attachment_dir: Path   # thư mục lưu tệp đính kèm
    output_csv: Path       # đường dẫn file CSV xuất kết quả
    output_excel: Path     # đường dẫn file Excel xuất kết quả
    email_unseen_only: bool = True  # chỉ quét email chưa đọc nếu True
    platform_api_key: str | None = None  # API key cho các platform (tùy chọn)


# Khởi tạo cấu hình từ biến môi trường
settings = Settings()

# Đảm bảo thư mục lưu attachments tồn tại
settings.attachment_dir.mkdir(parents=True, exist_ok=True)
# Đảm bảo thư mục chứa file kết quả tồn tại
settings.output_csv.parent.mkdir(parents=True, exist_ok=True)
settings.output_excel.parent.mkdir(parents=True, exist_ok=True)

# Cấu hình logging cho toàn ứng dụng
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Khởi tạo FastAPI app với metadata
app = FastAPI(title="CV AI MCP Server", version="1.0")


@app.get("/", summary="Health Check")
async def health():
    """
    Endpoint kiểm tra trạng thái service
    """
    return {"status": "ok"}


@app.post("/run-full-process", summary="Run full CV extraction process")
async def run_full(from_date: str | None = None, to_date: str | None = None):
    """Process all CV files in attachments and save results."""

    # Chuyển đổi chuỗi ngày (nếu có) sang datetime để lọc
    from_dt = datetime.strptime(from_date, "%d/%m/%Y") if from_date else None
    to_dt = datetime.strptime(to_date, "%d/%m/%Y") if to_date else None

    processor = CVProcessor(llm_client=LLMClient())
    df = processor.process(from_time=from_dt, to_time=to_dt)

    # Nếu không có CV mới, trả về số bản ghi đã xử lý = 0
    if df.empty:
        return {"processed": 0}

    # Lưu DataFrame vào CSV, ghi đè file cũ
    processor.save_to_csv(df, str(settings.output_csv))
    processor.save_to_excel(df, str(settings.output_excel))
    return {"processed": len(df)}


@app.post("/process-single-cv", summary="Process single CV file")
async def process_single_cv(file: UploadFile = File(...)):
    """
    Xử lý 1 file CV được upload:
    1. Lưu tạm file vào thư mục attachments
    2. Trích xuất text và thông tin
    3. Xóa file tạm
    4. Trả về dict kết quả
    """
    # Đường dẫn file tạm
    tmp_path = settings.attachment_dir / f"tmp_{file.filename}"

    # Ghi file upload vào ổ đĩa
    with tmp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Trích xuất text và thông tin
    processor = CVProcessor(llm_client=LLMClient())
    text = processor.extract_text(str(tmp_path))

    # Xóa file tạm (nếu có lỗi, chỉ log warning)
    try:
        tmp_path.unlink()
    except Exception as e:
        logging.warning(f"Không xóa được file tạm: {e}")

    # Nếu không trích xuất được text, trả về lỗi
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Cannot extract text from uploaded file"
        )

    # Trả về thông tin đã trích xuất
    return processor.extract_info_with_llm(text)


@app.get("/results", summary="Get processed results CSV")
async def get_results():
    """
    Trả về file CSV kết quả đã lưu
    """
    # Kiểm tra tồn tại của file kết quả
    if not settings.output_csv.exists():
        raise HTTPException(
            status_code=404,
            detail="Results not found"
        )

    # Trả về file CSV với tên gốc
    return FileResponse(
        path=str(settings.output_csv),
        media_type="text/csv",
        filename=settings.output_csv.name
    )


# === PILL RECOGNITION ENDPOINTS ===

# Import pill recognition integration
try:
    from .pill_recognition_integration import pill_recognition
    import io
    
    @app.get("/pill-recognition/status", summary="Check pill recognition system status")
    async def pill_recognition_status():
        """Check if pill recognition system is available."""
        return {
            "available": pill_recognition.is_available(),
            "status": "ready" if pill_recognition.is_available() else "not_available"
        }
    
    @app.post("/pill-recognition/predict", summary="Predict pill from single image")
    async def predict_pill(file: UploadFile = File(...), text: str = None):
        """
        Predict pill type from uploaded image.
        
        Args:
            file: Image file (jpg, png, etc.)
            text: Optional text input (if not provided, OCR will be used)
            
        Returns:
            Prediction results with confidence scores
        """
        if not pill_recognition.is_available():
            raise HTTPException(status_code=503, detail="Pill recognition system not available")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        try:
            # Read image data
            image_data = await file.read()
            
            # Make prediction
            result = pill_recognition.predict_pill(image_data, text)
            
            return {
                "filename": file.filename,
                "result": result
            }
            
        except Exception as e:
            logging.error(f"Pill prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
    @app.post("/pill-recognition/batch-predict", summary="Predict pills from multiple images")
    async def predict_pills_batch(files: list[UploadFile] = File(...)):
        """
        Predict pill types from multiple uploaded images.
        
        Args:
            files: List of image files
            
        Returns:
            List of prediction results
        """
        if not pill_recognition.is_available():
            raise HTTPException(status_code=503, detail="Pill recognition system not available")
        
        if len(files) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed per batch")
        
        try:
            # Read all image data
            image_data_list = []
            filenames = []
            
            for file in files:
                if not file.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail=f"File {file.filename} must be an image")
                
                image_data = await file.read()
                image_data_list.append(image_data)
                filenames.append(file.filename)
            
            # Make batch predictions
            results = pill_recognition.predict_pill_batch(image_data_list)
            
            # Add filenames to results
            for i, result in enumerate(results):
                result["filename"] = filenames[i]
            
            return {
                "batch_size": len(files),
                "results": results
            }
            
        except Exception as e:
            logging.error(f"Batch pill prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")
    
    @app.post("/pill-recognition/extract-text", summary="Extract text from pill image using OCR")
    async def extract_pill_text(file: UploadFile = File(...)):
        """
        Extract text from pill image using OCR.
        
        Args:
            file: Image file (jpg, png, etc.)
            
        Returns:
            Extracted text with confidence
        """
        if not pill_recognition.is_available():
            raise HTTPException(status_code=503, detail="Pill recognition system not available")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        try:
            # Read image data
            image_data = await file.read()
            
            # Extract text
            result = pill_recognition.extract_text_from_pill(image_data)
            
            return {
                "filename": file.filename,
                "result": result
            }
            
        except Exception as e:
            logging.error(f"Text extraction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

except ImportError:
    logging.warning("Pill recognition integration not available")
    
    @app.get("/pill-recognition/status", summary="Check pill recognition system status")
    async def pill_recognition_status():
        """Check if pill recognition system is available."""
        return {
            "available": False,
            "status": "not_installed",
            "message": "Pill recognition modules not installed"
        }
