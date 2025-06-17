import os
import threading
import click
import pandas as pd
import uvicorn

from modules.auto_fetcher import watch_loop
from modules.email_fetcher import EmailFetcher
from modules.cv_processor import CVProcessor
from modules.qa_chatbot import answer_question
from modules.mcp_server import settings

@click.group()
def cli():
    """Hoàn Cầu AI Agent CLI"""
    pass

@cli.command()
@click.option('--interval', default=600, show_default=True, help='Khoảng thời gian giữa các lần fetch (giây)')
@click.option('--host', default=lambda: settings.email_host, help='IMAP host')
@click.option('--port', default=lambda: settings.email_port, type=int, help='IMAP port')
@click.option('--user', default=lambda: settings.email_user, help='Email user')
@click.option('--password', default=lambda: settings.email_pass, help='Email password')
def watch(interval, host, port, user, password):
    """Tự động fetch CV từ email liên tục"""
    click.echo(f"Bắt đầu auto fetch với interval={interval}s...")
    watch_loop(interval, host=host, port=port, user=user, password=password)

@cli.command()
def full_process():
    """Chạy đầy đủ quy trình fetch và xử lý CV"""
    click.echo("Bắt đầu full process...")
    # Fetch email
    fetcher = EmailFetcher(settings.email_host, settings.email_port, settings.email_user, settings.email_pass)
    fetcher.connect()
    fetcher.fetch_cv_attachments()
    # Process CVs
    processor = CVProcessor(fetcher)
    df = processor.process()
    if df.empty:
        click.echo("Không có CV mới để xử lý.")
    else:
        processor.save_to_csv(df, str(settings.output_csv))
        click.echo(f"Đã xử lý {len(df)} CV và lưu vào {settings.output_csv}")

@cli.command()
@click.argument('file', type=click.Path(exists=True))
def single(file):
    """Xử lý một file CV đơn lẻ"""
    click.echo(f"Xử lý file: {file}")
    processor = CVProcessor()
    text = processor.extract_text(file)
    info = processor.extract_info_with_llm(text)
    click.echo(info)

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host để chạy server')
@click.option('--port', default=8000, type=int, help='Port để chạy server')
def serve(host, port):
    """Chạy FastAPI MCP server"""
    click.echo(f"Chạy MCP server tại http://{host}:{port}")
    uvicorn.run('modules.mcp_server:app', host=host, port=port, reload=True)

@cli.command()
@click.argument('question')
def chat(question):
    """Hỏi AI dựa trên kết quả CSV"""
    if not settings.output_csv.exists():
        click.echo("File kết quả không tồn tại, hãy chạy full_process trước.")
        return
    df = pd.read_csv(settings.output_csv)
    # Chọn provider và model từ env hoặc default
    provider = os.getenv('LLM_PROVIDER', 'google')
    model = os.getenv('LLM_MODEL', '')
    api_key = os.getenv('LLM_API_KEY', '')
    answer = answer_question(question, df, provider, model, api_key)
    click.echo(answer)

if __name__ == '__main__':
    cli()
