from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from data.dao import TxDao


class HomeScreen(MDScreen):
name = "home"


def on_pre_enter(self, *args):
self.ids.tx_list.clear_widgets()
for row in TxDao().latest():
text = f"#{row['id']} {row['date']} {row['type']} {row['amount']} {row['currency']} {row['category']}"
self.ids.tx_list.add_widget(OneLineListItem(text=text))


def build(self):
root = MDBoxLayout(orientation="vertical")
lst = MDList(id="tx_list")
root.add_widget(lst)
self.add_widget(root)