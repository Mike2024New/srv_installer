import asyncio, threading
import os
from pathlib import Path
from time import sleep
from typing import Callable
import customtkinter as ctk
from ui.progress_bar import ProgressesBar
from infrastructure_path_utils import get_root_dir_path, check_zip_integrity, check_tar_gz_integrity
from infrastructure_http_clients.file_downloader_v3 import DownloadTask, downolad_many_files

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
        self._root: ctk.CTk | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._frame: ctk.CTkFrame | None = None
        self._scroll_frame: ctk.CTkScrollableFrame | None = None
        self._silence_observer = False

        # создание задач на загрузку
        for asset in settings.assets:
            if not asset['ignore']:
                self._download_tasks.append(DownloadTask.model_validate(asset))

        self._feedback_dict = {
            dwn.label: {'progress': 0.0, 'total': 0, 'downolad': 0} for dwn in self._download_tasks
        }
        self._event = event

    async def download_files(self):
        try:
            def retries_callback(x):
                x = x + 1
                msg = f'Не все ассеты загрузились, ухожу на новый круг {x}/{settings.download_retries}.'
                # Безопасное обновление UI из потока
                self._root.after(0, lambda m=msg: self._row_state.configure(text=m))
                logger.warning(
                    f'[ {window_name} ] Не все ассеты загрузились, ухожу на новый круг {x}/{settings.download_retries}.\nСейчас загружено: {self._feedback_dict}'
                )

            await downolad_many_files(
                root_dir=self._target_dir,
                dwn_tasks=self._download_tasks,
                feedback_dict=self._feedback_dict,
                event=self._event,
                limit_tasks=4,  # одновременное количество загрузок (защита сети от перегрузки)
                retries=settings.download_retries,  # попытки переподключения
                retries_timeout=settings.download_retries_timeout,
                retries_callback=retries_callback,
                error_callback=lambda msg: logger.error(f'[ {window_name} ] Ошибка при загрузке компонентов: {msg}')
            )
            if self.finish_callback:
                logger.info(
                    f'[ {window_name} ][ end ] загрузка компонентов завершена, результат: {self._feedback_dict}'
                )
                self.finish_callback()
            return  # Успех, завершаем функцию

        except Exception as err:
            self._event.set()
            logger.error(
                f'[ {window_name} ] Ошибка не все компоненты удалось загрузить. Результат: {self._feedback_dict}, текст ошибки: {err}'
            )
            await asyncio.sleep(1)

            # Безопасное обновление UI из фонового потока
            def show_error_ui():
                self._row_state.configure(
                    text='Ошибка: интернет соединение слабое или отсутствует, попробуйте позже...',
                    text_color='red'
                )
                self._scroll_frame.destroy()
                msg = 'Ошибка, интернет соединение слабое. Попробуйте позже. Загрузка файлов продолжится с того же места. \nНажмите крестик чтобы выйти.'
                text_area = ctk.CTkTextbox(self._frame, width=550, fg_color='transparent')
                text_area.configure(font=('roboto', 14, 'normal'), text_color='red4')
                text_area.pack(expand=True, fill='both', padx=10, pady=(0, 5))
                text_area.insert('1.0', msg)

            self._root.after(0, show_error_ui)

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
                feedback_dict_values = [val['progress'] for val in self._feedback_dict.values()]

                feedback_all_percents = len(feedback_dict_values) * 100
                feedback_fact_percents = sum(feedback_dict_values)
                percent = round((feedback_fact_percents * 100) / feedback_all_percents, 2)
                # подсчёт количества загруженных элементов
                download_components_count = len(
                    [val['progress'] for val in self._feedback_dict.values() if val['progress'] >= 100]
                )
                # Загрузка [2/6]  |  89.32%
                if percent == 100:
                    row_state.after(0, lambda p=percent: row_state.configure(
                        text=f'Загрузка [ {all_components_count}/{all_components_count} ]    |    100%',
                        text_color='green4'
                    ))  # noqa
                    break
                if not self._silence_observer:
                    row_state.after(0, lambda p=percent: row_state.configure(
                        text=f'Загрузка [ {download_components_count}/{all_components_count} ]    |    {percent}%',
                        text_color='gold3'
                    ))  # noqa

        threading.Thread(target=lambda: observer_thread(), daemon=True).start()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage: dict):
        """загрузка компонентов"""
        logger.info(f'[ {window_name} ][ start ] начата загрузка компонентов')
        self._frame = frame
        self._root = root
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
