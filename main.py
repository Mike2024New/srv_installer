import sys
import asyncio, shutil
from core import ensure_python
from core import ensure_git
from core import download_services
from core import extract_services
from core import project_builder
from core import copy_services_to_target_dir
from infrastructure_path_utils import get_root_dir_path

# для разработки поместить файлы во временную папку (чтобы не пересекаться с текущим кодом)
exe_mode = getattr(sys, 'frozen', False)
root_dir = get_root_dir_path() if exe_mode else get_root_dir_path() / 'sandbox'
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
    shutil.rmtree('\\\\?\\' + str(temp_dir))
    print(f'[8/8] Инициализация приложения')
    # поиск папки сервиса
    for file in root_dir.iterdir():
        if not file.is_dir():
            continue
        if file.name.startswith('app_'):
            shutil.copytree(
                src=file,
                dst=root_dir,  # приложение распаковывается в корень
                dirs_exist_ok=True,
            )
            try:
                shutil.rmtree('\\\\?\\' + str(file))
            except Exception:  # noqa
                pass


if __name__ == '__main__':
    asyncio.run(start())
