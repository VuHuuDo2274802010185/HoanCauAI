# main_engine/main.py

import os
import sys
# Đưa thư mục gốc vào sys.path để import modules
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# Ensure the `src` directory is on the import path so that `modules` can be
# imported when this script is executed directly.
SRC_DIR = os.path.join(ROOT, "src")
for path in (ROOT, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import click
import logging
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor
from modules.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, OUTPUT_CSV
from modules.dynamic_llm_client import DynamicLLMClient

# Cấu hình logging chung
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

@click.command()
@click.option('--batch/--single', default=True, help="Chế độ batch (email) hoặc single (file)")
@click.argument('file', required=False, type=click.Path())
def main(batch: bool, file):
    """CLI để xử lý CV: batch qua email hoặc đơn file."""
    # Khởi tạo LLM client theo config
    llm_client = DynamicLLMClient()

    if batch:
        # Chạy batch nhưng bỏ qua bước kết nối email/fetch IMAP
        processor = CVProcessor(llm_client=llm_client)
        df = processor.process()
        if not df.empty:
            processor.save_to_csv(df, OUTPUT_CSV)
            click.echo(f"Saved {len(df)} records to {OUTPUT_CSV}")
        else:
            click.echo("Không có CV nào để xử lý.")
    else:
        # Chạy single-file
        if not file:
            click.echo("Vui lòng cung cấp đường dẫn file khi dùng --single")
            return
        processor = CVProcessor(llm_client=llm_client)
        text = processor.extract_text(file)
        info = processor.extract_info_with_llm(text)
        click.echo(info)

if __name__ == "__main__":
    main()
