from __future__ import annotations
from kivy.metrics import dp, sp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from ..widgets.currency_chip import CurrencyChip

class AmountBar(MDBoxLayout):
    """
    左：CurrencyChip（可綁 on_release 打開選單）
    右：金額 Label（提供 set_amount 調整字串）
    """
    def __init__(self, code: str, symbol: str, on_currency_tap, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(64), **kw)
        self.currency_chip = CurrencyChip(code=code, symbol=symbol)
        if callable(on_currency_tap):
            self.currency_chip.bind(on_release=lambda *_: on_currency_tap())

        self.lbl_amount = MDLabel(text="0", halign="right", font_size=sp(46),
                                  shorten=True, shorten_from="left")
        self.add_widget(self.currency_chip)
        self.add_widget(self.lbl_amount)

    def set_amount(self, text: str):
        self.lbl_amount.text = text

    def fit_amount_font(self, base_w: float, base_h: float):
        from kivy.metrics import sp
        base = min(base_w, base_h)
        fs = max(sp(28), min(sp(64), base * 0.075))
        self.lbl_amount.font_size = fs

    def set_currency(self, code: str, symbol: str):
        self.currency_chip.set_currency(code, symbol)
