import os
import shutil
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseSettings

from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher

class Settings(BaseSettings):
    email_host: str
    email_port: int
    email_user: str
    email_pass: str
    attachment_dir: Path
    output_csv: Path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
# Ensure attachment directory exists
settings.attachment_dir.mkdir(exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

app = FastAPI(title="CV AI MCP Server", version="1.0")

@app.get("/", summary="Health Check")
async def health():
    return {"status": "ok"}

@app.post("/run-full-process", summary="Run full CV extraction process")
async def run_full():
    if not settings.email_user or not settings.email_pass:
        raise HTTPException(status_code=400, detail="Email credentials not set")
    fetcher = EmailFetcher(
        settings.email_host, settings.email_port,
        settings.email_user, settings.email_pass
    )
    fetcher.connect()
    processor = CVProcessor(fetcher)
    df = processor.process()
    if df.empty:
        return {"processed": 0}
    processor.save_to_csv(df, str(settings.output_csv))
    return {"processed": len(df)}

@app.post("/process-single-cv", summary="Process single CV file")
async def process_single_cv(file: UploadFile = File(...)):
    tmp = settings.attachment_dir / f"tmp_{file.filename}"
    with tmp.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)
    processor = CVProcessor()
    text = processor.extract_text(str(tmp))
    tmp.unlink()
    if not text:
        raise HTTPException(status_code=400, detail="Cannot extract text from file")
    return processor.extract_info_with_llm(text)

@app.get("/results", summary="Get processed results CSV")
async def get_results():
    if not settings.output_csv.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    return FileResponse(
        path=str(settings.output_csv),
        media_type="text/csv",
        filename=settings.output_csv.name
    )