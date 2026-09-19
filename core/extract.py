import zipfile, shutil
from pathlib import Path


def extract_services(root_dir: Path, temp_dir: Path):
    # распаковка и перемещение директории
    delete_folders = []
    for file in temp_dir.rglob('*.zip'):
        folder_name = file.parent.parts[-1]
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(file.parent)
        extracted_folders = [p for p in file.parent.iterdir() if p.is_dir()]
        if not extracted_folders:
            raise RuntimeError("В архиве нет папок")

        source_folder = extracted_folders[0]
        delete_folders.append(file.parent)
        target_dir = root_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        # перенос папок в целевую директорию
        for item in source_folder.iterdir():
            shutil.move(str(item), str(target_dir / item.name))
