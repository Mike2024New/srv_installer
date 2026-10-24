"""
Автообновление хешей репозиториев в settings.json перед сборкой.
Запускается один раз перед сборкой релиза.
"""
import json
import subprocess
from pathlib import Path


def get_latest_sha(repo_url: str, branch: str = 'main') -> str:
    result = subprocess.run(
        ['git', 'ls-remote', repo_url, branch],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.split()[0]


def update_settings(settings_path: Path, branch: str = 'main'):
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    for i, repo in enumerate(settings['repos']):
        sha = get_latest_sha(repo['url'], branch=branch)
        settings['repos'][i]['hash'] = sha

    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    update_settings(Path(__file__).parent / 'settings.json')
