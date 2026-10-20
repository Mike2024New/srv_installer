import json

import customtkinter as ctk
from infrastructure_path_utils import get_root_dir_path
from typing import Callable, Literal
import tkinter as tk
from config import logger


class MainWindowUi:
    def __init__(
            self,
            pages: dict[str, Callable[[ctk.CTk, ctk.CTkFrame, ctk.CTkLabel, dict], None]] | None = None,
            min_width: int = 0, min_height: int = 0,
            resizable_width: bool = False, resizable_height: bool = False,
            start_theme: Literal['dark', 'light'] = 'dark',
            header_text: str = 'app',
            header: bool = False,
            footer: bool = False,
            nav_theme_switcher: bool = False,
            nav_pages_buttons: bool = False,
            nav_pages_combobox: bool = False,
    ):
        # решение проблемы с ошибками (можно логировать их через этот метод)
        tk.Tk.report_callback_exception = self._silent_exception_handler
        # остальная логика класса
        self._storage = {}  # окна могут хранить информацию между собой через ключи storage
        self._pages = pages
        self._page_index = 0
        self._page_order = list(self._pages.keys())
        self._page_combobox: ctk.CTkComboBox | None = None
        # установка темы
        ctk.set_appearance_mode(start_theme)
        ctk.set_default_color_theme(str(get_root_dir_path() / 'themes' / 'my_theme.json'))
        self.root = ctk.CTk()
        self._body_frame: ctk.CTkFrame | None = None

        # отрисовка шапки
        if header:
            self._header_frame_draw(
                header_text=header_text,
                nav_theme_switcher=nav_theme_switcher,
                nav_pages_buttons=nav_pages_buttons,
                nav_pages_combobox=nav_pages_combobox,
            )
        # отрисовка body -> фрейма на который размещается контент (pages)
        self._body_frame_draw()

        self._footer = footer
        if self._footer:
            self._footer_frame: ctk.CTkFrame | None = None
            self._row_state_lbl: ctk.CTkLabel | None = None
            self._footer_frame_draw()

        # отрисовка главного окна
        self.root.minsize(width=min_width, height=min_height)
        self.root.resizable(width=resizable_width, height=resizable_height)
        self.root.update_idletasks()
        self.center_window(win=self.root)  # окно теряется...

    def start(self):
        self.root.mainloop()

    @staticmethod
    def center_window(win):
        win.withdraw()
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        win_w = win.winfo_width()
        win_h = win.winfo_height()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        win.geometry(f'+{x}+{y}')
        win.after(0, win.deiconify)

    def _silent_exception_handler(self, _exc, _val, _tb):  # noqa
        """Перехват ошибок элементов -> ошибки tcl (необходимая мера, в частности из-за проблемы уничтожения скроллбаров)"""
        # пока принт, потом можно реализовать логирование
        # logger.exception(f'[ tkinter_error ] {_exc}\t{_val}\t{_tb}')
        pass

    def _body_frame_draw(self):
        """Очищаем только внутренности, не трогая сам базовый фрейм"""
        # Если фрейма еще нет (самый первый запуск) — создать его
        if self._body_frame is None:
            self._body_frame = ctk.CTkFrame(self.root)
            self._body_frame.pack(expand=True, fill='both', padx=10, pady=(10, 5))
        else:
            # Если он уже есть — просто удалить все дочерние виджеты внутри него
            self._body_frame.update_idletasks()
            for widget in self._body_frame.winfo_children():
                try:
                    widget.destroy()
                except Exception as err:  # noqa
                    logger.error(f'[ tkinter_error ] {err}')
        # В этой точке self._body_frame абсолютно чист, стабилен и готов принимать контент страницы

    def set_row_state(self, text: str, text_color: str):
        if not self._footer or not self._row_state_lbl:
            return
        # Безопасный вызов из любого фонового потока
        self.root.after(0, lambda: self._row_state_lbl.configure(text=text, text_color=text_color))  # noqa

    def _footer_frame_draw(self):
        """Отрисовка/перерисовка элементов футера"""
        if not self._footer:
            return
        if self._footer_frame is not None:
            self._footer_frame.pack_forget()
            for widget in self._footer_frame.winfo_children():
                widget.destroy()  # удалить дочерние элементы

        text = self._row_state_lbl.cget('text') if self._row_state_lbl is not None else ''
        text_color = self._row_state_lbl.cget('text_color') if self._row_state_lbl is not None else 'green'

        self._footer_frame = ctk.CTkFrame(self.root)
        self._row_state_lbl = ctk.CTkLabel(
            self._footer_frame, text=text, text_color=text_color, font=('roboto', 12, 'bold')
        )
        self._row_state_lbl.pack(anchor='w', padx=10, pady=10)
        self._footer_frame.pack(expand=False, fill='both', padx=10, pady=(5, 10))

    def _header_frame_draw(
            self, header_text: str, nav_pages_buttons: bool = False,
            nav_pages_combobox: bool = False, nav_theme_switcher: bool = False,
    ):
        """Отрисовка основных элементов шапки (заголовок, кнопки <> и переключения тем)"""
        # кнопка переключения тем
        frame_header = ctk.CTkFrame(self.root)
        frame_header.pack(expand=False, fill='x', padx=10, pady=(10, 0))

        # на прямую нет возможности через темы прописать стиль для этих кнопок (где текст как кнопки)
        # поэтому стиль выдергивается через fg_color
        elements_text_color = ctk.CTkButton(frame_header).cget('fg_color')

        self._header_lbl = ctk.CTkLabel(frame_header, text=header_text, text_color=elements_text_color)
        self._header_lbl.configure(font=('roboto', 18, 'bold'))
        self._header_lbl.pack(side='left', fill='x', padx=10, pady=8)

        if nav_theme_switcher:
            # кнопка переключения тем
            theme_btn = ctk.CTkButton(frame_header, text='◐', border_width=0, text_color=elements_text_color)
            theme_btn.configure(font=('roboto', 20, 'bold'))
            theme_btn.pack(side='right', anchor='e', padx=(0, 10), pady=2)
            theme_btn.configure(command=lambda: self._theme_switcher(theme_btn))
            theme_btn.configure(fg_color='transparent', hover=False, width=10)

        # переключение страниц
        if nav_pages_buttons:
            # окно вправо
            right_btn = ctk.CTkButton(frame_header, text_color=elements_text_color)
            right_btn.configure(
                text='▶', cursor='hand2', border_width=0,
                fg_color='transparent', hover=False, width=10,
                font=('roboto', 18, 'bold'),
                command=lambda: self._right_nav_button(),

            )
            right_btn.pack(side='right', fill='x', padx=(0, 10), pady=2)

            # окно влево
            left_btn = ctk.CTkButton(frame_header, text_color=elements_text_color)
            left_btn.configure(
                text='◀', cursor='hand2', border_width=0,
                fg_color='transparent', hover=False, width=10,
                font=('roboto', 18, 'bold'),
                command=lambda: self._left_nav_button(),
            )
            left_btn.pack(side='right', fill='x', padx=0, pady=0)

        # выбор страниц по названию
        if nav_pages_combobox:
            self._page_combobox = ctk.CTkComboBox(frame_header, values=self._page_order)
            self._page_combobox.configure(state='readonly', command=lambda choice: self.set_page(name=choice))
            self._page_combobox.pack(side='right', padx=0, pady=0)
            current_page = self._page_order[self._page_index]
            self._page_combobox.set(current_page)

    def _left_nav_button(self):
        if self._page_index > 0:
            self._page_index -= 1
        self.set_page(name=self._page_order[self._page_index])

    def _right_nav_button(self):
        if self._page_index < len(self._pages) - 1:
            self._page_index += 1
        self.set_page(name=self._page_order[self._page_index])

    def set_page(self, name: str):
        self._page_index = self._page_order.index(name)
        self._body_frame_draw()
        self._footer_frame_draw()
        self._pages[name](self.root, self._body_frame, self._row_state_lbl, self._storage)
        current_page = self._page_order[self._page_index]
        if self._page_combobox:
            self._page_combobox.set(current_page)

    @staticmethod
    def _theme_switcher(theme_btn):
        """Переключатель тем окна"""
        current_apperance_mode = ctk.get_appearance_mode().lower()
        if current_apperance_mode == 'light':
            ctk.set_appearance_mode('dark')
            theme_btn.configure(text='◐')
        elif current_apperance_mode == 'dark':
            ctk.set_appearance_mode('light')
            theme_btn.configure(text='◑')


