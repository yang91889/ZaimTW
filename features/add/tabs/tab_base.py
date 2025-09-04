# features/add/tabs/tab_base.py
from __future__ import annotations
from typing import Callable, Optional

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.tab import MDTabsBase

class AddTabBase(MDBoxLayout, MDTabsBase):
    """
    Add 子分頁共同基底。
    - title: 供 MDTabs 顯示
    - record_expense: 上層注入的動作 callback（存起來就好，不要往 super 傳）
    """
    def __init__(self, title: str, record_expense: Optional[Callable] = None, **kwargs):
        # 只把 Kivy 相關的 kwargs 傳給 super，避免自訂參數觸發錯誤
        super().__init__(orientation="vertical", **kwargs)
        self.title = title
        self.record_expense = record_expense  # 給子類使用
