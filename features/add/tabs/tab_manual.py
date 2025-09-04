# features/add/tabs/tab_manual.py
from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

from .tab_base import AddTabBase
from core.i18n import t as _t


# 可挑的幣別（之後你要加/改，直接編這裡）
CURRENCIES = [
    {"code": "JPY", "symbol": "¥"},
    {"code": "TWD", "symbol": "NT$"},
    {"code": "USD", "symbol": "$"},
    {"code": "EUR", "symbol": "€"},
    {"code": "CNY", "symbol": "¥"},
    {"code": "HKD", "symbol": "HK$"},
    {"code": "KRW", "symbol": "₩"},
]


# ──────────────────────────────────────────────────────────────────────────────
# 無邊框可點擊的大字鍵
# ──────────────────────────────────────────────────────────────────────────────
class Key(ButtonBehavior, MDLabel):
    scale = NumericProperty(0.42)  # 依 cell 尺寸比例

    def __init__(self, text: str, on_tap, scale: float | None = None, **kw):
        super().__init__(**kw)
        self.text = text
        self.halign = "center"
        self.valign = "center"
        self.theme_text_color = "Primary"
        if scale is not None:
            self.scale = scale
        self.bind(size=lambda *_: self._fit())
        self.on_tap = on_tap

    def _fit(self):
        s = min(self.width, self.height) * self.scale
        self.font_size = max(sp(18), s)
        self.text_size = (self.width, self.height)

    def on_release(self):
        if callable(self.on_tap):
            self.on_tap(self.text)


