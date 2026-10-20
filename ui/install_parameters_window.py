from pathlib import Path
from typing import Callable
from config import logger
import customtkinter as ctk

window_name = 'start_window'


class StartWindow:
    def __init__(self, finish_callback: Callable | None = None, title: str = ''):
        self.finish_callback = finish_callback
        self._title = title

    def window(self, _root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))

        if 'target_dir' not in storage:
            storage['target_dir'] = Path.home()
        row_state.configure(text='выбор параметров установки', text_color='green4')
        frame1 = ctk.CTkFrame(frame, fg_color='transparent')
        label = ctk.CTkLabel(frame1, text='Выберите целевую папку:')
        entry = ctk.CTkEntry(frame1)
        button_select_folder = ctk.CTkButton(frame1, text='выбрать', cursor='hand2')

        def select_folder(title: str = 'Выбор папки', initialdir: Path = Path.home()):
            from tkinter import filedialog
            # Открывает системное окно выбора папки
            folder_path = filedialog.askdirectory(
                title=title,
                initialdir=initialdir
            )

            if folder_path:  # Если пользователь выбрал папку (не нажал "Отмена")
                entry.delete(0, "end")
                entry.insert('0', str(folder_path))
                storage['target_dir'] = folder_path
                logger.info(f'[{window_name}] Выбрана директория: {folder_path}')

        button_select_folder.configure(command=lambda: select_folder())
        button_next_install = ctk.CTkButton(frame, text='далее', cursor='hand2')
        button_next_install.configure(command=lambda: self.finish_callback())
        entry.insert('0', storage['target_dir'])
        frame1.configure(border_width=0)
        frame1.pack(expand=True, fill='both', padx=2, pady=2)
        label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        entry.pack(expand=True, anchor='nw', fill='x', side='left', padx=10, pady=(5, 5))
        button_select_folder.pack(fill='x', anchor='nw', side='left', padx=10, pady=(5, 5))
        button_next_install.pack(fill='x', anchor='se', side='right', padx=10, pady=(5, 10))
