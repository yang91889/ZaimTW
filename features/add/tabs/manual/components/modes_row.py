from __future__ import annotations
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton

class ModesRow(MDBoxLayout):
    """
    三顆 mode 按鈕列。透過 on_mode 回呼通知外部，並內建樣式切換（無陰影）。
    on_mode(mode: str) 會收到 "expense" | "income" | "transfer"
    """
    def __init__(self, on_mode, **kw):
        super().__init__(orientation="horizontal", spacing=dp(10),
                         size_hint_y=None, height=dp(44), **kw)
        self.on_mode = on_mode
        self._mode = "expense"

        self.btn_exp = MDRaisedButton(text="EXPENSE", size_hint=(1, None), height=dp(40))
        self.btn_inc = MDFlatButton(text="INCOME",   size_hint=(1, None), height=dp(40))
        self.btn_trf = MDFlatButton(text="TRANSFER", size_hint=(1, None), height=dp(40))

        for b in (self.btn_exp, self.btn_inc, self.btn_trf):
            b.pos_hint = {"center_y": .5}
            b.elevation = 0
            if hasattr(b, "elevation_disabled"): b.elevation_disabled = 0
            if hasattr(b, "shadow_color"): b.shadow_color = (0, 0, 0, 0)
            self.add_widget(b)

        self.btn_exp.bind(on_release=lambda *_: self.set_mode("expense"))
        self.btn_inc.bind(on_release=lambda *_: self.set_mode("income"))
        self.btn_trf.bind(on_release=lambda *_: self.set_mode("transfer"))

        self._apply_styles("expense")

    def set_mode(self, m: str):
        if m == self._mode:
            return
        self._mode = m
        self._apply_styles(m)
        if callable(self.on_mode):
            self.on_mode(m)

    def _apply_styles(self, m: str):
        ACTIVE_BG  = self.theme_cls.primary_color
        ACTIVE_TXT = (1, 1, 1, 1)
        INACTIVE_BG  = (0, 0, 0, 0.10)
        INACTIVE_TXT = (0, 0, 0, 0.87)

        def paint(btn, active: bool):
            btn.disabled = False
            btn.md_bg_color = ACTIVE_BG if active else INACTIVE_BG
            btn.text_color  = ACTIVE_TXT if active else INACTIVE_TXT
            btn.elevation = 0

        paint(self.btn_exp, m == "expense")
        paint(self.btn_inc, m == "income")
        paint(self.btn_trf, m == "transfer")
