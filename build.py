from infrastructure_builder import build, BuildParameters
from infrastructure_path_utils import get_root_dir_path, create_zip_func
from git_updater import update_settings

root_dir = get_root_dir_path()

parameters = BuildParameters(
    name='app',
    entry_point_path=root_dir / 'main.py',
    one_file=False,
    create_resources_symlink=False,
    copy_from_dist_to_target_dir=root_dir,
    icon_path=root_dir / 'icon.ico',
    delete_releases_folder=True,
    console=False,
    copy_dirs=[
        (root_dir / 'themes', 'app/themes'),
        (root_dir / 'LICENSES', 'app/LICENSES'),
    ],
    copy_files=[
        (root_dir / 'settings.json', 'app/settings.json'),
    ]
)
if __name__ == '__main__':
    user_input = input(f'Обновить hash комитов репозитория?(y/n): ')
    if user_input == 'y':
        print('обновление хешей репозитория')
        update_settings(settings_path=root_dir / 'settings.json')
    print('сборка билда')
    build(parameters)
    print('сборка zip')
    create_zip_func(
        source_dir=root_dir / 'app',  # например сборка приложения app
        target_zip=root_dir / 'win_x86_64.zip',  # выходной архив
        archive_root_folder_name=None,  # чтобы внутри не создавалась папка
    )
