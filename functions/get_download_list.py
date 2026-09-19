from pathlib import Path
from infrastructure_http_clients import DownloadFileType


def get_download_type_for_git_repo(url: str, target_dir: Path):
    """Создание объекта для загрузки репозиториев с гит"""
    return DownloadFileType(
        url_list=[f'{url}/archive/refs/heads/main.zip'],
        target_dir=target_dir / f'{url.split('/')[-1]}',
        filename=f'{url.split('/')[-1]}.zip',
        replace=False,
    )


def get_download_type(url: str, target_dir: Path):
    """Прочие объекты"""
    return DownloadFileType(
        url_list=[url],
        target_dir=target_dir,
        filename=f'{url.split('/')[-1]}',
        replace=False,
    )
