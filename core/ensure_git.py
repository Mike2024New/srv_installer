import zipfile, os, subprocess
from infrastructure_http_clients import file_downloader
from functions.get_download_list import get_download_type
from config import settings
from pathlib import Path


async def ensure_git(target_dir: Path):
    """Проверка гит, если нет то скачать portable, и на время скрипта прописать его в окружении"""
    try:
        answer = subprocess.run(['git', '--version'], capture_output=True)
        # проверить, есть ли гит в системе
        if answer.returncode == 0:
            return
    except Exception:  # noqa
        pass

    download = get_download_type(url=settings.ensure_git_url, target_dir=target_dir)
    git_path = download.target_dir / download.filename
    git_dir = git_path.parent

    # скачать git_portable
    if not git_dir.exists():
        await file_downloader(download_list=[download], timeout=3, attempts=3)
        with zipfile.ZipFile(git_path, 'r') as zip_ref:
            zip_ref.extractall(git_dir)
        # удалить zip файл с гитом
        os.remove(git_path)

    # прописать git_portable в переменных средах на время выполнения скрипта
    os.environ["PATH"] = os.path.join(git_dir, "cmd") + os.path.pathsep + os.environ["PATH"]
    # проверка что git удаось поставить
    cmd = ['git', '--version']
    res = subprocess.run(cmd, check=False, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f'На машине нет git, а также не удалось скачать портативную версию git.')
