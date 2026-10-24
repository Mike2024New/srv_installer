import asyncio
from ui.root import MainWindowUi
from infrastructure_path_utils import get_root_dir_path
from ui.install_parameters_window import StartWindow
from ui.download_assets_window import DownloadAssets
from ui.extract_archive_window import ExtractFiles
from ui.services_installer_window import ServicesInstallerWindow
from ui.finish_window import FinishWindow
from ui.services_move_window import ServicesMovingWindow
from ui.license_window import LicenseWindow
from config import logger

window_name = 'main'

if __name__ == '__main__':
    event = asyncio.Event()
    temp_dir = get_root_dir_path() / 'temp'
    steps_count_all = 7

    license_window = LicenseWindow(
        target_dir=get_root_dir_path(),
        title=f'Используемые компоненты и лицензии [ 1/{steps_count_all} ]',
    )

    # стартовое окно с выбором опций и параметров
    start_window = StartWindow(
        title=f'Параметры установки [ 2/{steps_count_all} ]',
    )  # устанавливает storage['target_dir'] = folder_path (переменную пути целевой папки установки)

    # окно с загрузкой элементов
    download_assets_window = DownloadAssets(
        target_dir=temp_dir,
        event=event,
        title=f'Загрузка компонентов [ 3/{steps_count_all} ]',
    )

    # окно с распаковкой zip
    extract_files_window = ExtractFiles(
        target_dir=temp_dir,
        event=event,
        title=f'Распаковка компонентов [ 4/{steps_count_all} ]',
    )
    # окно с сборщиком .exe приложений
    services_installer_window = ServicesInstallerWindow(
        target_dir=temp_dir,
        event=event,
        title=f'Сборка компонентов [ 5/{steps_count_all} ]',
    )
    # окно с переносом проекта
    services_moving_window = ServicesMovingWindow(
        root_dir=temp_dir,
        title=f'Перемещение компонентов в целевую директорию [ 6/{steps_count_all} ]',
        event=event,
    )

    # окно с завершением сборки
    finish_window = FinishWindow(
        root_dir=temp_dir,
        title=f'Завершение установки [ 7/{steps_count_all} ]',
    )

    # главное окно
    main_ui = MainWindowUi(
        pages={
            'license_window': license_window.window,
            'start_window': start_window.window,
            'download_assets_window': download_assets_window.window,
            'extract_files_window': extract_files_window.window,
            'services_installer_window': services_installer_window.window,
            'services_moving_window': services_moving_window.window,
            'finish_window': finish_window.window,
        },
        min_width=800, min_height=550, header=True, header_text='srv_installer',
        footer=True, nav_theme_switcher=True,
    )
    # начало с 1 страницы (выбор параметров установки)
    logger.info(f'[ {window_name} ][ START ] окно установщика открыто')

    main_ui.set_page(name='license_window')
    license_window.finish_callback = lambda: main_ui.set_page(name='start_window')
    start_window.finish_callback = lambda: main_ui.set_page(name='download_assets_window')
    download_assets_window.finish_callback = lambda: main_ui.set_page(name='extract_files_window')
    extract_files_window.finish_callback = lambda: main_ui.set_page(name='services_installer_window')
    services_installer_window.finish_callback = lambda: main_ui.set_page(name='services_moving_window')
    services_moving_window.finish_callback = lambda: main_ui.set_page(name='finish_window')
    finish_window.finish_callback = lambda: main_ui.root.destroy()

    # для отладки загрузок
    # main_ui.set_page(name='download_assets_window')
    # download_assets_window.finish_callback = lambda: main_ui.set_page(name='finish_window')

    main_ui.start()
    logger.info(f'[ {window_name} ][ END ] окно установщика закрыто')