if __name__ == '__main__':
    def example():
        # страница с контентом для примера
        def page1(_root, frame, _row_state, _storage):
            print(_storage)
            label = ctk.CTkLabel(frame, text='Page 1')
            text = ctk.CTkTextbox(frame)
            text.insert('0.0', text='Это первая страница, этого приложения. Просто для примера.')
            btn = ctk.CTkButton(frame, text='хорошо', cursor='hand2')

            label.pack(expand=True, fill='x', padx=10, pady=0, anchor='e')
            text.pack(expand=True, fill='both', padx=10, pady=(0, 10))
            btn.pack(expand=True, padx=10, pady=(0, 10), anchor='e')

        # страница с контентом для примера
        def page2(_root, frame, _row_state, _storage):
            from ui.collapsible_panel_text import CollapsiblePanel
            body_header_label = ctk.CTkLabel(frame, text=f'Параметры установки [ 1/8 ]')
            body_header_label.configure(font=('roboto', 18, 'bold'))
            body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
            lbl = ctk.CTkLabel(frame, text='Пожалуйста, прочтите и ознакомьтесь с условиями лицензий.')
            lbl.pack(anchor='nw', padx=10, pady=10)

            licenses_dir = get_root_dir_path() / 'LICENSES'
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
            agree_checkbox = ctk.CTkCheckBox(frame2, text='Я принимаю условия пользовательского соглашения')
            agree_checkbox.pack(expand=True, fill="x", side='left', padx=10, pady=10)

            next_btn = ctk.CTkButton(frame2, text='Далее', cursor='hand2', state='disabled', command=lambda: print(123))

            def update_next_btn():
                next_btn.configure(state='normal' if agree_checkbox.get() else 'disabled')

            agree_checkbox.configure(command=lambda *args: update_next_btn())
            next_btn.pack(side='left', padx=10, pady=10)

        # создание формы
        main_ui = MainWindowUi(
            pages={'page1': page1, 'page2': page2},
            header=True,
            header_text='установщик',
            footer=True,
            resizable_width=True, resizable_height=True,
            min_width=700, min_height=450,
            nav_theme_switcher=True,
            nav_pages_buttons=True,
            nav_pages_combobox=False,
        )
        # установка текущей страницы (опционально)
        main_ui.set_page(name='page2')
        main_ui.set_row_state(text='лицензионное соглашение', text_color='gold4')
        # запуск формы
        main_ui.start()


    example()
