import asyncio, subprocess, os
from pathlib import Path
from config import logger
from infrastructure_path_utils import get_root_dir_path, find_interpreter_by_root_dir
from config import settings

# флаг Windows для скрытия консоли (которая появлялась на win11) - иначе в процессе установки будет не красиво терминал дергаться
CREATE_NO_WINDOW = 0x08000000

window_name = 'services_installer'


async def run(
        cmd, cwd, queue: asyncio.Queue, event: asyncio.Event, srv_name: str,
        description_start: str = '', description_end: str = '',
):
    report = []  # текст в который добавляется прогресс установки

    def _run_sync():
        if description_start:
            report.append(description_start)
            queue.put_nowait(description_start)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=False,  # читать байты
            bufsize=1, shell=False, cwd=cwd,
            creationflags=CREATE_NO_WINDOW,
        )
        try:
            for raw_line in iter(process.stdout.readline, b''):  # пустая строка '' - EOF (является завершением цикла)
                if event.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    break
                # остановка процесса
                line = raw_line.decode(
                    'utf-8',
                    errors='replace',  # замена битых байтов
                ).rstrip()
                if line.strip():
                    report.append(line.rstrip())
                    queue.put_nowait(line.rstrip())
            if description_end:
                report.append(description_end)
                queue.put_nowait(description_end)
        except Exception as err:
            logger.exception(f'[ {window_name} ] Ошибка выполнения cmd {cmd} -> {err}')
            queue.put_nowait(f"❌ Ошибка выполнения cmd {cmd} -> {err}")
        finally:
            if process.poll() is None:
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            # записать логи процесса установки, для выявления ошибок в случае необходимости
            file_path = get_root_dir_path() / 'logs' / f'{srv_name}.txt'
            with open(file=file_path, mode='a', encoding='utf-8') as f:
                f.write('\n'.join(report))

    await  asyncio.to_thread(_run_sync)


def log_results(services, results, action_name: str):
    for srv, result in zip(services, results):
        if isinstance(result, Exception):
            logger.opt(exception=result).error(f'[{window_name}] Не удалось {action_name} для {srv.name}')
        else:
            logger.info(f'[{window_name}] {action_name} для {srv.name} успешно выполнено')


