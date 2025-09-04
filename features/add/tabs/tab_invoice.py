# features/add/tabs/tab_invoice.py
from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton

from core.i18n import t
from .tab_base import AddTabBase


class InvoiceTab(AddTabBase):
    def __init__(self, record_expense, **kwargs):
        # title 會顯示在 MDTabs 的 tab 標籤
        super().__init__(title=t("ADD_TAB_INVOICE") or "Invoice", **kwargs)
        self.spacing = 12
        self.padding = [0, 0, 0, 0]

        # 內容
        self.add_widget(
            MDLabel(
                text="Camera / OCR pipeline will be added later.",
                halign="center",
            )
        )

        btn_row = MDBoxLayout(size_hint_y=None, height=48, spacing=12, padding=[12, 0, 12, 0])
        btn_row.add_widget(MDRaisedButton(text=t("SELECT_IMAGE") or "Select Image (stub)",
                                          on_release=lambda *_: None))
        btn_row.add_widget(MDFlatButton(text=t("SCAN_OCR") or "Scan (OCR - later)",
                                        on_release=lambda *_: None))
        self.add_widget(btn_row)
