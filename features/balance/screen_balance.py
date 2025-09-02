from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from data.dao import BalanceDao

class BalanceScreen(MDScreen):
    name = "balance"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tbl = MDDataTable(
            size_hint=(1, 1),
            column_data=[("ID", dp(40)), ("帳戶", dp(100)), ("餘額", dp(100))],
            row_data=[],
        )
        self.add_widget(self.tbl)

    def on_pre_enter(self, *args):
        rows = [(str(r['id']), r['name'], f"{r['balance']:.2f}") for r in BalanceDao().balances()]
        self.tbl.update_row_data(None, rows)
