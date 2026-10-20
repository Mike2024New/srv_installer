import shutil
import threading
from pathlib import Path
import queue
from queue import Queue
from config import settings, logger

window_name = 'services_move'


def services_move(root_dir: Path, target_dir: Path, queue_report: Queue) -> None:
    """
    Перенос сервисов в целевую папку
    """
    target_dir = target_dir / settings.app_name
    if not target_dir.exists():
        target_dir.mkdir(exist_ok=True, parents=True)

    try:
        for file in root_dir.rglob('*'):
            if '.venv' in file.parts or 'utils' in file.parts:
                continue

            exe_dir = file / 'app'  # это именно директория !
            license_path = file / 'LICENSE'
            readme_md_path = file / 'README.md'
            settings_json = file / 'settings.json'

            # проверка что это сервис по критериям
            if exe_dir.exists() and license_path.exists() and readme_md_path.exists():
                logger.info(f'[ {window_name} ] перенос сервиса {file.parts[-1]} в целевую папку')
                queue_report.put_nowait(f'Перенос сервиса {file.parts[-1]} в целевую папку')
                new_app_dir = target_dir / file.parts[-1]

                if not new_app_dir.exists():
                    new_app_dir.mkdir(exist_ok=True, parents=True)

                # перенос папки с приложением
                if new_app_dir.exists():
                    shutil.rmtree('\\\\?\\' + str(new_app_dir))
                shutil.copytree('\\\\?\\' + str(exe_dir), '\\\\?\\' + str(new_app_dir))

                # перенос файлов с лицензиями и readme
                shutil.copy2('\\\\?\\' + str(license_path), '\\\\?\\' + str(new_app_dir / license_path.name))
                shutil.copy2('\\\\?\\' + str(readme_md_path), '\\\\?\\' + str(new_app_dir / readme_md_path.name))

                if settings_json.exists():
                    shutil.copy2('\\\\?\\' + str(settings_json), '\\\\?\\' + str(new_app_dir / settings_json.name))

                # перенос иконки если она есть
                icon_path = file / 'icon.ico'
                if icon_path.exists():
                    shutil.copy2('\\\\?\\' + str(icon_path), '\\\\?\\' + str(new_app_dir / icon_path.name))

                # папка с ресурсами (например с моделями)
                resources_dir = file / 'resources'
                if resources_dir.exists():
                    target_resources = new_app_dir / 'resources'
                    if target_resources.exists():
                        shutil.rmtree('\\\\?\\' + str(target_resources))
                    shutil.copytree('\\\\?\\' + str(resources_dir), '\\\\?\\' + str(target_resources))

                # папка с блоком лицензий (когда несколько лицензий в папке)
                licenses_dir = file / 'LICENSES'
                if licenses_dir.exists():
                    target_licenses = new_app_dir / 'LICENSES'
                    if target_licenses.exists():
                        shutil.rmtree('\\\\?\\' + str(target_licenses))
                    shutil.copytree('\\\\?\\' + str(licenses_dir), '\\\\?\\' + str(target_licenses))

                # папка с темами для ui
                themes_dir = file / 'themes'
                if themes_dir.exists():
                    target_themes = new_app_dir / 'themes'
                    if target_themes.exists():
                        shutil.rmtree('\\\\?\\' + str(target_themes))
                    shutil.copytree('\\\\?\\' + str(themes_dir), '\\\\?\\' + str(target_themes))


    except Exception as err:  # потом сделать более детальную обработку
        logger.exception(f'[ {window_name} ] {err}')
    finally:
        queue_report.put_nowait(None)


if __name__ == '__main__':
    from infrastructure_path_utils import get_root_dir_path


    def observer(queue_rp: Queue):
        while True:
            try:
                res = queue_rp.get(timeout=0.4)
                if res is None:
                    return
                print(res)
            except queue.Empty:
                pass


    queue_rep = Queue()
    threading.Thread(target=lambda: observer(queue_rp=queue_rep)).start()
    services_move(
        root_dir=get_root_dir_path() / 'temp',
        target_dir=Path(r'C:\Users\projects\Desktop\target_dir'),
        queue_report=queue_rep,
    )
