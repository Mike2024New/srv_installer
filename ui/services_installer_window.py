import asyncio
import threading
from pathlib import Path
from typing import Callable
import customtkinter as ctk
from core import installer

window_name = 'services_installer_window'

class ServicesInstallerWindow:
    def __init__(
            self, target_dir: Path, event: asyncio.Event,
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
        self._queue_report = asyncio.Queue()

    async def process(self):
        await installer(target_dir=self.target_dir, queue=self._queue_report, event=self._event)

    def start_installer(self):
        """Запуск сборщика приложений"""
        threading.Thread(target=lambda: asyncio.run(self.process()), daemon=True).start()

    def start_observer(self, textbox):
        async def observer():
            """Наблюдение за процессом установки приложений"""
            while True:
                try:
                    res = await asyncio.wait_for(self._queue_report.get(), timeout=0.4)
                    if res is None:
                        # функция в конце выполнения полезной нагрузки (например переход на новую страницу)
                        if self.finish_callback is not None:
                            textbox.after(0, self.finish_callback)
                        return
                    textbox.after(0, lambda r=res: textbox.insert('end', f"\n{r}"))
                    textbox.after(0, lambda: textbox.see('end'))
                except asyncio.TimeoutError:
                    pass

        threading.Thread(
            target=lambda: asyncio.run(observer()),
            daemon=True,
        ).start()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage):
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        text = ctk.CTkTextbox(frame)
        row_state.configure(text='сборка компонентов', text_color='gold3')
        text.pack(expand=True, fill='both', padx=10, pady=(10, 10))
        root.after(1000, lambda: self.start_installer())  # noqa
        root.after(500, lambda: self.start_observer(textbox=text))  # noqa
