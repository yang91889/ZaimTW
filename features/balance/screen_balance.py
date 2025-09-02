from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from data.dao import BalanceDao


class BalanceScreen(MDScreen):
name = "balance"


def on_pre_enter(self, *args):
self.ids.tbl.update_row_data(None, [(
str(r['id']), r['name'], f"{r['balance']:.2f}") for r in BalanceDao().balances()])


def build(self):
tbl = MDDataTable(
id="tbl",
size_hint=(1, 1),
column_data=[("ID", dp(40)), ("帳戶", dp(80)), ("餘額", dp(80))],
row_data=[],
)
self.add_widget(tbl)