async def installer(target_dir: Path, queue: asyncio.Queue, event: asyncio.Event):
    # вспомогательный софт для установки
    utils_dir = target_dir / 'utils'
    services_dir = target_dir / 'services'
    services_dir.mkdir(exist_ok=True, parents=True)
    portable_git_dir = utils_dir / 'git'
    portable_python_path = utils_dir / 'python' / 'python.exe'
    # Проверка что portable python доступен
    if not portable_python_path.exists():
        logger.error(f'[ {window_name} ] На машине отсутствует python, не удалось его скачать и установить.')
        raise RuntimeError(f'На машине отсутствует python, не удалось его скачать и установить.')

    logger.info(f'[ {window_name} ] Собран портативный python')
    # Установка и проверка что git установился
    os.environ["PATH"] = os.path.join(portable_git_dir, "cmd") + os.path.pathsep + os.environ["PATH"]
    cmd = ['git', '--version']
    res = await asyncio.to_thread(
        lambda: subprocess.run(
            cmd,
            check=False, capture_output=True,
            creationflags=CREATE_NO_WINDOW,  # предотвращение появления черного окна консоли windows
        )
    )
    if res.returncode != 0:  # noqa
        logger.error(f'[ {window_name} ] На машине нет git, а также не удалось скачать портативную версию git.')
        raise RuntimeError(f'На машине нет git, а также не удалось скачать портативную версию git.')
    logger.info(f'[ {window_name} ] Собран портативный git')

    # ====================================================
    # Новое решение с гитом. Не забыть обложить всё трейс-беками
    tasks = []
    for repo in settings.repos:
        repo_url = repo['url']
        repo_name = repo_url.split('/')[-1]
        repo_dir = services_dir / repo_name
        repo_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f'git init для сервиса `{repo_name}`')
        cmd = ['git', 'init']
        task = asyncio.create_task(
            run(
                cmd=cmd, cwd=repo_dir, queue=queue,
                srv_name=repo_name,
                event=event,
            )
        )
        tasks.append(task)
    await asyncio.gather(*tasks, return_exceptions=True)

    for repo in settings.repos:
        repo_url = repo['url']
        repo_name = repo_url.split('/')[-1]
        repo_dir = services_dir / repo_name
        logger.info(f'git remote для сервиса `{repo_name}`')
        check = await asyncio.to_thread(
            lambda: subprocess.run(['git', 'remote'], cwd=repo_dir, capture_output=True, text=True)
        )
        if 'origin' not in check.stdout:
            cmd = ['git', 'remote', 'add', 'origin', repo_url]
        task = asyncio.create_task(
            run(
                cmd=cmd, cwd=repo_dir, queue=queue,
                srv_name=repo_name,
                event=event,
            )
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    for repo in settings.repos:
        repo_url = repo['url']
        repo_name = repo_url.split('/')[-1]
        repo_dir = services_dir / repo_name
        logger.info(f'git fetch origin для сервиса `{repo_name}`')
        cmd = ['git', 'fetch', 'origin']
        task = asyncio.create_task(
            run(
                cmd=cmd, cwd=repo_dir, queue=queue,
                srv_name=repo_name,
                event=event,
            )
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    tasks = []
    for repo in settings.repos:
        repo_url = repo['url']
        repo_name = repo_url.split('/')[-1]
        repo_hash = repo['hash']
        repo_dir = services_dir / repo_name
        logger.info(f'git checkout для сервиса `{repo_name}`')
        cmd = ['git', 'checkout', repo_hash]
        task = asyncio.create_task(
            run(
                cmd=cmd, cwd=repo_dir, queue=queue,
                srv_name=repo_name,
                event=event,
            )
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    # =====================================================
    services = [srv for srv in services_dir.iterdir()]
    # 1. Создание виртуальных окружений для сервисов
    tasks = []
    for srv in services:
        if event.is_set():
            return
        cmd = [portable_python_path, '-m', 'venv', '.venv']
        logger.info(f'[ {window_name} ] Создание виртуального окружения для {srv.name}')
        task = asyncio.create_task(
            run(
                cmd=cmd, cwd=srv, queue=queue,
                srv_name=srv.name,
                description_start=f'{srv.name} создание .venv',
                description_end=f'{srv.name} создание .venv    OK',
                event=event,
            )
        )
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    log_results(services=services, results=results, action_name='создание venv')

    # 2. Установка зависимостей сервисов (uv sync и так далее)
    tasks = []
    for srv in services:
        if event.is_set():
            return
        python_interpreter_venv = str(find_interpreter_by_root_dir(srv))
        logger.info(f'[ {window_name} ] Установка библиотек для {srv.name}')
        cmd = [python_interpreter_venv, 'start.py', 'sync']
        task = asyncio.create_task(run(cmd=cmd, cwd=srv, queue=queue, srv_name=srv.name, event=event))
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    log_results(services=services, results=results, action_name='установка библиотек')

    # 3. сборка билдов .exe
    tasks = []
    for srv in services:
        if event.is_set():
            return
        logger.info(f'[ {window_name} ] Сборка .exe для {srv.name}')
        python_interpreter_venv = str(find_interpreter_by_root_dir(srv))
        cmd = [python_interpreter_venv, 'cli.py', 'build']  # сборка директории (не одним файлом)
        task = asyncio.create_task(run(cmd=cmd, cwd=srv, queue=queue, event=event, srv_name=srv.name, ))
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    log_results(services=services, results=results, action_name='сборка .exe')
    await queue.put(None)  # обязательно sentinel


async def main():
    """Пример работы установщика"""

    async def observer(queue_in: asyncio.Queue):
        while True:
            try:
                res = await asyncio.wait_for(queue_in.get(), timeout=0.4)
                if res is None:
                    return
                print(res)
            except asyncio.TimeoutError:
                pass

    queue = asyncio.Queue()
    event = asyncio.Event()
    observer_task = asyncio.create_task(observer(queue_in=queue))
    await installer(target_dir=get_root_dir_path() / 'temp', queue=queue, event=event)
    await observer_task


if __name__ == '__main__':
    asyncio.run(main())
