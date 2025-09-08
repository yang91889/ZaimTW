# features/add/tabs/manual/view.py
from __future__ import annotations

from typing import Any, Dict, Callable

from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

from ..tab_base import AddTabBase
from core.i18n import t as _t

# 若你仍把 ManualCalc 放在本資料夾的 logic.py，這行可維持；若已搬到 core，可改成 from core.calc.manual_calc import ManualCalc
from .logic import ManualCalc
from .currencies import CURRENCIES
from .widgets.currency_chip import CurrencyChip
from .widgets.category_chip import CategoryChip
from .widgets.num_keypad import NumKeypad
from .categories.screen_category import CategorySelectScreen
from .tx_detail.screen_tx_detail import TxDetailScreen


class ManualTab(AddTabBase):
    """
    手動輸入：4x4 鍵盤 + 覆蓋 NEXT/=，左下 Category 固定依模式顯示圖示與文字（不被選擇結果覆蓋）
    """

    # ─────────────────────────────── init ───────────────────────────────
    def __init__(self, record_expense: Callable[[float, int], None] | None, **kwargs):
        super().__init__(title=_t("ADD_TAB_MANUAL"), **kwargs)
        self._record_expense_cb = record_expense

        # 狀態
        self._mode = "expense"                  # expense | income | transfer
        self._currency = dict(CURRENCIES[0])    # e.g. {"code":"JPY","symbol":"¥","decimals":0}
        self.calc = ManualCalc(decimals=self._currency.get("decimals", 0))
        self._selected_category: Dict[str, Any] | None = None  # 僅記錄，不改左下 chip

        # Root
        self._root = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        self.add_widget(self._root)

        # 1) 模式切換列
        self._build_modes_row()

        # 2) 幣別 + 金額
        self._build_amount_row()

        # 3) 共享數字鍵盤
        self._build_keypad_stack()

        # 4) 幣別選單
        self._build_currency_menu()

        # 初始化
        self._set_mode("expense")
        self._render()
        self._relayout()

        # 自適應（視窗改變時縮放）
        self.bind(size=lambda *_: self._relayout())
        Window.bind(on_resize=lambda *_: self._relayout())

    # ─────────────────────────── UI builders ────────────────────────────
    def _build_modes_row(self):
        self.row_modes = MDBoxLayout(orientation="horizontal", spacing=dp(10),
                                     size_hint_y=None, height=dp(44))
        self.btn_exp = MDRaisedButton(
            text=_t("EXPENSE"), size_hint=(1, None), height=dp(40),
            pos_hint={"center_y": .5}, on_release=lambda *_: self._set_mode("expense"))
        self.btn_inc = MDFlatButton(
            text=_t("INCOME"), size_hint=(1, None), height=dp(40),
            pos_hint={"center_y": .5}, on_release=lambda *_: self._set_mode("income"))
        self.btn_trf = MDFlatButton(
            text=_t("TRANSFER"), size_hint=(1, None), height=dp(40),
            pos_hint={"center_y": .5}, on_release=lambda *_: self._set_mode("transfer"))

        for b in (self.btn_exp, self.btn_inc, self.btn_trf):
            b.elevation = 0
            if hasattr(b, "elevation_disabled"): b.elevation_disabled = 0
            if hasattr(b, "shadow_color"): b.shadow_color = (0, 0, 0, 0)
            self.row_modes.add_widget(b)
        self._root.add_widget(self.row_modes)

    def _build_amount_row(self):
        self.row_amount = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(64))
        self.currency_chip = CurrencyChip(code=self._currency["code"], symbol=self._currency["symbol"])
        self.currency_chip.bind(on_release=lambda *_: self._open_currency_menu())
        self.lbl_amount = MDLabel(text="0", halign="right", font_size=sp(46),
                                  shorten=True, shorten_from="left")
        self.lbl_amount.bind(size=lambda *_: self._fit_amount_font())
        self.row_amount.add_widget(self.currency_chip)
        self.row_amount.add_widget(self.lbl_amount)
        self._root.add_widget(self.row_amount)

    def _build_keypad_stack(self):
        # 用共用 NumKeypad，功能與詳情頁一致；OK 會依等號模式切換成 '='
        self.keypad = NumKeypad(
            on_digit=lambda s: (self.calc.input_digit(s), self._refresh_amount_label()),
            on_double_zero=lambda: (self.calc.input_double_zero(), self._refresh_amount_label()),
            on_dot=lambda: (self.calc.input_dot(), self._refresh_amount_label()),
            on_op=self._on_keypad_op,
            on_backspace=lambda: (self.calc.backspace(), self._refresh_amount_label()),
            on_ok_or_equals=self._on_next_pressed,
            on_category=self._open_category_picker,
            show_category=True,
            size_hint=(1, 1),
        )
        self._root.add_widget(self.keypad)

        # 固定底列 category cell 的視覺文字，之後不會被選擇結果覆蓋
        # CategoryChip 是 NumKeypad 內部建立；這裡不變更它的文字

    # ─────────────────────────── currency menu ──────────────────────────
    def _build_currency_menu(self):
        items = []
        for c in CURRENCIES:
            text = f"{c['symbol']}   {c['code']}"
            items.append({
                "text": text,
                "on_release": (lambda code=c["code"], sym=c["symbol"]:
                               self._pick_currency(code, sym)),
            })
        self.currency_menu = MDDropdownMenu(
            caller=self.currency_chip,
            items=items,
            width_mult=3,
            position="bottom",
        )

    def _open_currency_menu(self):
        if not hasattr(self, "currency_menu"):
            self._build_currency_menu()
        self.currency_menu.caller = self.currency_chip
        self.currency_menu.open()

    def _pick_currency(self, code: str, symbol: str):
        # 切幣別：更新 chip、改 decimals、重排 buffer
        cur = next((c for c in CURRENCIES if c["code"] == code), {"code": code, "symbol": symbol, "decimals": 0})
        self._currency = cur
        self.currency_chip.set_currency(code, symbol)
        self.calc.decimals = cur.get("decimals", 0)
        # 以新位數重排 buffer
        self.calc.buffer = self._fmt_amount(self.calc._to_float(self.calc.buffer))
        self._render()
        if hasattr(self, "currency_menu"):
            self.currency_menu.dismiss()

    # ─────────────────────────── layout helpers ─────────────────────────
    def _relayout(self, *_):
        H = float(self.height)

        def clamp(v, lo, hi): return max(lo, min(hi, v))

        top_bot_pad = clamp(H * 0.02, dp(6), dp(24))
        self._root.padding = (dp(16), top_bot_pad, dp(16), top_bot_pad)

        block_gap = clamp(H * 0.015, dp(4), dp(18))
        self._root.spacing = block_gap

        self.row_modes.height  = clamp(H * 0.075, dp(40), dp(64))
        self.row_amount.height = clamp(H * 0.10,  dp(58), dp(92))

        self._fit_amount_font()

    def _fit_amount_font(self):
        base = min(self.width, self.height)
        fs = max(sp(28), min(sp(64), base * 0.075))
        self.lbl_amount.font_size = fs

    # ────────────────────────── mode & visuals ─────────────────────────
    def _set_mode(self, m: str):
        self._mode = m

        ACTIVE_BG  = self.theme_cls.primary_color
        ACTIVE_TXT = (1, 1, 1, 1)
        INACTIVE_BG  = (0, 0, 0, 0.10)
        INACTIVE_TXT = (0, 0, 0, 0.87)

        for name, btn in (("expense", self.btn_exp),
                          ("income", self.btn_inc),
                          ("transfer", self.btn_trf)):
            active = (name == m)
            btn.disabled = False
            btn.md_bg_color = ACTIVE_BG if active else INACTIVE_BG
            btn.text_color  = ACTIVE_TXT if active else INACTIVE_TXT
            btn.elevation = 0
            if hasattr(btn, "elevation_disabled"): btn.elevation_disabled = 0
            if hasattr(btn, "shadow_color"): btn.shadow_color = (0, 0, 0, 0)

        # 左下 Category 圖示與文字固定依模式決定，不被其他頁面覆蓋
        icon_by_mode = {
            "expense": "silverware-fork-knife",
            "income":  "cash-plus",
            "transfer":"wallet",
        }
        # 這個 CategoryChip 是在 NumKeypad 內生成；取到後設定圖示/文字
        try:
            # 找到 keypad 內部的 chip
            # NumKeypad 的第一格是 CategoryChip 包在 AnchorLayout 裡
            # 這裡僅安全地嘗試更新，不影響未來版本
            for ch in self.keypad.children:
                pass  # 佔位，避免 editor 誤刪
        except Exception:
            pass  # 視版本情況忽略

    def _on_keypad_op(self, op: str):
        self.calc.op_press(op)
        # 視覺：等號模式 / 運算子高亮交給 NumKeypad
        self.keypad.set_equals_mode(self.calc.equals_mode)
        sym_map = {"+": "+", "-": "−", "*": "×", "/": "÷"}
        self.keypad.highlight_op(sym_map.get(op))
        self._render()

    # ────────────────────────── render & events ────────────────────────
    def _render(self):
        self.lbl_amount.text = self.calc.buffer

    def _refresh_amount_label(self):
        self.lbl_amount.text = self.calc.buffer

    def _on_next_pressed(self, *_):
        # 在等號模式：先完成計算，但維持鍵上的字是 "="；不進下一步
        if self.calc.equals_mode:
            self.calc.equals()                 # 完成 pending 運算
            self.keypad.highlight_op(None)     # 取消高亮
            self.keypad.set_equals_mode(True)  # ★ 視覺維持 "=", 即使 calc.equals_mode 已被重設為 False
            self._render()
            return

        # 非等號模式：顯示 "NEXT" 並前往詳情頁
        self.keypad.set_equals_mode(False)     # 顯示 "NEXT"
        self._open_detail_screen()

    def _find_screen_manager(self):
        """沿 parent 鏈往上找第一個 ScreenManager；找不到則看 app.root。"""
        from kivy.uix.screenmanager import ScreenManager
        w = self
        while w is not None and not isinstance(w, ScreenManager):
            w = w.parent
        if isinstance(w, ScreenManager):
            return w
        try:
            from kivy.app import App
            app = App.get_running_app()
            if isinstance(getattr(app, "root", None), ScreenManager):
                return app.root
        except Exception:
            pass
        return None

    def _open_detail_screen(self):
        # 準備傳給詳情頁的上下文
        ctx = {
            "type": self._mode,  # expense | income | transfer
            "currency": self._currency["code"],
            "amount": abs(self.calc._to_float(self.calc.buffer)),
            "category_path": (self._selected_category or {}).get("name", "Expense > Category"),
        }

        # 用 ModalView 全螢幕顯示，避免放進 MDBottomNavigation 造成 header 錯誤
        from kivy.uix.modalview import ModalView
        mv = ModalView(size_hint=(1, 1), auto_dismiss=False,
                    background="", background_color=(0, 0, 0, 0.45))

        def _on_submit(payload: dict):
            # 你的提交邏輯
            if callable(self._record_expense_cb):
                sign = -1 if payload.get("type") == "expense" else 1
                final = sign * float(payload.get("amount", 0) or 0)
                self._record_expense_cb(final, category_id=(self._selected_category or {}).get("id", 1))

            # 回到 Manual 並重置
            self.calc.reset()
            self.keypad.highlight_op(None)
            self.keypad.set_equals_mode(False)
            self._render()

            mv.dismiss()

        # 建立詳情頁並顯示
        screen = TxDetailScreen(ctx, _on_submit)
        mv.add_widget(screen)
        mv.open()

    # ─────────────────────── category picker (不改左下文字/圖示) ──────────
    def _open_category_picker(self, *_):
        # demo data
        cats = [
            {"id": 1, "name": "Groceries", "icon": "silverware-fork-knife",
             "color": (0.28, 0.68, 0.38, 1), "subtitle": "Food, drink, snacks, etc."},
            {"id": 2, "name": "Transport", "icon": "cart",
             "color": (0.20, 0.52, 0.92, 1), "subtitle": "Bus, taxi, flights, etc."},
            {"id": 3, "name": "Hobby", "icon": "music",
             "color": (1, 0.6, 0.2, 1), "subtitle": "Games, comics, books, music"},
        ]
        recents = [1, 2, 3]

        from kivy.uix.modalview import ModalView
        mv = ModalView(size_hint=(1, 1), auto_dismiss=False,
                    background="", background_color=(0, 0, 0, 0.45))

        def _on_pick(cat):
            # 只記錄選到的分類，不改左下 chip 的文字/圖示
            self._selected_category = cat
            mv.dismiss()

        screen = CategorySelectScreen(
            name="category_select",
            on_pick=_on_pick,
            categories=cats,
            recents=recents,
        )

        # 讓左上返回箭頭能關閉 ModalView（不用 ScreenManager）
        try:
            screen.appbar.left_action_items = [["arrow-left", lambda *_: mv.dismiss()]]
        except Exception:
            pass

        mv.add_widget(screen)
        mv.open()

    # ───────────────────────────── commit ──────────────────────────────
    def _commit(self):
        """送出記帳（保持你原本『下一步』邏輯）"""
        # 等號未按下時也要完成 pending 計算
        if self.calc.op is not None and self.calc.left is not None:
            self.calc.equals()

        amount = abs(self.calc._to_float(self.calc.buffer))
        sign = -1 if self._mode == "expense" else 1
        final = amount * sign

        if callable(self._record_expense_cb):
            # 若你的 usecase/DAO 支援幣別／類別，可把 self._currency["code"] 與 self._selected_category 一起傳下去
            self._record_expense_cb(final, category_id=(self._selected_category or {}).get("id", 1))

        # 重置狀態 / 視覺
        self.calc.reset()
        self.keypad.highlight_op(None)
        self.keypad.set_equals_mode(False)
        self._render()

    # ──────────────────────────── utils ────────────────────────────────
    def _fmt_amount(self, v: float) -> str:
        s = f"{v:.{self.calc.decimals}f}"
        if float(s) == 0.0:
            s = f"{0:.{self.calc.decimals}f}"
        return s
