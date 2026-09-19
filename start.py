import asyncio, sys, subprocess
import json
from pathlib import Path

"""
Пусковой стартовый скрипт, для сборки зависимостей и скачивания необходимых компонентов.
Важно! Перед запуском должно быть создано виртуальное окружение, и название папки должно быть .venv
"""
steps = 5
lock = asyncio.Lock()


async def installer_log(step: int, description: str):
    """Запись текущей операции в json (для интеграции с лаунчером)"""
    print(f'{step}.{description}')
    async with lock:
        with open(file=Path('installer.json'), mode='w', encoding='utf8') as f:
            f.write(
                json.dumps(
                    {'step': step, 'steps': steps, 'description': description},
                    indent=2,
                    ensure_ascii=False,
                )
            )


async def start():
    await installer_log(step=1, description='установка uv')
    cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
    subprocess.run(cmd, shell=False)

    await installer_log(step=2, description='установка библиотек')
    cmd = [sys.executable, '-m', 'uv', 'sync']
    subprocess.run(cmd, shell=False)

    await installer_log(step=3, description='сборка .exe/bin')
    cmd = [sys.executable, 'cli.py', 'build', '-oe']
    subprocess.run(cmd, shell=False)


if __name__ == '__main__':
    asyncio.run(start())
