import subprocess
from pathlib import Path
from typing import Callable
import customtkinter as ctk
from config import settings
from pyshortcuts import make_shortcut

# для запуска приложения в процессе не привязанном к этому инсталлеру
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


class FinishWindow:
    def __init__(self, root_dir: Path, finish_callback: Callable | None = None, title: str = ''):
        self.root_dir = root_dir
        self.finish_callback = finish_callback
        self._title = title

    def window(self, _root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))

        row_state.configure(text='завершение установки', text_color='green4')
        frame1 = ctk.CTkFrame(frame, fg_color='transparent')
        label = ctk.CTkLabel(frame1, text='Установка завершена! Выберите опции и нажмите "закрыть"')
        checkbox_shortcut_dekstop_icon = ctk.CTkCheckBox(frame1, text='создать ярлык на рабочем столе')
        checkbox_shortcut_start_menu = ctk.CTkCheckBox(frame1, text='создать ярлык в меню пуск')
        run_app_checkbox = ctk.CTkCheckBox(frame1, text='запустить приложение')
        label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        checkbox_shortcut_dekstop_icon.pack(anchor='w', padx=10, pady=10)
        checkbox_shortcut_start_menu.pack(anchor='w', padx=10, pady=10)
        run_app_checkbox.pack(anchor='w', padx=10, pady=10)
        checkbox_shortcut_start_menu.set(True)
        checkbox_shortcut_dekstop_icon.set(True)

        def finish():
            exe_path = None
            if 'target_dir' in storage:
                target_dir = Path(storage['target_dir'])
                # получение точного пути к приложению
                exe_path = Path(target_dir) / settings.app_name / settings.main_srv_dirname / 'app.exe'

            if exe_path is not None and exe_path.exists():
                # если установлена галочка создать ярлык на рабочий стол

                make_shortcut(
                    str(exe_path), name=settings.app_name,
                    desktop=bool(checkbox_shortcut_dekstop_icon.get()),
                    startmenu=bool(checkbox_shortcut_start_menu.get()),
                    icon=str(exe_path.parent / 'icon.ico'),
                )

                # если установлена галочка запустить приложение
                if bool(run_app_checkbox.get()):
                    subprocess.Popen(
                        [str(exe_path)],
                        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        cwd=str(exe_path.parent),
                    )

            # запуск финального callback
            if self.finish_callback is not None:
                self.finish_callback()

        button_next_install = ctk.CTkButton(frame, text='закрыть', cursor='hand2')
        button_next_install.configure(command=lambda: finish())
        frame1.configure(border_width=0)
        frame1.pack(expand=True, fill='both', padx=2, pady=2)
        button_next_install.pack(fill='x', anchor='se', side='right', padx=10, pady=(5, 10))
