from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel


class CurrencyChip(ButtonBehavior, MDBoxLayout):
    """幣別圓角卡（上：大符號；下：代碼）。點擊由外層開選單。"""
    code   = StringProperty("JPY")
    symbol = StringProperty("¥")

    def __init__(self, code: str, symbol: str, **kw):
        super().__init__(**kw)
        self.code = code
        self.symbol = symbol

        # layout
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.height = dp(52)
        self.width  = dp(92)  # 想更像圓就把 width = height
        self.padding = (dp(12), dp(8), dp(12), dp(8))
        self.spacing = dp(2)

        # background
        self._bg_normal = [0, 0, 0, 0.06]
        self._bg_down   = [0, 0, 0, 0.12]
        with self.canvas.before:
            self._bg_color = Color(rgba=self._bg_normal)
            self._bg_rect  = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(1)]*4)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # labels (centered)
        self.lbl_symbol = MDLabel(text=self.symbol, font_size=sp(24), bold=True,
                                  halign="center", valign="middle")
        self.lbl_code   = MDLabel(text=self.code,   font_size=sp(12), opacity=0.85,
                                  halign="center", valign="middle")
        for lbl in (self.lbl_symbol, self.lbl_code):
            lbl.bind(size=lambda *_ , L=lbl: self._center_label(L))
        self.add_widget(self.lbl_symbol)
        self.add_widget(self.lbl_code)

    def _center_label(self, lbl):
        lbl.text_size = lbl.size

    def _update_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size
        r = min(self.width, self.height) / 2.0
        self._bg_rect.radius = [r, r, r, r]

    def on_press(self):
        self._bg_color.rgba = self._bg_down

    def on_release(self):
        self._bg_color.rgba = self._bg_normal
        super().on_release()

    def set_currency(self, code: str, symbol: str):
        self.code = code
        self.symbol = symbol
        self.lbl_code.text = code
        self.lbl_symbol.text = symbol
