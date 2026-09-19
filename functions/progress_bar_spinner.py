import asyncio
import itertools
from rich.live import Live
from rich.table import Table
import subprocess
from infrastructure_path_utils import find_interpreter_by_root_dir, get_root_dir_path
from dataclasses import dataclass


@dataclass
class TaskForSpinner:
    text: str
    task: asyncio.Task


async def console_spinner_progress_bar(tasks: list[TaskForSpinner]) -> None:
    """
    Прогресс бар, спинер, для отображения строк одной и более задач, например:
    task1 ..
    task2 ...
    task3 OK
    :param tasks: список состоящий из объектов TaskForSpinner (задача и её label)
    """
    # для windows консолей, максимально простой
    spinner = itertools.cycle(['.', '..', '...', '....', '.....', '....', '...', '..', '.'])

    with Live(refresh_per_second=10) as live:  # частота обновления экрана
        exit_for = False
        while not exit_for:
            table = Table(box=None)
            exit_for = True
            for t in tasks:
                if t.task.done():
                    table.add_row(f'{t.text} [green]OK[/green]')
                else:
                    exit_for = False  # если хотябы одна задача не выполнена, то продолжить
                    table.add_row(f'{t.text} [yellow]{next(spinner)}[/yellow]')
                live.update(table)
            await asyncio.sleep(0.2)


def run(delay: float = 2.0):
    """Длительная синхронная нагрузка для примера"""
    interpreter = find_interpreter_by_root_dir(get_root_dir_path())
    cmd = [interpreter, '-c', f'from time import sleep;sleep({delay})']
    subprocess.run(cmd, capture_output=True)


async def main():
    sync_task = asyncio.create_task(asyncio.to_thread(lambda: run(delay=4)))
    sync_task2 = asyncio.create_task(asyncio.to_thread(lambda: run(delay=2)))
    progress_task = asyncio.create_task(
        console_spinner_progress_bar(
            tasks=[
                TaskForSpinner(text='установка1', task=sync_task),
                TaskForSpinner(text='установка2', task=sync_task2),
            ]
        )
    )

    await sync_task
    await sync_task2
    await progress_task


if __name__ == '__main__':
    asyncio.run(main())
