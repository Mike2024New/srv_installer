from pathlib import Path

from config import settings
from functions import get_download_type_for_git_repo
from infrastructure_http_clients import file_downloader

async def download_services(target_dir: Path):
    """Загрузка подчиненных сервисов"""
    downloads_list = []
    for url in settings.repositories_url:
        download_svc = get_download_type_for_git_repo(url=url, target_dir=target_dir)
        downloads_list.append(download_svc)
    await file_downloader(download_list=downloads_list, timeout=3, attempts=3)
