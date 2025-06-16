# main_engine/config_info.py

import os
import sys
# Đưa thư mục gốc (chứa `modules/`) vào sys.path
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import click                               # CLI framework
from modules.config import LLM_CONFIG       # cấu hình LLM
from modules.model_fetcher import ModelFetcher  # fetch list models

@click.group()
def cli():
    """Nhóm lệnh CLI xem cấu hình và models."""
    pass

@cli.command()
def info():
    """Hiển thị cấu hình LLM hiện tại."""
    click.echo("="*60)
    click.echo(f"Provider:      {LLM_CONFIG['provider'].upper()}")
    click.echo(f"Model:         {LLM_CONFIG['model']}")
    key_status = "OK" if LLM_CONFIG.get("api_key") else "Không"
    click.echo(f"API Key set:   {key_status}")
    count = len(LLM_CONFIG.get("available_models", []))
    click.echo(f"Models avail.: {count}")
    click.echo("="*60)

@cli.command('list-models')
def list_models():
    """Liệt kê chi tiết các models khả dụng."""
    provider = LLM_CONFIG["provider"]
    api_key = LLM_CONFIG.get("api_key")
    if provider == "google":
        models = ModelFetcher.get_google_models(api_key)
    else:
        # OpenRouter trả về list dict
        models = [m.get("id","") for m in ModelFetcher.get_openrouter_models(api_key)]

    for m in models:
        mark = "*" if m == LLM_CONFIG["model"] else " "
        click.echo(f"{mark} {m}")

if __name__ == "__main__":
    cli()
