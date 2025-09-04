from __future__ import annotations
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from core.i18n import t
from .tab_base import AddTabBase

class QuickTab(AddTabBase):
    def __init__(self, record_expense, **kwargs):
        super().__init__(title=t("ADD_TAB_QUICK"), record_expense=record_expense, **kwargs)
        self.spacing = 12
        self.padding = [12, 12, 12, 12]

        chips = MDBoxLayout(size_hint_y=None, height=48, spacing=8)
        for amt in (50, 100, 150, 200, 300):
            chips.add_widget(
                MDRaisedButton(text=str(amt),
                               on_release=lambda _w, a=amt: self.record_expense(float(a), 1))
            )
        self.add_widget(chips)

        row = MDBoxLayout(size_hint_y=None, height=56, spacing=8)
        self.amount = MDTextField(hint_text=t("AMOUNT"), input_filter="float", mode="fill")
        row.add_widget(self.amount)
        row.add_widget(MDRaisedButton(text=t("ADD_EXPENSE"), on_release=lambda *_: self._on_add()))
        self.add_widget(row)

    def _on_add(self):
        try:
            amt = float(self.amount.text)
        except Exception:
            return
        self.record_expense(amt, 1)
        self.amount.text = ""
