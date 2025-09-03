from __future__ import annotations
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from core.i18n import t
from .base import AddTabBase

class InvoiceTab(AddTabBase):
    def __init__(self, record_expense=None, **kwargs):
        super().__init__(title=t("ADD_TAB_INVOICE"), record_expense=record_expense, **kwargs)
        self.spacing = 12
        self.padding = [12, 12, 12, 12]
        self.add_widget(MDLabel(text="Camera / OCR pipeline will be added later.", halign="center"))
        row = MDBoxLayout(size_hint_y=None, height=48, spacing=12)
        row.add_widget(MDRaisedButton(text=t("SELECT_IMAGE"), on_release=lambda *_: None))
        row.add_widget(MDFlatButton(text=t("SCAN_OCR"), on_release=lambda *_: None))
        self.add_widget(row)