# ──────────────────────────────────────────────────────────────────────────────
# 左側幣別卡（兩行：符號大、代碼小）＋可點開選單
# ──────────────────────────────────────────────────────────────────────────────
class CurrencyChip(ButtonBehavior, MDBoxLayout):
    def __init__(self, code: str, symbol: str, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.padding = (0, 0, 0, 0)
        self.spacing = dp(0)
        self.size_hint_x = None
        self.width = dp(72)

        self.lbl_symbol = MDLabel(text=symbol, halign="left", valign="bottom", font_size=sp(20))
        self.lbl_code   = MDLabel(text=code,   halign="left", valign="top",    font_size=sp(14), opacity=0.85)

        self.add_widget(self.lbl_symbol)
        self.add_widget(self.lbl_code)

    @property
    def code(self):
        return self.lbl_code.text

    @property
    def symbol(self):
        return self.lbl_symbol.text

    def set_currency(self, code: str, symbol: str):
        self.lbl_symbol.text = symbol
        self.lbl_code.text = code


# ──────────────────────────────────────────────────────────────────────────────
# Manual Tab（4×5 網格；NEXT 覆蓋在最底列的中間兩格）
# ──────────────────────────────────────────────────────────────────────────────
class ManualTab(AddTabBase):
    def __init__(self, record_expense, **kwargs):
        super().__init__(title=_t("ADD_TAB_MANUAL"), **kwargs)
        self._record_expense_cb = record_expense

        # 狀態（四則）
        self._mode = "expense"
        self._buffer = "0"
        self._left = None
        self._op = None

        # 目前幣別
        self._currency = dict(CURRENCIES[0])  # 預設第一個（JPY/¥）

        # ---- 整體容器：上(模式) / 中(幣別+數值) / 下(浮動疊加的數字網格) ----
        self._root = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        self.add_widget(self._root)

        # 1) 模式切換
        self.row_modes = MDGridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(44))
        self.btn_exp = MDRaisedButton(text=_t("EXPENSE"), on_release=lambda *_: self._set_mode("expense"))
        self.btn_inc = MDFlatButton(text=_t("INCOME"),  on_release=lambda *_: self._set_mode("income"))
        self.btn_trf = MDFlatButton(text=_t("TRANSFER"), on_release=lambda *_: self._set_mode("transfer"))
        for b in (self.btn_exp, self.btn_inc, self.btn_trf):
            b.size_hint_x = 1
            self.row_modes.add_widget(b)
        self._root.add_widget(self.row_modes)

        # 2) 幣別 + 右側金額（幣別用 CurrencyChip，可點開選單）
        self.row_amount = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(64))
        self.currency_chip = CurrencyChip(code=self._currency["code"], symbol=self._currency["symbol"])
        self.currency_chip.bind(on_release=lambda *_: self._open_currency_menu())
        self.lbl_amount = MDLabel(text="0", halign="right", font_size=sp(46), shorten=True, shorten_from="left")
        self.lbl_amount.bind(size=lambda *_: self._fit_amount_font())
        self.row_amount.add_widget(self.currency_chip)
        self.row_amount.add_widget(self.lbl_amount)
        self._root.add_widget(self.row_amount)

        # 3) 數字網格 + NEXT 覆蓋（Stack）
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

        keys = [
            ("7", self._tap_num), ("8", self._tap_num), ("9", self._tap_num), ("÷", self._tap_op),
            ("4", self._tap_num), ("5", self._tap_num), ("6", self._tap_num), ("×", self._tap_op),
            ("1", self._tap_num), ("2", self._tap_num), ("3", self._tap_num), ("−", self._tap_op),
            ("00", self._tap_num), ("0", self._tap_num), (".", self._tap_dot), ("+", self._tap_op),
        ]
        for text, handler in keys:
            scale = 0.42 if text not in ("+", "−", "×", "÷") else 0.36
            self.grid.add_widget(Key(text=text, on_tap=lambda s, h=handler: h(s), scale=scale))

        # 最底列： [分類] [空] [空] [退格]  （中間兩格留白給 NEXT 覆蓋）
        cat_cell = AnchorLayout(anchor_x="center", anchor_y="center")
        self.btn_cat = MDIconButton(icon="silverware-fork-knife", size_hint=(None, None), size=(dp(44), dp(44)))
        self.btn_cat.bind(on_release=lambda *_: self._tap_num("00"))
        cat_cell.add_widget(self.btn_cat)
        self.grid.add_widget(cat_cell)

        self.grid.add_widget(Widget())  # 空
        self.grid.add_widget(Widget())  # 空

        back_cell = AnchorLayout(anchor_x="center", anchor_y="center")
        self.btn_back = MDIconButton(icon="backspace-outline", size_hint=(None, None), size=(dp(44), dp(44)))
        self.btn_back.bind(on_release=lambda *_: self._backspace())
        back_cell.add_widget(self.btn_back)
        self.grid.add_widget(back_cell)

        # NEXT 覆蓋在底列中間兩格
        self.next_overlay = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(None, None))
        self.btn_next = MDRaisedButton(text=_t("NEXT"), size_hint=(None, None), height=dp(40))
        self.btn_next.bind(on_release=lambda *_: self._commit())
        self.next_overlay.add_widget(self.btn_next)
        self.stack.add_widget(self.next_overlay)

        self.grid.bind(size=lambda *_: self._place_next(), pos=lambda *_: self._place_next())
        self.bind(size=lambda *_: self._place_next())
        Window.bind(on_resize=lambda *_: self._place_next())

        # 幣別選單
        self._build_currency_menu()

        # 初始狀態
        self._set_mode("expense")
        self._render()
        self._relayout()
        self._place_next()

    # ─── 幣別選單 ───────────────────────────────────────────────────────────
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

    # ─── 讓 NEXT 橫跨最底列中間兩格 ─────────────────────────────────────────
    def _place_next(self):
        grid = self.grid
        cols = 4
        rows = 5

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
        x = grid.x + pl + (cw + sx) * 1

        self.next_overlay.pos = (x, y)
        self.next_overlay.size = (cw * 2 + sx, ch)
        self.btn_next.width = min(dp(420), max(dp(140), self.next_overlay.width * 0.92))
        self.btn_next.height = min(dp(56), max(dp(36), self.next_overlay.height * 0.70))

    # ─── 版面自適應 ─────────────────────────────────────────────────────────
    def _relayout(self, *_):
        H = float(self.height)

        def clamp(v, lo, hi):
            return max(lo, min(hi, v))

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

    # ─── 模式 / 顯示 / 計算 ────────────────────────────────────────────────
    def _set_mode(self, m: str):
        self._mode = m
        self.btn_exp.disabled = m == "expense"
        self.btn_inc.disabled = m == "income"
        self.btn_trf.disabled = m == "transfer"

    def _render(self):
        self.lbl_amount.text = self._buffer

    def _tap_num(self, token: str):
        if self._buffer == "0" and token not in (".", "00"):
            self._buffer = token
        elif token == "00":
            self._buffer += "00"
        else:
            self._buffer += token
        self._render()

    def _tap_dot(self, _):
        if "." not in self._buffer:
            self._buffer += "." if self._buffer else "0."
            self._render()

    def _tap_op(self, sym: str):
        op = {"+": "+", "−": "-", "×": "*", "÷": "/"}[sym]
        self._apply_pending(op_switch=op)

    def _backspace(self):
        if len(self._buffer) <= 1:
            self._buffer = "0"
        else:
            self._buffer = self._buffer[:-1]
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

    def _commit(self):
        val = self._parse()
        if self._op is not None and self._left is not None:
            val = self._calc(self._left, val, self._op)
        amount = abs(val)
        sign = -1 if self._mode == "expense" else 1
        final = amount * sign
        # TODO: 若你的 usecase/DAO 支援幣別，這裡可以把 self._currency["code"] 一起傳下去
        if callable(self._record_expense_cb):
            self._record_expense_cb(final, category_id=1)
        self._buffer, self._left, self._op = "0", None, None
        self._render()

    @staticmethod
    def _format_amount(v: float) -> str:
        s = f"{v:.2f}"
        s = s.rstrip("0").rstrip(".")
        return s or "0"
