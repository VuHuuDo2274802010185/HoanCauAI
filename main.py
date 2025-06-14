import click
import logging
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor
from modules.config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, OUTPUT_CSV, LLM_CONFIG
from modules.dynamic_llm_client import DynamicLLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

@click.command()
@click.option('--batch/--single', default=True, help="Batch (email) or single file mode")
@click.argument('file', required=False, type=click.Path(exists=True))
def main(batch: bool, file):
    """CLI to process CVs."""
    if batch:
        if not EMAIL_USER or not EMAIL_PASS:
            click.echo("EMAIL_USER and EMAIL_PASS must be set in .env")
            return
        fetcher = EmailFetcher(EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS)
        fetcher.connect()
        processor = CVProcessor(fetcher)
        processor.llm_client = DynamicLLMClient(LLM_CONFIG['provider'], LLM_CONFIG['model'])
        df = processor.process()
        if not df.empty:
            processor.save_to_csv(df, OUTPUT_CSV)
            click.echo(f"Saved {len(df)} records to {OUTPUT_CSV}")
        else:
            click.echo("No CVs to process.")
    else:
        if not file:
            click.echo("Provide file path for single mode.")
            return
        processor = CVProcessor()
        processor.llm_client = DynamicLLMClient(LLM_CONFIG['provider'], LLM_CONFIG['model'])
        text = processor.extract_text(file)
        info = processor.extract_info_with_llm(text)
        click.echo(info)

if __name__ == "__main__":
    main()