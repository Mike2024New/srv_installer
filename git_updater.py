"""
Автообновление хешей репозиториев в settings.json перед сборкой.
Запускается один раз перед сборкой релиза.
"""
import json
import subprocess
from pathlib import Path

# Репозитории, которые нужно обновить
REPOS = {
    'app_ai_assistant': 'https://github.com/Mike2024New/app_ai_assistant',
    'srv_stt': 'https://github.com/Mike2024New/srv_stt',
    'srv_tts': 'https://github.com/Mike2024New/srv_tts',
    'srv_llm': 'https://github.com/Mike2024New/srv_llm',
}


def get_latest_sha(repo_url: str, branch: str = 'main') -> str:
    result = subprocess.run(
        ['git', 'ls-remote', repo_url, branch],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.split()[0]


def update_settings(settings_path: Path, branch: str = 'main'):
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    for asset in settings['assets']:
        label = asset['label']
        for repo_name, repo_url in REPOS.items():
            if label.startswith(repo_name):
                sha = get_latest_sha(repo_url, branch=branch)
                # обновление url и relative_path_file
                asset['url'] = f'{repo_url}/archive/{sha}.zip'
                asset['relative_path_file'] = f'services/{repo_name}/{sha}.zip'
                break

    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    update_settings(Path(__file__).parent / 'settings.json')
