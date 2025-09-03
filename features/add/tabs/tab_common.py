from __future__ import annotations
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from data.dao import TxDao
from core.i18n import t
from .base import AddTabBase

class CommonTab(AddTabBase):
    def __init__(self, dao: TxDao, record_expense, **kwargs):
        super().__init__(title=t("ADD_TAB_COMMON"), record_expense=record_expense, **kwargs)
        self.dao = dao
        self.spacing = 8
        self.padding = [12, 12, 12, 12]
        self._sel = {"id": None, "name": "-"}

        # Frequent / Recent 切換（等分）
        switch_row = MDBoxLayout(size_hint_y=None, height=48, spacing=0)
        btn_freq = MDRaisedButton(text=t("FREQUENT"), size_hint_x=0.5)
        btn_recent = MDFlatButton(text=t("RECENT"), size_hint_x=0.5)
        switch_row.add_widget(btn_freq); switch_row.add_widget(btn_recent)
        self.add_widget(switch_row)

        # 已選 + 金額 + 新增
        form = MDBoxLayout(size_hint_y=None, height=56, spacing=8)
        self.selected = MDLabel(text=t("SELECTED_CATEGORY", name="-"), halign="left")
        self.amount = MDTextField(hint_text=t("AMOUNT"), input_filter="float", mode="fill", size_hint_x=0.4)
        form.add_widget(self.selected); form.add_widget(self.amount)
        form.add_widget(MDRaisedButton(text=t("ADD"), on_release=lambda *_: self._on_add()))
        self.add_widget(form)

        sv = ScrollView(); self.list = MDList(); sv.add_widget(self.list)
        self.add_widget(sv)

        btn_freq.on_release = lambda *_: self._load_freq()
        btn_recent.on_release = lambda *_: self._load_recent()
        self._load_freq()

    def _load_freq(self):
        self.list.clear_widgets()
        rows = self.dao.top_categories(limit=12)
        if not rows:
            self.list.add_widget(OneLineListItem(text=t("NO_DATA"))); return
        for r in rows:
            text = f"{r['category']}  (x{r['cnt']})"
            self.list.add_widget(OneLineListItem(text=text, on_release=lambda _w, r=r: self._choose(r)))

    def _load_recent(self):
        self.list.clear_widgets()
        rows = self.dao.latest(limit=15)
        if not rows:
            self.list.add_widget(OneLineListItem(text=t("NO_DATA"))); return
        for r in rows:
            text = f"{r['date']}  {r['category']}  {r['amount']} {r['currency']}"
            self.list.add_widget(OneLineListItem(text=text, on_release=lambda _w, r=r: self._duplicate(r)))

    def _choose(self, row: dict):
        self._sel = {"id": row["category_id"], "name": row["category"]}
        self.selected.text = t("SELECTED_CATEGORY", name=row["category"])

    def _on_add(self):
        try:
            amt = float(self.amount.text)
        except Exception:
            return
        cat_id = self._sel.get("id") or 1
        self.record_expense(amt, cat_id)
        self.amount.text = ""
        self._sel = {"id": None, "name": "-"}
        self.selected.text = t("SELECTED_CATEGORY", name="-")

    def _duplicate(self, row: dict):
        self.record_expense(float(row["amount"]), row.get("category_id") or 1)
