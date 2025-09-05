from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.core.window import Window
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

from .currencies import CURRENCIES
from .widgets.key import Key
from .widgets.currency_chip import CurrencyChip
from .widgets.category_chip import CategoryChip


class ManualTab(AddTabBase):
    """手動輸入頁（已拆分 widgets）：4x4 鍵盤 + 底列帽形 + 幣別可選。"""

    # ─────────────────────────────── init ───────────────────────────────
    def __init__(self, record_expense, **kwargs):
        super().__init__(title=_t("ADD_TAB_MANUAL"), **kwargs)
        self._record_expense_cb = record_expense

        # 計算狀態
        self._mode = "expense"
        self._buffer = "0"
        self._left = None
        self._op = None
        self._awaiting_rhs = False

        # 當前幣別
        self._currency = dict(CURRENCIES[0])

        # Root layout
        self._root = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        self.add_widget(self._root)

        # 1) 模式切換排
        self._build_modes_row()

        # 2) 幣別 + 金額
        self._build_amount_row()

        # 3) 鍵盤 + NEXT 覆蓋
        self._build_keypad_stack()

        # 幣別選單
        self._build_currency_menu()

        # 初始化
        self._set_mode("expense")
        self._render()
        self._relayout()
        self._place_next()

        # 自適應
        self.grid.bind(size=lambda *_: self._place_next(), pos=lambda *_: self._place_next())
        self.bind(size=lambda *_: self._place_next())
        Window.bind(on_resize=lambda *_: self._place_next())

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
        self.stack = FloatLayout(size_hint_y=1)
        self._root.add_widget(self.stack)

        self.grid = MDGridLayout(
            cols=4,
            spacing=(dp(12), dp(16)),
            padding=(dp(0), dp(8), dp(0), dp(8)),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.stack.add_widget(self.grid)

        # —— 運算符元件索引（用來高亮/取消高亮）——
        self.op_widgets = {}
        op_symbols = ("+", "−", "×", "÷")
        mark = list(self.theme_cls.primary_color)
        mark[3] = 0.22  # 高亮圓形透明度

        keys = [
            ("7", self._tap_num), ("8", self._tap_num), ("9", self._tap_num), ("÷", self._tap_op),
            ("4", self._tap_num), ("5", self._tap_num), ("6", self._tap_num), ("×", self._tap_op),
            ("1", self._tap_num), ("2", self._tap_num), ("3", self._tap_num), ("−", self._tap_op),
            ("00", self._tap_num), ("0", self._tap_num), (".", self._tap_dot), ("+", self._tap_op),
        ]
        for text, handler in keys:
            scale = 0.42 if text not in op_symbols else 0.36
            k = Key(text=text,
                    on_tap=lambda s, h=handler: h(s),
                    scale=scale,
                    mark_rgba=mark)
            self.grid.add_widget(k)
            if text in op_symbols:
                self.op_widgets[text] = k

        # bottom row
        self.grid.add_widget(self._build_category_cell())
        self.grid.add_widget(Widget())
        self.grid.add_widget(Widget())
        back_cell = AnchorLayout(anchor_x="center", anchor_y="center")
        self.btn_back = MDIconButton(icon="backspace-outline",
                                     size_hint=(None, None), size=(dp(44), dp(44)))
        self.btn_back.bind(on_release=lambda *_: self._backspace())
        back_cell.add_widget(self.btn_back)
        self.grid.add_widget(back_cell)

        # NEXT / '=' overlay
        self.next_overlay = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(None, None))
        self.btn_next = MDRaisedButton(text=_t("NEXT"), size_hint=(None, None), height=dp(40))
        if hasattr(self.btn_next, "adaptive_width"):
            self.btn_next.adaptive_width = False   # 關掉自動依文字調寬
        self.btn_next.min_width = dp(140)
        self.btn_next.bind(on_release=self._on_next_pressed)  # ← 改成統一入口
        self.next_overlay.add_widget(self.btn_next)
        self.stack.add_widget(self.next_overlay)

        self._equals_mode = False  # 目前是否顯示 '='

    def _highlight_op(self, symbol: str | None):
        """圓形高亮對應的運算符；symbol=None 則全部取消。"""
        for sym, widget in self.op_widgets.items():
            widget.selected = (sym == symbol) if symbol else False

    def _set_equals_mode(self, on: bool):
        self._equals_mode = bool(on)
        self.btn_next.text = "=" if self._equals_mode else _t("NEXT")
        # 文字更新會先改變內部 texture，下一幀再強制回到我們的寬度
        Clock.schedule_once(self._size_next_button, 0)

    def _on_next_pressed(self, *_):
        if self._equals_mode:
            self._equals()
        else:
            self._commit()

    def _build_category_cell(self):
        wrap = AnchorLayout(anchor_x="center", anchor_y="center")
        self.cat_chip = CategoryChip(text=_t("CATEGORY"))
        self.cat_chip.bind(on_release=lambda *_: self._tap_num("00"))
        wrap.add_widget(self.cat_chip)
        self._update_category_chip_for_mode()
        return wrap
    
    def _update_category_chip_for_mode(self):
        """
        依目前 self._mode 調整左下角 Category 的圖示與文字：
        - 支出 expense：餐具圖示 +「CATEGORY」
        - 收入 income ：收入圖示（cash-plus）+「CATEGORY」
        - 轉帳 transfer：錢包圖示 +「選擇帳號」
        """
        mode = self._mode
        if mode == "expense":
            icon = "silverware-fork-knife"
            text = _t("CATEGORY")
        elif mode == "income":
            icon = "cash-plus"
            text = _t("CATEGORY")
        else:  # transfer
            # 若 'wallet' 不可用，改 'wallet-outline' 或 'bank-transfer'
            icon = "wallet"
            text = "ACCOUNTS"  # 不用 i18n，因為轉帳通常是跨國語系

        # 動態套用
        if hasattr(self, "cat_chip"):
            self.cat_chip.set_icon(icon)
            self.cat_chip.set_text(text)

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
        self._currency = {"code": code, "symbol": symbol}
        self.currency_chip.set_currency(code, symbol)
        if hasattr(self, "currency_menu"):
            self.currency_menu.dismiss()

    # ─────────────────────────── layout helpers ─────────────────────────
    def _place_next(self):
        grid = self.grid
        cols, rows = 4, 5

        sp = grid.spacing
        sx, sy = (sp if isinstance(sp, (list, tuple)) else (sp, sp))
        pad = grid.padding
        if isinstance(pad, (list, tuple)) and len(pad) == 4:
            pl, pt, pr, pb = pad
        else:
            pl = pt = pr = pb = float(pad or 0)

        cw = (grid.width  - pl - pr - sx * (cols - 1)) / cols if cols else 0
        ch = (grid.height - pb - pt - sy * (rows - 1)) / rows if rows else 0

        y = grid.y + pb
        x = grid.x + pl + (cw + sx) * 1  # 第二欄起、橫跨兩欄

        self.next_overlay.pos = (x, y)
        self.next_overlay.size = (cw * 2 + sx, ch)
        self.btn_next.width = min(dp(420), max(dp(140), self.next_overlay.width * 0.92))
        self.btn_next.height = min(dp(56), max(dp(36), self.next_overlay.height * 0.70))

        # 同步左下「分類/Accounts」chip 的寬度為一個 cell 的寬
        if hasattr(self, "cat_chip"):
            self.cat_chip.width = cw

    def _relayout(self, *_):
        H = float(self.height)

        def clamp(v, lo, hi): return max(lo, min(hi, v))

        top_bot_pad = clamp(H * 0.02, dp(6), dp(24))
        self._root.padding = (dp(16), top_bot_pad, dp(16), top_bot_pad)

        block_gap = clamp(H * 0.015, dp(4), dp(18))
        self._root.spacing = block_gap

        self.row_modes.height  = clamp(H * 0.075, dp(40), dp(64))
        self.row_amount.height = clamp(H * 0.10,  dp(58), dp(92))

        key_gap = clamp(H * 0.02, dp(8), dp(22))
        self.grid.spacing = (dp(12), key_gap)
        self.grid.padding = (dp(0), key_gap * 0.5, dp(0), key_gap * 0.5)

        self._fit_amount_font()
        self._place_next()

    def _fit_amount_font(self):
        base = min(self.width, self.height)
        fs = max(sp(28), min(sp(64), base * 0.075))
        self.lbl_amount.font_size = fs

    # ────────────────────────── mode & compute ─────────────────────────
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

        self._update_category_chip_for_mode()

    # --- 修改：統一由 _render 來套用規範化 ---
    def _render(self):
        self._buffer = self._normalize_buffer(self._buffer)
        self.lbl_amount.text = self._buffer

    # --- 新增：將 self._buffer 規範化 ---
    def _normalize_buffer(self, s: str, *, for_backspace: bool = False) -> str:
        s = (s or "").strip()
        # 只有符號或空字串 → 0
        if s in ("", "-", "+"):
            return "0"
        # 僅在退格情境下才把尾巴孤單的小數點收掉（1. -> 1）
        if for_backspace and s.endswith("."):
            s = s[:-1] or "0"

        neg = s.startswith("-")
        body = s[1:] if neg else s

        if "." in body:
            int_part, frac = body.split(".", 1)
            int_part = (int_part.lstrip("0") or "0")
            # 不在退格時：允許處於 0. 的中間輸入狀態
            if not for_backspace and body.endswith("."):
                body = int_part + "."
            else:
                body = int_part + ("." + frac if frac != "" else "")
        else:
            body = body.lstrip("0") or "0"

        if body == "0":
            neg = False  # -0 → 0

        return ("-" if neg else "") + body

    # —— 新增：等號計算 ————————————————————————————————————————
    def _equals(self):
        cur = self._parse()
        if self._op is None or self._left is None:
            self._set_equals_mode(False)
            self._highlight_op(None)
            return
        res = self._calc(self._left, cur, self._op)
        self._buffer = self._format_amount(res)
        self._left, self._op = None, None
        self._awaiting_rhs = False
        self._render()
        self._highlight_op(None)
        self._set_equals_mode(False)

    def _size_next_button(self, *_):
        # 依 overlay 大小固定寬高，避免被文字長度影響
        w = self.next_overlay.width * 0.92
        h = self.next_overlay.height * 0.70
        self.btn_next.width  = min(dp(420), max(dp(140), w))
        self.btn_next.height = min(dp(56),  max(dp(36),  h))

    # --- 修改：數字鍵 ---
    def _tap_num(self, token: str):
        if self._awaiting_rhs:
            self._buffer = "0" if token == "00" else token
            self._awaiting_rhs = False
        else:
            if self._buffer == "0" and token not in (".", "00"):
                self._buffer = token
            elif token == "00":
                self._buffer += "00"
            else:
                self._buffer += token
        self._render()

    # --- 修改：小數點鍵 ---
    def _tap_dot(self, _):
        b = self._buffer or "0"
        # 已經有小數點就不再加
        if "." in b:
            return
        # 空字串或只有 +/- 時，補成 0.
        if b in ("", "-", "+"):
            b = "0"
        # 變成 0. 或 n.
        self._buffer = b + "."
        self._render()

    def _tap_op(self, sym: str):
        op = {"+": "+", "−": "-", "×": "*", "÷": "/"}[sym]

        cur = self._parse()

        if self._op is None:
            # 第一次按運算符：把左運算元定下來
            self._left = cur
        elif not self._awaiting_rhs:
            # 已有左運算元且右運算元已輸入 → 先把舊運算算完
            self._left = self._calc(self._left, cur, self._op)
            self._buffer = self._format_amount(self._left)
            self._render()
        else:
            # 正在等右運算元（使用者只是換了一個運算子）→ 什麼也不算
            pass

        self._op = op
        self._awaiting_rhs = True            # 進入等右運算元狀態
        # 顯示仍維持 left，不把畫面改成 "0"
        self._highlight_op(sym)
        self._set_equals_mode(True)

    def _backspace(self):
        b = self._buffer or "0"
        if len(b) <= 1:
            self._buffer = "0"
        else:
            b = b[:-1]
            self._buffer = self._normalize_buffer(b, for_backspace=True)
        self._render()

    def _parse(self) -> float:
        try:
            return float(self._buffer)
        except Exception:
            return 0.0

    def _calc(self, a: float, b: float, op: str) -> float:
        try:
            if op == "+": return a + b
            if op == "-": return a - b
            if op == "*": return a * b
            if op == "/": return a / b if b != 0 else a
        except Exception:
            pass
        return b

    def _apply_pending(self, op_switch: str | None):
        cur = self._parse()
        if self._op is None:
            self._left = cur
        else:
            self._left = self._calc(self._left, cur, self._op)
            self._buffer = self._format_amount(self._left)
            self._render()
        self._op = op_switch
        self._buffer = "0"

    # 送出後重置狀態
    def _commit(self):
        val = self._parse()
        if self._op is not None and self._left is not None:
            val = self._calc(self._left, val, self._op)
        amount = abs(val)
        sign = -1 if self._mode == "expense" else 1
        final = amount * sign
        if callable(self._record_expense_cb):
            self._record_expense_cb(final, category_id=1)
        self._buffer, self._left, self._op = "0", None, None
        self._awaiting_rhs = False
        self._highlight_op(None)
        self._set_equals_mode(False)
        self._render()

    def _format_amount(self, v: float) -> str:
        if abs(v) < 1e-12:
            v = 0.0
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        if s in ("-0", "-0.", "-0.0"):
            s = "0"
        return s or "0"
