# main.py
from modules.cv_processor import CVProcessor
from modules.email_fetcher import EmailFetcher
from modules.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, OUTPUT_EXCEL


def main():
    fetcher = EmailFetcher(
        host=EMAIL_HOST,
        port=EMAIL_PORT,
        user=EMAIL_USER,
        password=EMAIL_PASS
    )
    fetcher.connect()

    processor = CVProcessor(fetcher)
    df = processor.process()
    processor.save_to_excel(df, OUTPUT_EXCEL)


if __name__ == "__main__":
    main()
