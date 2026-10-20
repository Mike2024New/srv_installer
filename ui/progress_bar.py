import threading
from time import sleep
from typing import Callable

import customtkinter as ctk
from dataclasses import dataclass, field


@dataclass
class ProgressesBar:
    parent: ctk.CTk | ctk.CTkFrame | ctk.CTkScrollableFrame
    feedback_dict: dict[str, float]
    btn_close: bool = True
    btn_close_callback: Callable | None = None
    padx: int = 10
    pady: int = 10
    _event: threading.Event = field(default_factory=threading.Event)
    _frame: ctk.CTkFrame | None = None
    _progress_bar_widgets: dict[str, tuple[ctk.CTkProgressBar, ctk.CTkLabel]] = field(default_factory=dict)

    def __post_init__(self):
        self._frame = ctk.CTkFrame(self.parent)
        for dwn in self.feedback_dict:
            label = ctk.CTkLabel(self._frame, text=dwn, anchor='nw')
            progress = ctk.CTkProgressBar(self._frame, height=8, corner_radius=4)
            self._progress_bar_widgets[dwn] = (progress, label)
            progress.set(0.0)  # значение прогресс бара
            label.pack(fill='x', padx=self.padx, pady=(self.pady, self.pady / 5))
            progress.pack(fill='x', padx=self.padx, pady=(self.pady / 5, self.pady * 1.5))

        if self.btn_close:
            button = ctk.CTkButton(self._frame, text='Отменить', cursor='hand2')

            def stop_progress_bar_callback():
                self._event.set()
                if self.btn_close_callback is not None:
                    self.btn_close_callback()
                self._frame.destroy()

            button.configure(command=lambda: stop_progress_bar_callback())
            button.pack(side='right', padx=self.padx, pady=self.pady)

        self._frame.pack(expand=True, fill='x')
        self._observer()

    def _observer(self):
        """Наблюдатель за прогресс-баром, смотрит словарь feedback_dict и меняет шкалу прогресса"""
        # если задача была отменена
        if self._event.is_set():
            return

        # если окно уже было уничтожено
        if not self._frame.winfo_exists():
            return

        for key, val in self.feedback_dict.items():
            if key in self._progress_bar_widgets:
                self._progress_bar_widgets[key][0].set(val / 100)
                if val == 100:
                    self._progress_bar_widgets[key][0].destroy()
                    self._progress_bar_widgets[key][1].destroy()
                    self._progress_bar_widgets.pop(key)

        # выход когда все значения 100
        if all(val == 100 for val in self.feedback_dict.values()):
            self._frame.destroy()
            return

        self._frame.after(100, lambda: self._observer())  # noqa


if __name__ == '__main__':
    """Пример использования прогресс бара"""

    # создание формы
    padx, pady = 10, 10
    root = ctk.CTk()
    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('green')
    root.geometry('600x300+1000+100')
    root.configure(padx=padx, pady=pady)
    feedback_dict = {'srv_stt': 0, 'srv_llm': 0}


    # функция иммитирующая загрузку для прогресс-бара
    def example_gen_progress(fd):
        lock = threading.Lock()
        i = 0
        while i <= 100:
            sleep(0.1)
            for f in fd:
                with lock:
                    feedback_dict[f] = i
            i += 1


    # создать обект прогресс бара и он включит автоматически наблюдатель и будет обновлять прогресс
    ProgressesBar(parent=root, feedback_dict=feedback_dict, btn_close_callback=lambda: print(123))
    root.after(100, lambda: threading.Thread(target=lambda: example_gen_progress(fd=feedback_dict)).start())  # noqa
    root.mainloop()
