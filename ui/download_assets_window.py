import asyncio, threading
from pathlib import Path
from time import sleep
from typing import Callable
import customtkinter as ctk
from ui.progress_bar import ProgressesBar
from infrastructure_path_utils import get_root_dir_path
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
        self._download_tasks = []
        self._title = title

        # создание задач на загрузку
        for asset in settings.assets:
            self._download_tasks.append(DownloadTask.model_validate(asset))

        self._feedback_dict = {dwn.label: 0.0 for dwn in self._download_tasks}
        self._event = event

    async def download_files(self):
        try:
            await downolad_many_files(
                root_dir=self._target_dir,
                dwn_tasks=self._download_tasks,
                feedback_dict=self._feedback_dict,
                event=self._event,
                limit_tasks=4,
            )

            if self.finish_callback is not None:
                # фиксация, прогресса загрузок
                logger.info(f"[{window_name}] Загружены файлы: {self._feedback_dict.values()}")
                # выполнение функции после загрузки (например переход на следующую страницу)
                self.finish_callback()
        except Exception as err:
            logger.exception(f'[{window_name}] Ошибка загрузки: {err}')
            print(f'❌ Ошибка загрузки: {err}')

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
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.configure(fg_color='transparent', border_width=0)
        ProgressesBar(parent=scroll_frame, feedback_dict=self._feedback_dict, btn_close=False)
        scroll_frame.pack(expand=True, fill='both', padx=2, pady=2)
        root.after(1000, lambda: self.download_files_callback())  # noqa
        root.after(500, lambda: self.observer(row_state=row_state))  # noqa


if __name__ == '__main__':
    # окно с загрузкой ассетов из settings.json (вставляется в ui/main.py)
    download_assets_window = DownloadAssets(
        target_dir=get_root_dir_path() / 'sandbox',
        event=asyncio.Event(), finish_callback=lambda: print(123),
    )
