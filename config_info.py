import click
from modules.config import LLM_CONFIG
from modules.model_fetcher import ModelFetcher

@click.group()
def cli():
    """CLI to display LLM config and models."""
    pass

@cli.command()
def info():
    """Show current LLM configuration."""
    click.echo("="*60)
    click.echo(f"Provider: {LLM_CONFIG['provider'].upper()}")
    click.echo(f"Model:    {LLM_CONFIG['model']}")
    click.echo(f"API Key:  {'🔑' if LLM_CONFIG['api_key'] else '❌'}")
    click.echo(f"Models avail: {len(LLM_CONFIG.get('available_models', []))}")
    click.echo("="*60)

@cli.command()
def list_models():
    """List available models from API."""
    prov = LLM_CONFIG['provider']
    key = LLM_CONFIG['api_key']
    if prov == 'google':
        models = ModelFetcher.get_google_models(key)
    else:
        models = [m['id'] for m in ModelFetcher.get_openrouter_models(key)]
    for m in models:
        mark = ' *' if m == LLM_CONFIG['model'] else ''
        click.echo(f"- {m}{mark}")

if __name__ == "__main__":
    cli()