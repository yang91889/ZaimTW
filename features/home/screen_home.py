from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, OneLineListItem
from data.dao import TxDao

class HomeScreen(MDScreen):
    name = "home"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = MDBoxLayout(orientation="vertical")
        sv = ScrollView()
        self.tx_list = MDList()
        sv.add_widget(self.tx_list)
        root.add_widget(sv)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.tx_list.clear_widgets()
        for row in TxDao().latest():
            text = f"#{row['id']} {row['date']}  {row['type']}  {row['amount']} {row['currency']}  {row['category']}"
            self.tx_list.add_widget(OneLineListItem(text=text))
