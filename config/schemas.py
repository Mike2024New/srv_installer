from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_repo_name: str = Field(default='')
    repositories_url: list[str] = Field(default_factory=list)
    ensure_python_url: str = 'https://github.com/astral-sh/python-build-standalone/releases/download/20260825/cpython-3.12.14+20260825-x86_64-pc-windows-msvc-install_only.tar.gz'
    ensure_git_url: str = 'https://github.com/git-for-windows/git/releases/download/v2.54.0.windows.1/MinGit-2.54.0-64-bit.zip'
