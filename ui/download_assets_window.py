import asyncio, threading
from pathlib import Path
from time import sleep
from typing import Callable
import customtkinter as ctk
from ui.progress_bar import ProgressesBar
from infrastructure_path_utils import get_root_dir_path, check_zip_integrity, check_tar_gz_integrity
from infrastructure_http_clients import DownloadTask, downolad_many_files
from config import settings, logger

window_name = 'download_assets_window'


class DownloadAssets:
    def __init__(
            self, target_dir: Path, event: asyncio.Event,
            finish_callback: Callable | None = None,
            title: str = '',
    ):
        """
        :param target_dir: целевая директория для скачивания файлов
        :param event: прерывание
        """
        self.finish_callback = finish_callback
        self._target_dir = target_dir
        self._download_tasks: list[DownloadTask] = []
        self._title = title
        self._row_state: ctk.CTkLabel | None = None
        self._scroll_frame: ctk.CTkScrollableFrame | None = None

        # создание задач на загрузку
        for asset in settings.assets:
            if not asset['ignore']:
                self._download_tasks.append(DownloadTask.model_validate(asset))

        self._feedback_dict = {dwn.label: 0.0 for dwn in self._download_tasks}
        self._event = event

    async def download_files(self):
        # Количество полных кругов (скачали -> проверили) [вынести потом в параметры]
        try:
            for i in range(settings.download_attempts):
                # 1. Качать всё, что не 100%
                pending = [t for t in self._download_tasks if self._feedback_dict[t.label] < 100]
                if pending:
                    await downolad_many_files(
                        root_dir=self._target_dir,
                        dwn_tasks=pending,
                        feedback_dict=self._feedback_dict,
                        event=self._event,
                        limit_tasks=4,  # одновременное количество загрузок
                    )

                # 2. Проверить целостность тех, что достигли 100%
                # файлы tar, zip критически важны, нужно проверить их целостность, без них приложение не соберется
                for task in self._download_tasks:
                    if self._feedback_dict[task.label] >= 100:
                        full_path = self._target_dir / task.relative_path_file
                        is_broken = False

                        # Проверка ZIP
                        if full_path.suffix == '.zip':
                            try:
                                check_zip_integrity(full_path)
                            except Exception:
                                is_broken = True
                        # Проверка TAR.GZ
                        elif full_path.name.endswith('.tar.gz'):
                            try:
                                check_tar_gz_integrity(full_path)
                            except Exception:
                                is_broken = True

                        # 3. Если битый - удалить и ставить 0%, чтобы скачался заново
                        if is_broken:
                            logger.warning(f"[{window_name}] Битый файл {full_path.name}, качается заново")
                            full_path.unlink(missing_ok=True)
                            self._feedback_dict[task.label] = 0.0

                # 4. Если после проверки нет файлов меньше 100%, значит всё идеально — выход
                if all(v >= 100 for v in self._feedback_dict.values()):
                    logger.info(f"[{window_name}] Все файлы скачаны и проверены.")
                    if self.finish_callback:
                        self.finish_callback()
                    return  # Успех, завершаем функцию

                # Если остались битые (0%), цикл пойдет на следующую попытку
                self._row_state.after(0, lambda: self._row_state.configure(
                    text=f'Перекачка битых файлов ({i + 1} / {attempts})...',
                    text_color='gold3'
                ))
                await asyncio.sleep(settings.download_attempts_interval_sec)

            # Если все 5 попыток прошли, а файлы всё еще битые
            print(f'Ни чего не прошло....')
            self._event.set()
            await asyncio.sleep(1)
            self._row_state.after(0, lambda: self._row_state.configure(
                text='Ошибка: интернет соединение слабое или отсутствует, попробуйте позже...', text_color='red'
            ))
            self._scroll_frame.destroy()

        except Exception as err:
            logger.exception(f'[{window_name}] Ошибка загрузки: {err}')
            self._event.set()

    def download_files_callback(self):
        threading.Thread(target=lambda: asyncio.run(self.download_files()), daemon=True).start()

    def observer(self, row_state: ctk.CTkLabel):
        def observer_thread():
            if not self._feedback_dict.values():
                return
            all_components_count = len(self._feedback_dict.values())
            while not self._event.is_set():
                # подсчёт текущего процента загрузки
                sleep(0.2)
                feedback_dict_values = list(self._feedback_dict.values())
                feedback_all_percents = len(feedback_dict_values) * 100
                feedback_fact_percents = sum(feedback_dict_values)
                percent = round((feedback_fact_percents * 100) / feedback_all_percents, 2)
                download_components_count = len([f for f in self._feedback_dict.values() if f >= 100])
                # Загрузка [2/6]  |  89.32%
                if percent == 100:
                    row_state.after(0, lambda p=percent: row_state.configure(
                        text=f'Загрузка [ {all_components_count}/{all_components_count} ]    |    100%',
                        text_color='green4'
                    ))  # noqa
                    break
                row_state.after(0, lambda p=percent: row_state.configure(
                    text=f'Загрузка [ {download_components_count}/{all_components_count} ]    |    {percent}%',
                    text_color='gold3'
                ))  # noqa

        threading.Thread(target=lambda: observer_thread(), daemon=True).start()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage: dict):
        """загрузка компонентов"""
        self._row_state = row_state
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        self._scroll_frame = ctk.CTkScrollableFrame(frame)
        self._scroll_frame.configure(fg_color='transparent', border_width=0)
        ProgressesBar(parent=self._scroll_frame, feedback_dict=self._feedback_dict, btn_close=False)
        self._scroll_frame.pack(expand=True, fill='both', padx=2, pady=2)
        root.after(1000, lambda: self.download_files_callback())  # noqa
        root.after(500, lambda: self.observer(row_state=row_state))  # noqa


if __name__ == '__main__':
    # окно с загрузкой ассетов из settings.json (вставляется в ui/main.py)
    download_assets_window = DownloadAssets(
        target_dir=get_root_dir_path() / 'sandbox',
        event=asyncio.Event(), finish_callback=lambda: print(123),
    )
