from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, OneLineListItem
from data.dao import TxDao


class HistoryScreen(MDScreen):
name = "history"


def on_pre_enter(self, *args):
self.ids.lst.clear_widgets()
for row in TxDao().latest(100):
self.ids.lst.add_widget(OneLineListItem(text=f"{row['date']} {row['type']} {row['amount']} {row['currency']}"))


def build(self):
lst = MDList(id="lst")
self.add_widget(lst)