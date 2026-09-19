import shutil
from pathlib import Path


# копирование компонентов в целевую директорию
def copy_services_to_target_dir(root_dir: Path, temp_dir: Path):
    for svc_dir in temp_dir.iterdir():
        if not svc_dir.is_dir() or not (svc_dir / 'cli.py').exists() or not (svc_dir / 'start.py').exists():
            continue
        target_dir = root_dir / svc_dir.parts[-1]

        if target_dir.exists():
            shutil.rmtree(target_dir)

        target_dir.mkdir(exist_ok=True, parents=True)
        for file in svc_dir.iterdir():
            if file.is_dir() and file.name == 'resources':
                shutil.copytree(
                    src=file,
                    dst=target_dir / 'resources',
                )

            if file.suffix == '.exe':
                shutil.copy2(
                    src=file,
                    dst=target_dir / 'app.exe',
                )

            if file.suffix == '.md' or file.parts[-1] == 'LICENSE' or file.name == 'settings.json':
                shutil.copy2(
                    src=file,
                    dst=target_dir,
                )
