import customtkinter as ctk


class CollapsiblePanel(ctk.CTkFrame):
    def __init__(self, master, title="Заголовок", **kwargs):
        super().__init__(master, **kwargs)
        self._title = title
        self._is_expanded = False  # Изначально панель свернута
        # 1. Кнопка-заголовок, которая будет переключать видимость
        self.header_button = ctk.CTkButton(
            self, text=f'+  {self._title}', anchor="w", cursor="hand2",
            command=self.toggle, fg_color='transparent', hover=False, text_color='gray50',
            font=('roboto', 14)
        )
        self.header_button.pack(fill="x", padx=5, pady=5)
        # 2. Контентный фрейм, который будет скрываться/показываться
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Добавление текста
        self.text = ctk.CTkTextbox(self._content_frame, font=('roboto', 18))
        self.text.pack(fill="x", padx=10, pady=10)

    def set_text(self, text: str):
        self.text.insert('0.0', text)

    def toggle(self):
        if self._is_expanded:
            self._content_frame.pack_forget()
            self.header_button.configure(text=f'+  {self._title}')
            self._is_expanded = False
        else:
            self._content_frame.pack(fill="x", padx=5, pady=(0, 5))
            self.header_button.configure(text=f'−  {self._title}')
            self._is_expanded = True
