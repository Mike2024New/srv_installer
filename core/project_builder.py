import asyncio, subprocess
from pathlib import Path
from infrastructure_path_utils import find_interpreter_by_root_dir
from functions import console_spinner_progress_bar, TaskForSpinner


async def run(cmd, cwd):
    def func():
        res = subprocess.run(cmd, cwd=cwd, capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(f'Ошибка {cmd}.')

    await asyncio.to_thread(func)


async def builder(python_portable, svc_dir):
    cmd = [python_portable, '-m', 'venv', '.venv']
    await run(cmd, cwd=svc_dir)
    # # получение интерпретатора (.venv/python)
    python_interpreter = str(find_interpreter_by_root_dir(svc_dir))
    cmd = [python_interpreter, 'start.py']
    await run(cmd, cwd=svc_dir)


async def project_builder(target_dir: Path, python_portable: Path):
    if not target_dir.exists():
        raise RuntimeError(f'Не найдена директория с сервисами `{target_dir}`')

    tasks = []
    tasks_for_spinner = []
    for svc_dir in target_dir.iterdir():
        # фильтрация сервисов по критериям
        if not svc_dir.is_dir() or not (svc_dir / 'cli.py').exists() or not (svc_dir / 'start.py').exists():
            continue
        svc_name = svc_dir.name
        task = asyncio.create_task(builder(python_portable=python_portable, svc_dir=svc_dir))
        tasks.append(task)
        tasks_for_spinner.append(TaskForSpinner(text=f'установка `{svc_name}`', task=task))

    progress_task = asyncio.create_task(
        console_spinner_progress_bar(
            tasks=tasks_for_spinner,
        )
    )

    await asyncio.gather(*tasks, return_exceptions=False)
    await progress_task
