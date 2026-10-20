from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from config.schemas import default_settings
from infrastructure_log_utils import Logger
import uuid

__all__ = ['settings', 'settings_manager', 'logger']

logger = Logger(
    log_path=get_root_dir_path() / 'logs/app.log',
    rotation='10 MB', retention=10,
    compression='zip',
    fmt='{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[request_id]} | {message}'
)
logger.set_logger(request_id=str(uuid.uuid4())[:4])

settings_manager = get_settings_manager(
    json_file_path=get_root_dir_path() / 'settings.json',
    settings_model=default_settings,
)

settings = settings_manager.settings
