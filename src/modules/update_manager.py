# modules/update_manager.py

import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class UpdateManager:
    """
    Quản lý cập nhật và rollback cho ứng dụng HoanCau AI
    """
    
    def __init__(self, app_root: Path = None):
        self.app_root = app_root or Path(__file__).parent.parent
        self.backup_dir = self.app_root / "backups"
        self.version_file = self.app_root / "version.json"
        self.config_dir = self.app_root / "config"
        
        # Tạo thư mục cần thiết
        self.backup_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # URL repository (có thể thay đổi)
        self.repo_url = "https://api.github.com/repos/your-username/HoanCauAI"
        self.download_url = "https://github.com/your-username/HoanCauAI/archive/refs/heads/main.zip"
        
    def get_current_version(self) -> Dict:
        """Lấy thông tin phiên bản hiện tại"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Không thể đọc version.json: {e}")
        
        # Default version nếu không có file
        return {
            "version": "1.0.0",
            "build": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "updated_at": datetime.now().isoformat(),
            "features": ["Thanh tiến trình trực quan", "Email fetcher", "CV processor"]
        }
    
    def save_version_info(self, version_info: Dict):
        """Lưu thông tin phiên bản"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)
            logger.info(f"Đã lưu thông tin phiên bản: {version_info['version']}")
        except Exception as e:
            logger.error(f"Lỗi lưu version.json: {e}")
    
    def check_for_updates(self) -> Tuple[bool, Dict]:
        """Kiểm tra cập nhật mới từ repository"""
        try:
            # Kiểm tra commit mới nhất từ GitHub API
            response = requests.get(f"{self.repo_url}/commits/main", timeout=10)
            if response.status_code == 200:
                latest_commit = response.json()
                current_version = self.get_current_version()
                
                latest_info = {
                    "version": f"1.0.{latest_commit['sha'][:8]}",
                    "commit_sha": latest_commit['sha'],
                    "commit_date": latest_commit['commit']['committer']['date'],
                    "message": latest_commit['commit']['message'],
                    "author": latest_commit['commit']['author']['name']
                }
                
                # So sánh với phiên bản hiện tại
                is_newer = latest_info['commit_sha'] != current_version.get('commit_sha', '')
                
                return is_newer, latest_info
            else:
                logger.warning(f"Không thể kiểm tra cập nhật: HTTP {response.status_code}")
                return False, {}
                
        except requests.RequestException as e:
            logger.warning(f"Lỗi kết nối khi kiểm tra cập nhật: {e}")
            return False, {}
        except Exception as e:
            logger.error(f"Lỗi kiểm tra cập nhật: {e}")
            return False, {}
    
    def create_backup(self, backup_name: str = None) -> Path:
        """Tạo backup của phiên bản hiện tại"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Danh sách thư mục/file quan trọng cần backup
        important_items = [
            "src", 
            "scripts", 
            "requirements.txt", 
            "requirements-dev.txt",
            "setup_linux.sh",
            "setup_window.cmd", 
            "start_linux.sh",
            "start_window.cmd",
            "pyproject.toml",
            "version.json",
            ".env.example"
        ]
        
        logger.info(f"Tạo backup tại: {backup_path}")
        
        for item_name in important_items:
            item_path = self.app_root / item_name
            if item_path.exists():
                if item_path.is_file():
                    shutil.copy2(item_path, backup_path / item_name)
                else:
                    shutil.copytree(item_path, backup_path / item_name, dirs_exist_ok=True)
                logger.debug(f"Đã backup: {item_name}")
        
        # Lưu thông tin backup
        backup_info = {
            "created_at": datetime.now().isoformat(),
            "version": self.get_current_version(),
            "backup_name": backup_name
        }
        
        with open(backup_path / "backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Backup hoàn thành: {backup_path}")
        return backup_path
    
    def download_update(self, progress_callback=None) -> Path:
        """Tải xuống phiên bản mới"""
        logger.info("Bắt đầu tải xuống cập nhật...")
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = downloaded / total_size
                        progress_callback(downloaded, total_size, f"Đã tải: {downloaded//1024} KB / {total_size//1024} KB")
            
            tmp_file.flush()
            logger.info(f"Đã tải xuống: {tmp_file.name}")
            return Path(tmp_file.name)
    
    def apply_update(self, update_zip: Path, progress_callback=None) -> bool:
        """Áp dụng cập nhật từ file zip"""
        try:
            # Giải nén vào thư mục tạm
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                if progress_callback:
                    progress_callback(0, 100, "Giải nén cập nhật...")
                
                with zipfile.ZipFile(update_zip, 'r') as zip_ref:
                    zip_ref.extractall(temp_path)
                
                # Tìm thư mục gốc trong zip (thường là HoanCauAI-main)
                extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if not extracted_dirs:
                    raise Exception("Không tìm thấy thư mục trong file zip")
                
                source_dir = extracted_dirs[0]
                
                if progress_callback:
                    progress_callback(30, 100, "Sao chép file mới...")
                
                # Sao chép file mới (trừ .env để giữ cấu hình)
                important_items = [
                    "src", 
                    "scripts", 
                    "requirements.txt", 
                    "requirements-dev.txt",
                    "setup_linux.sh",
                    "setup_window.cmd", 
                    "start_linux.sh",
                    "start_window.cmd",
                    "pyproject.toml"
                ]
                
                for i, item_name in enumerate(important_items):
                    source_item = source_dir / item_name
                    target_item = self.app_root / item_name
                    
                    if source_item.exists():
                        if target_item.exists():
                            if target_item.is_file():
                                target_item.unlink()
                            else:
                                shutil.rmtree(target_item)
                        
                        if source_item.is_file():
                            shutil.copy2(source_item, target_item)
                        else:
                            shutil.copytree(source_item, target_item)
                        
                        logger.debug(f"Đã cập nhật: {item_name}")
                    
                    if progress_callback:
                        progress = 30 + (i + 1) / len(important_items) * 60
                        progress_callback(int(progress), 100, f"Cập nhật: {item_name}")
                
                if progress_callback:
                    progress_callback(90, 100, "Hoàn thiện cập nhật...")
                
                # Cập nhật thông tin phiên bản
                new_version = {
                    "version": f"1.0.{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "updated_at": datetime.now().isoformat(),
                    "features": ["Thanh tiến trình trực quan", "Email fetcher", "CV processor", "Auto update system"]
                }
                self.save_version_info(new_version)
                
                if progress_callback:
                    progress_callback(100, 100, "✅ Cập nhật hoàn thành!")
                
                logger.info("✅ Cập nhật ứng dụng thành công!")
                return True
                
        except Exception as e:
            logger.error(f"Lỗi áp dụng cập nhật: {e}")
            return False
        finally:
            # Xóa file zip tạm
            try:
                update_zip.unlink()
            except:
                pass
    
    def revert_to_backup(self, backup_name: str, progress_callback=None) -> bool:
        """Khôi phục từ backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Không tìm thấy backup: {backup_name}")
            return False
        
        try:
            if progress_callback:
                progress_callback(0, 100, f"Bắt đầu khôi phục từ {backup_name}...")
            
            # Đọc thông tin backup
            backup_info_file = backup_path / "backup_info.json"
            if backup_info_file.exists():
                with open(backup_info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                logger.info(f"Khôi phục phiên bản: {backup_info.get('version', 'unknown')}")
            
            # Khôi phục file
            items = list(backup_path.iterdir())
            for i, item in enumerate(items):
                if item.name == "backup_info.json":
                    continue
                
                target_item = self.app_root / item.name
                
                # Xóa file/thư mục hiện tại
                if target_item.exists():
                    if target_item.is_file():
                        target_item.unlink()
                    else:
                        shutil.rmtree(target_item)
                
                # Khôi phục từ backup
                if item.is_file():
                    shutil.copy2(item, target_item)
                else:
                    shutil.copytree(item, target_item)
                
                if progress_callback:
                    progress = (i + 1) / len(items) * 90
                    progress_callback(int(progress), 100, f"Khôi phục: {item.name}")
            
            if progress_callback:
                progress_callback(100, 100, "✅ Khôi phục hoàn thành!")
            
            logger.info(f"✅ Khôi phục thành công từ backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khôi phục backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Liệt kê tất cả backup có sẵn"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                backup_info_file = backup_dir / "backup_info.json"
                
                if backup_info_file.exists():
                    try:
                        with open(backup_info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                        backups.append({
                            "name": backup_dir.name,
                            "created_at": info.get("created_at", "unknown"),
                            "version": info.get("version", {}),
                            "size": self._get_dir_size(backup_dir)
                        })
                    except Exception as e:
                        logger.warning(f"Không thể đọc backup info: {backup_dir.name}: {e}")
                else:
                    # Backup cũ không có info file
                    backups.append({
                        "name": backup_dir.name,
                        "created_at": datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                        "version": {"version": "unknown"},
                        "size": self._get_dir_size(backup_dir)
                    })
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def _get_dir_size(self, path: Path) -> str:
        """Tính kích thước thư mục"""
        try:
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024**2:
                return f"{total_size/1024:.1f} KB"
            else:
                return f"{total_size/(1024**2):.1f} MB"
        except:
            return "unknown"
    
    def delete_backup(self, backup_name: str) -> bool:
        """Xóa backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return False
        
        try:
            shutil.rmtree(backup_path)
            logger.info(f"Đã xóa backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Lỗi xóa backup {backup_name}: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """Dọn dẹp backup cũ, chỉ giữ lại số lượng nhất định"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        deleted_count = 0
        for backup in backups[keep_count:]:
            if self.delete_backup(backup["name"]):
                deleted_count += 1
        
        logger.info(f"Đã dọn dẹp {deleted_count} backup cũ")
        return deleted_count
