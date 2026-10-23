import json
from pathlib import Path
from typing import Callable
import customtkinter as ctk
from ui.collapsible_panel_text import CollapsiblePanel
from config import logger

window_name = 'license_window'


class LicenseWindow:
    def __init__(self, target_dir: Path, finish_callback: Callable | None = None, title: str = ''):
        self.finish_callback = finish_callback
        self._target_dir = target_dir
        self._title = title

    def window(self, _root: ctk.CTk, frame: ctk.CTkFrame, _row_state: ctk.CTkLabel, _storage: dict):
        if self._title:
            body_header_label = ctk.CTkLabel(frame, text=self._title)
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))

        lbl = ctk.CTkLabel(frame, text='Пожалуйста, прочтите и ознакомьтесь с лицензиями используемых компонентов.')
        lbl.pack(anchor='nw', padx=10, pady=10)

        licenses_dir = self._target_dir / 'LICENSES'
        panel_name = ''
        for file in licenses_dir.iterdir():
            content = ''
            text_license = ''
            for fr in file.iterdir():
                if fr.name == 'info.json':
                    with open(file / 'info.json', mode='r', encoding='utf8') as f:
                        info = json.loads(f.read())
                        panel_name = f"{file.name} ({info.get('license')})"
                        content += f'используется для: {info.get('description')}\n'
                        content += f'url лицензии: \n{"\n".join(info.get('url'))}\n\n'
                else:
                    with open(fr, mode='r', encoding='utf8') as f:
                        text_license += f"\nТекст лицензии ({fr.name}): {f.read()}"

            content += text_license
            panel = CollapsiblePanel(frame, title=panel_name)
            panel.set_text(text=content)
            panel.pack(fill="x", padx=10, pady=10)

        frame2 = ctk.CTkFrame(frame, fg_color='transparent', border_width=0)
        frame2.pack(fill="x", padx=10, pady=10)
        agree_checkbox = ctk.CTkCheckBox(frame2, text='Я ознакомился с лицензиями используемых компонентов')
        agree_checkbox.pack(expand=True, fill="x", side='left', padx=10, pady=10)

        def next_btn_callback():
            logger.info(f'[ {window_name} ] Условия лицензий просмотрены.')
            if self.finish_callback is not None:
                self.finish_callback()

        next_btn = ctk.CTkButton(frame2, text='Далее', cursor='hand2', state='disabled',
                                 command=lambda: next_btn_callback())

        def update_next_btn():
            next_btn.configure(state='normal' if agree_checkbox.get() else 'disabled')

        agree_checkbox.configure(command=lambda *args: update_next_btn())
        next_btn.pack(side='left', padx=10, pady=10)
