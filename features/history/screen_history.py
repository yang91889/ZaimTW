from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, OneLineListItem
from data.dao import TxDao

class HistoryScreen(MDScreen):
    name = "history"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        sv = ScrollView()
        self.lst = MDList()
        sv.add_widget(self.lst)
        self.add_widget(sv)

    def on_pre_enter(self, *args):
        self.lst.clear_widgets()
        for row in TxDao().latest(100):
            self.lst.add_widget(
                OneLineListItem(text=f"{row['date']} {row['type']} {row['amount']} {row['currency']}")
            )
