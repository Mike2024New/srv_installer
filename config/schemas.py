from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = 'app'
    main_srv_dirname: str | None = None
    app_files: list[str]
    assets: list[dict[str, str | bool]]


default_settings = Settings(app_files=[], assets=[])

if __name__ == '__main__':
    print(default_settings.assets)
