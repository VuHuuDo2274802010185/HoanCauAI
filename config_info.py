# config_info.py

import click  # thư viện tạo CLI (Command Line Interface) dễ dùng
from modules.config import LLM_CONFIG  # import cấu hình LLM đã thiết lập sẵn
from modules.model_fetcher import ModelFetcher  # import lớp fetcher để lấy danh sách models

@click.group()  # định nghĩa nhóm lệnh chính cho CLI
def cli():
    """
    Nhóm lệnh CLI để hiển thị thông tin cấu hình và danh sách models.
    """
    pass  # không làm gì, chỉ dùng để group các lệnh con

@cli.command()  # đánh dấu hàm này là một lệnh con của nhóm cli
def info():
    """
    Hiển thị cấu hình hiện tại của LLM:
    - Provider (Google hoặc OpenRouter)
    - Model đang sử dụng
    - Trạng thái API Key (có hoặc không)
    - Số lượng models khả dụng
    """
    # in đường kẻ phân cách
    click.echo("=" * 60)
    # in provider (chữ hoa) để dễ phân biệt
    click.echo(f"Provider:      {LLM_CONFIG['provider'].upper()}")
    # in tên model đang dùng
    click.echo(f"Model:         {LLM_CONFIG['model']}")
    # kiểm tra xem API key có hay không, hiển thị biểu tượng tương ứng
    has_key = "🔑" if LLM_CONFIG.get("api_key") else "❌"
    click.echo(f"API Key:       {has_key}")
    # đếm số models khả dụng, dùng get để tránh lỗi nếu key không tồn tại
    count = len(LLM_CONFIG.get("available_models", []))
    click.echo(f"Models avail.: {count}")
    # in đường kẻ kết thúc
    click.echo("=" * 60)

@cli.command()  # đánh dấu hàm này là lệnh con thứ hai
def list_models():
    """
    Liệt kê chi tiết các models khả dụng từ API của provider hiện tại.
    Model đang chọn sẽ được đánh dấu bằng dấu '*'.
    """
    # đọc provider và api_key từ cấu hình
    provider = LLM_CONFIG.get("provider")
    api_key = LLM_CONFIG.get("api_key")

    # lấy danh sách models tuỳ theo provider
    if provider == "google":
        models = ModelFetcher.get_google_models(api_key)
    else:
        # với OpenRouter, get_openrouter_models trả về list dict, nên lấy 'id'
        models = [m.get("id", "") for m in ModelFetcher.get_openrouter_models(api_key)]

    # in từng model, nếu trùng với model đang dùng thì thêm dấu *
    for m in models:
        mark = " *" if m == LLM_CONFIG.get("model") else ""
        click.echo(f"- {m}{mark}")

# khi chạy file này trực tiếp (không phải import), sẽ gọi lệnh CLI
if __name__ == "__main__":
    cli()  # khởi chạy CLI
