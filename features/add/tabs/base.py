from __future__ import annotations
from typing import Callable, Optional
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.tab import MDTabsBase

RecordExpense = Callable[[float, int | None, str | None], int | None]

class AddTabBase(MDBoxLayout, MDTabsBase):
    """所有 Add 子分頁的共同基底。"""
    def __init__(self, title: str, record_expense: Optional[RecordExpense] = None, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.title = title
        self.record_expense = record_expense
