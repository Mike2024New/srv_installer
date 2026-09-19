from infrastructure_builder import build, BuildParameters
from infrastructure_path_utils import get_root_dir_path

root_dir = get_root_dir_path()

parameters = BuildParameters(
    name='installer',
    entry_point_path=root_dir / 'main.py',
    one_file=True,
    create_resources_symlink=False,
    copy_from_dist_to_target_dir=root_dir,
    icon_path=root_dir / 'icon.ico',
    delete_releases_folder=True,
)
if __name__ == '__main__':
    build(parameters)
