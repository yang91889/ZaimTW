from __future__ import annotations
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from core.i18n import t
from .base import AddTabBase

class ManualTab(AddTabBase):
    def __init__(self, record_expense, **kwargs):
        super().__init__(title=t("ADD_TAB_MANUAL"), record_expense=record_expense, **kwargs)
        self.spacing = 12
        self.padding = [12, 12, 12, 12]

        self.add_widget(MDLabel(text=t("QUICK_ADD"), halign="center"))
        self.amount = MDTextField(hint_text=t("AMOUNT"), input_filter="float", mode="fill")
        self.add_widget(self.amount)

        row = MDFlatButton(text=t("CLEAR"))
        btn_row = MDRaisedButton(text=t("ADD_EXPENSE"), on_release=lambda *_: self._on_add())
        self.add_widget(btn_row)
        self.add_widget(row)
        row.bind(on_release=lambda *_: setattr(self.amount, "text", ""))

        self.status = MDLabel(text="", halign="center")
        self.add_widget(self.status)

    def _on_add(self):
        try:
            amt = float(self.amount.text)
        except Exception:
            self.status.text = t("ENTER_AMOUNT")
            return
        tx_id = self.record_expense(amt, 1)
        self.amount.text = ""
        self.status.text = t("RECORDED_TX", id=tx_id)
