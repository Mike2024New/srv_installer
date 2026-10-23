import shutil
import threading, queue
from pathlib import Path
from typing import Callable
from queue import Queue
import customtkinter as ctk
from config import logger

window_name = 'delete_temp_dir'


class DeleteTempDirWindow:
    def __init__(
            self,
            root_dir: Path, event: threading.Event,
            finish_callback: Callable | None = None,
            title: str = '',
    ):
        self.root_dir = root_dir
        self._event = event
        self.finish_callback = finish_callback
        self._title = title
        self._queue_report = Queue()

    def process(self):
        # удаление сервисов
        try:
            self._queue_report.put_nowait('Удаление временных директорий')
            shutil.rmtree('\\\\?\\' + str(self.root_dir))
            self._queue_report.put_nowait(None)
            logger.info(f'[ {window_name} ] временная директория удалена')
        except Exception as err:
            logger.exception(f'[ {window_name} ] ошибка при удалении временной директории: {err}')
            self._queue_report.put_nowait(f'Не удалось удалить временную директорию: {err}')
            self._queue_report.put_nowait(None)

    def observer(self, textbox):
        """Вставка строк прогресса в текстовое поле (живой процесс установки)"""

        def observer_thread():
            while not self._event.is_set():
                try:
                    row = self._queue_report.get(timeout=0.5)
                    if row is None:
                        if self.finish_callback is not None:
                            logger.info(f'[ {window_name} ][ END ] удаление временной директории завершено')
                            textbox.after(100, self.finish_callback)
                        break
                except queue.Empty:
                    continue

                textbox.after(0, lambda r=row: textbox.insert('end', f"\n{r}"))
                textbox.after(0, lambda: textbox.see('end'))

        threading.Thread(target=lambda: observer_thread(), daemon=True).start()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage):
        logger.info(f'[ {window_name} ][ START ] удаление временной директории')
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        text = ctk.CTkTextbox(frame)
        row_state.configure(text='перемещение проекта в целевую директорию', text_color='gold3')
        text.pack(expand=True, fill='both', padx=10, pady=(10, 10))
        threading.Thread(target=lambda: self.process(), daemon=True).start()
        root.after(500, lambda: self.observer(textbox=text))  # noqa
