import asyncio, os, sys, tarfile
from pathlib import Path
from infrastructure_http_clients import file_downloader
from functools import partial
from functions import console_spinner_progress_bar, TaskForSpinner, get_download_type
from config import settings


def extract_tar(path: Path, target_dir: Path):
    with tarfile.open(path, 'r:gz') as tar:
        # распаковать всё в папку (filter можно установ ключи безопаности для подозрительных путей)
        tar.extractall(path=target_dir, filter='data')


async def ensure_python(target_dir: Path) -> Path:
    download = get_download_type(settings.ensure_python_url, target_dir=target_dir)

    portable_python = target_dir / 'python' / 'python.exe'
    if portable_python.exists():
        return portable_python

    # загрузка python
    python_tar_gz = download.target_dir / download.filename
    if not python_tar_gz.exists():
        await file_downloader(download_list=[download])
    # извлечение python
    sync_task = asyncio.create_task(
        asyncio.to_thread(
            partial(
                extract_tar, path=python_tar_gz, target_dir=target_dir
            )
        )
    )
    progress_task = asyncio.create_task(
        console_spinner_progress_bar(
            tasks=[TaskForSpinner(task=sync_task, text='распаковка python')]
        )
    )
    await sync_task
    await progress_task
    # удаление python zip
    os.remove(python_tar_gz)
    portable_python = target_dir / 'python' / 'python.exe'
    if not portable_python.exists():
        print(
            f'[red]Не удалось установить портативный python, установите python с python.org, или с помощью магазина приложений.[/red]'
        )
        sys.exit()
    return portable_python
