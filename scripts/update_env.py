# -*- coding: utf-8 -*-
# Tiện ích cập nhật file .env thông qua dòng lệnh

import os  # Thao tác hệ thống tệp và biến môi trường
import shutil  # Hỗ trợ sao chép tệp
import click  # Thư viện tạo CLI
from dotenv import load_dotenv, set_key, get_key  # Làm việc với file .env

# Định nghĩa lệnh CLI sử dụng Click
@click.command()
@click.option('--env-file', default='.env', help='Đường dẫn tới file .env')
@click.option('--create-from-example', is_flag=True,
              help='Tạo file .env từ .env.example nếu chưa tồn tại')
@click.option('--set', 'kv_pairs', multiple=True,
              help='Cặp KEY=VALUE để thiết lập (có thể lặp lại)')
def main(env_file, create_from_example, kv_pairs):
    """Cập nhật file .env dựa trên input người dùng."""
    # Tạo file nếu chưa có
    if not os.path.exists(env_file):
        if create_from_example and os.path.exists('.env.example'):
            shutil.copy('.env.example', env_file)  # copy từ template
            click.echo(f'Đã tạo {env_file} từ .env.example')
        else:
            open(env_file, 'a').close()  # tạo file trống
            click.echo(f'Đã tạo file trống {env_file}')

    # Nạp biến môi trường hiện có
    load_dotenv(env_file)

    updates = {}  # Dict lưu các cập nhật
    for pair in kv_pairs:
        if '=' not in pair:
            raise click.BadParameter('--set phải theo dạng KEY=VALUE')
        key, value = pair.split('=', 1)
        updates[key.strip()] = value

    # Nếu không truyền tham số --set thì hỏi từng biến
    if not updates:
        click.echo('Nhập tên biến trống để kết thúc.')
        while True:
            key = click.prompt('Biến', default='', show_default=False)
            if not key:
                break
            default = os.getenv(key) or get_key(env_file, key) or ''
            value = click.prompt('Giá trị', default=default, show_default=bool(default))
            updates[key] = value

    # Ghi các giá trị vào file .env
    for key, value in updates.items():
        set_key(env_file, key, value)
        click.echo(f'Đã đặt {key}')

    click.echo('Hoàn tất cập nhật môi trường.')

# Entry point khi chạy trực tiếp
if __name__ == '__main__':
    main()
