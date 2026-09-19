import sys
import asyncio, shutil
from core import ensure_python
from core import ensure_git
from core import download_services
from core import extract_services
from core import project_builder
from core import copy_services_to_target_dir
from infrastructure_path_utils import get_root_dir_path
from config import settings

exe_mode = getattr(sys, 'frozen', False)
root_dir = get_root_dir_path()
temp_dir = root_dir / 'temp'


async def start():
    print(f'[1/8] Проверка/загрузка python')
    python_portable = await ensure_python(target_dir=temp_dir / 'python')
    print(f'[2/8] Проверка/загрузка git_portable')
    await ensure_git(target_dir=temp_dir / 'MinGit')
    print(f'[3/8] Загрузка компонентов приложения')
    await download_services(target_dir=temp_dir)
    print(f'[4/8] Распаковка компонентов приложения')
    extract_services(root_dir=temp_dir, temp_dir=temp_dir)
    print(f'[5/8] Сборка компонентов приложения')
    await project_builder(target_dir=temp_dir, python_portable=python_portable)
    print(f'[6/8] Перенос компонентов')
    copy_services_to_target_dir(root_dir=root_dir, temp_dir=temp_dir)
    print(f'[7/8] Очистка директории от временных файлов')
    shutil.rmtree(temp_dir)
    print(f'[8/8] Инициализация приложения')
    # чтобы не повредить текущий проект случайно
    if not exe_mode:
        shutil.copytree(
            src=root_dir / settings.app_repo_name,
            dst=root_dir,  # приложение распаковывается в корень
            dirs_exist_ok=True,
        )
        shutil.rmtree(root_dir / settings.app_repo_name)


if __name__ == '__main__':
    asyncio.run(start())
