# main.py
from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, OUTPUT_CSV

def main():
    if not all([EMAIL_USER, EMAIL_PASS]):
        print("Vui lòng cấu hình EMAIL_USER và EMAIL_PASS trong file .env để chạy chức năng này.")
        return

    fetcher = EmailFetcher(
        host=EMAIL_HOST,
        port=EMAIL_PORT,
        user=EMAIL_USER,
        password=EMAIL_PASS
    )
    fetcher.connect()

    processor = CVProcessor(fetcher)
    df = processor.process()
    if not df.empty:
        processor.save_to_csv(df, OUTPUT_CSV)

if __name__ == "__main__":
    main()