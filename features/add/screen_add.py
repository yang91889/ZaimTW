from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
from domain.usecases import UseCases


class AddScreen(MDScreen):
name = "add"


def __init__(self, usecases: UseCases, **kwargs):
super().__init__(**kwargs)
self.usecases = usecases


def _on_add(self, *_):
try:
amt = float(self.ids.amount.text)
except Exception:
self.ids.status.text = "請輸入金額"
return
tx_id = self.usecases.quick_add_tx(amount=amt, category_id=1)
self.ids.amount.text = ""
self.ids.status.text = f"已記錄交易 #{tx_id}"
# 讓首頁刷新
self.parent.switch_to(self.parent.get_screen("home"))


def build(self):
root = MDBoxLayout(orientation="vertical", padding=12, spacing=12)
root.add_widget(MDLabel(text="快速記帳", halign="center"))
self.ids.amount = MDTextField(hint_text="金額", input_filter="float", mode="fill")
root.add_widget(self.ids.amount)
btn_row = MDBoxLayout(size_hint_y=None, height=48, spacing=12)
add_btn = MDRaisedButton(text="支出", on_release=self._on_add)
clr_btn = MDFlatButton(text="清除", on_release=lambda *_: setattr(self.ids.amount, 'text', ''))
btn_row.add_widget(add_btn)
btn_row.add_widget(clr_btn)
root.add_widget(btn_row)
self.ids.status = MDLabel(text="", halign="center")
root.add_widget(self.ids.status)
self.add_widget(root)