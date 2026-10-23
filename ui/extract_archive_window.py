import threading, queue
from pathlib import Path
from typing import Callable
from queue import Queue
import customtkinter as ctk
from config import settings, logger
from infrastructure_path_utils import extract_zip_func, extract_tar_func

window_name = 'extract_files'


class ExtractFiles:
    def __init__(
            self, target_dir: Path, event: threading.Event,
            finish_callback: Callable | None = None,
            title: str = '',
    ):
        """
        :param target_dir: целевая директория для скачивания файлов
        :param event: прерывание
        """
        self.target_dir = target_dir
        self._event = event
        self.finish_callback = finish_callback
        self._title = title
        self._extracted_report = []

    def extract(self, queue_progress: Queue | None = None):
        """
        Извлечение архивов файлов указанных в settings.json
        """
        for fl in settings.assets:
            if self._event.is_set():
                break
            path_archive = self.target_dir / fl['relative_path_file']
            if queue_progress is not None:
                queue_progress.put_nowait(f'Извлечение: {path_archive.name}')
            # обработка zip файлов
            if path_archive.suffix == '.zip':
                self._extracted_report.append(path_archive.name)
                extract_zip_func(
                    file=path_archive,
                    delete_archive=False,  # оставить архивы, так как мало ли установка прервется пользователем
                    del_root_folder=fl['del_root_folder'],
                )
            # обработка tar файлов
            elif path_archive.name.endswith('.tar.gz'):
                self._extracted_report.append(path_archive.name)
                extract_tar_func(
                    file=path_archive,
                    delete_archive=False,  # оставить архивы, так как мало ли установка прервется пользователем
                    del_root_folder=fl['del_root_folder'],
                )
            if queue_progress is not None:
                queue_progress.put_nowait(f'извлечение: {path_archive.name}    OK')
        if queue_progress is not None:
            queue_progress.put_nowait(None)

    def observer(self, textbox, queue_progress: Queue):
        """Вставка строк прогресса в текстовое поле (живой процесс установки)"""

        def observer_thread():
            while not self._event.is_set():
                try:
                    row = queue_progress.get(timeout=0.5)
                    if row is None:
                        if self.finish_callback is not None:
                            logger.info(f'[ {window_name} ] извлечены файлы: {self._extracted_report}')
                            logger.info(f'[ {window_name} ][ END ] извлечение .zip/.tar.gz компонентов')
                            textbox.after(100, self.finish_callback)
                        break
                except queue.Empty:
                    continue

                textbox.after(0, lambda r=row: textbox.insert('end', f"\n{r}"))
                textbox.after(0, lambda: textbox.see('end'))

        threading.Thread(target=lambda: observer_thread(), daemon=True).start()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage):
        logger.info(f'[ {window_name} ][ start ] извлечение .zip/.tar.gz компонентов')
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        text = ctk.CTkTextbox(frame)
        row_state.configure(text='распаковка ахивов', text_color='gold3')
        text.pack(expand=True, fill='both', padx=10, pady=(10, 10))
        queue_progress = Queue()
        threading.Thread(target=lambda: self.extract(queue_progress=queue_progress), daemon=True).start()
        root.after(500, lambda: self.observer(textbox=text, queue_progress=queue_progress))
