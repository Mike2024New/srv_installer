from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = 'app'
    download_attempts: int = 10
    download_attempts_interval_sec: float = 5
    download_retries: int = 10
    download_retries_timeout: float = 5
    main_srv_dirname: str | None = None
    app_files: list[str]
    assets: list[dict[str, str | bool]]


default_settings = Settings(app_files=[], assets=[])

if __name__ == '__main__':
    print(default_settings)
