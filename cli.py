from infrastructure_cli_utils import get_cli_app, CliSettings
from infrastructure_path_utils import get_root_dir_path
from build import parameters

cli_settings = CliSettings(
    enable_run_command=True,
    enable_git_push=True,
    enable_build_command=True,
)
app = get_cli_app(
    name='installer',
    root_dir=get_root_dir_path(),
    cli_settings=cli_settings,
    build_settings=parameters,
)

# для быстрых коммитов на git, и сборки `python cli.py`
if __name__ == '__main__':
    app()
