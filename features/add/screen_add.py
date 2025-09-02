from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from domain.usecases import UseCases
from core.i18n import t

class AddScreen(MDScreen):
    name = "add"

    def __init__(self, usecases: UseCases, switch_tab, **kwargs):
        super().__init__(**kwargs)
        self.usecases = usecases
        self.switch_tab = switch_tab

        root = MDBoxLayout(orientation="vertical", padding=12, spacing=12)
        root.add_widget(MDLabel(text=t("QUICK_ADD"), halign="center"))

        self.amount = MDTextField(hint_text=t("AMOUNT"), input_filter="float", mode="fill")
        root.add_widget(self.amount)

        btn_row = MDBoxLayout(size_hint_y=None, height=48, spacing=12)
        add_btn = MDRaisedButton(text=t("ADD_EXPENSE"), on_release=self._on_add)
        clr_btn = MDFlatButton(text=t("CLEAR"), on_release=lambda *_: setattr(self.amount, 'text', ''))
        btn_row.add_widget(add_btn)
        btn_row.add_widget(clr_btn)
        root.add_widget(btn_row)

        self.status = MDLabel(text="", halign="center")
        root.add_widget(self.status)
        self.add_widget(root)

    def _on_add(self, *_):
        try:
            amt = float(self.amount.text)
        except Exception:
            self.status.text = t("ENTER_AMOUNT")
            return
        tx_id = self.usecases.quick_add_tx(amount=amt, category_id=1)
        self.amount.text = ""
        self.status.text = t("RECORDED_TX", id=tx_id)
        self.switch_tab(t("TAB_HOME"))
