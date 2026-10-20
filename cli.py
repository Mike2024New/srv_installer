import sys
from infrastructure_cli_utils import get_cli_app, CliSettings
from infrastructure_path_utils import get_root_dir_path
from config import settings

app = get_cli_app(
    exe_mode=getattr(sys, 'frozen', False),
    name=settings.app_name,
    root_dir=get_root_dir_path(),
    cli_settings=CliSettings(enable_git_push=True),
)

if __name__ == '__main__':
    app()
