# features/add/tabs/manual/view.py
from __future__ import annotations

from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock

from kivy.uix.screenmanager import ScreenManager, SlideTransition
from .categories.data import CATEGORIES as DEFAULT_CATEGORIES
from .categories.screen_category import CategorySelectScreen

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

from ..tab_base import AddTabBase
from core.i18n import t as _t

from .logic import ManualCalc
from .currencies import CURRENCIES
from .widgets.key import Key
from .widgets.currency_chip import CurrencyChip
from .widgets.category_chip import CategoryChip


class ManualTab(AddTabBase):
    """
    手動輸入頁：4x4 鍵盤 + 最底列「帽形」(Category/空/空/Backspace)，
    NEXT 覆蓋底列中間兩格；幣別可選且自動決定小數位。
    """

    # ─────────────────────────────── init ───────────────────────────────
    def __init__(self, record_expense, **kwargs):
        super().__init__(title=_t("ADD_TAB_MANUAL"), **kwargs)
        self._record_expense_cb = record_expense

        # 狀態（依幣別小數位決定顯示）
        self._mode = "expense"
        self._currency = dict(CURRENCIES[0])  # e.g. {"code":"JPY","symbol":"¥","decimals":0}
        self.calc = ManualCalc(decimals=self._currency.get("decimals", 0))

        # Root
        self._root = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        self.add_widget(self._root)

        # 1) 模式
        self._build_modes_row()

        # 2) 幣別 + 金額
        self._build_amount_row()

        # 3) 鍵盤 + NEXT 覆蓋
        self._build_keypad_stack()

        # 4) 幣別選單
        self._build_currency_menu()

        # 初始化
        self._set_mode("expense")
        self._render()
        self._relayout()
        self._place_next()

        # 自適應（格子或視窗變動時重新定位 NEXT）
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

        # 4x4 keypad
        self.grid = MDGridLayout(
            cols=4,
            spacing=(dp(12), dp(16)),
            padding=(dp(0), dp(8), dp(0), dp(8)),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.stack.add_widget(self.grid)

        # —— 運算符用於高亮 —— #
        self.op_widgets = {}
        op_symbols = ("+", "−", "×", "÷")
        mark = list(self.theme_cls.primary_color)
        mark[3] = 0.22  # 高亮圓形透明度

        keys = [
            ("7", self._tap_num), ("8", self._tap_num), ("9", self._tap_num), ("÷", self._tap_op),
            ("4", self._tap_num), ("5", self._tap_num), ("6", self._tap_num), ("×", self._tap_op),
            ("1", self._tap_num), ("2", self._tap_num), ("3", self._tap_num), ("−", self._tap_op),
            ("00", self._tap_double_zero), ("0", self._tap_num), (".", self._tap_dot), ("+", self._tap_op),
        ]
        for text, handler in keys:
            scale = 0.42 if text not in op_symbols else 0.36
            k = Key(text=text, on_tap=lambda s, h=handler: h(s), scale=scale, mark_rgba=mark)
            self.grid.add_widget(k)
            if text in op_symbols:
                self.op_widgets[text] = k

        # 底列： [分類] [空] [空] [退格]
        self.grid.add_widget(self._build_category_cell())
        self.grid.add_widget(Widget())
        self.grid.add_widget(Widget())
        back_cell = AnchorLayout(anchor_x="center", anchor_y="center")
        self.btn_back = MDIconButton(icon="backspace-outline",
                                     size_hint=(None, None), size=(dp(44), dp(44)))
        self.btn_back.bind(on_release=self._tap_backspace)
        back_cell.add_widget(self.btn_back)
        self.grid.add_widget(back_cell)

        # NEXT / '=' 覆蓋在底列中間兩格
        self.next_overlay = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(None, None))
        self.btn_next = MDRaisedButton(text=_t("NEXT"), size_hint=(None, None), height=dp(40))
        self.btn_next.bind(on_release=self._on_next_pressed)
        self.next_overlay.add_widget(self.btn_next)
        self.stack.add_widget(self.next_overlay)

        self._equals_mode = False  # 目前是否顯示 '='

    def _build_category_cell(self):
        wrap = AnchorLayout(anchor_x="center", anchor_y="center")
        self.cat_chip = CategoryChip(text=_t("CATEGORY"))  # 預設「類別」
        self.cat_chip.bind(on_release=self._open_category_page)
        wrap.add_widget(self.cat_chip)
        return wrap
    
    def _open_category_page(self, *_):
        sm = self._find_screen_manager()
        if not sm:
            return  # 找不到 ScreenManager 就先不開，通常你的 root 會是 SM

        screen = CategorySelectScreen(
            name="category_select",
            on_pick=self._on_category_selected,
            categories=DEFAULT_CATEGORIES,
            recents=getattr(self, "_recent_category_ids", [101, 102, 103]),  # 先給幾個常用
        )
        sm.add_widget(screen)
        # 優雅換頁
        old = sm.transition
        sm.transition = SlideTransition(direction="left", duration=0.18)
        sm.current = "category_select"
        sm.transition = old

    def _on_category_selected(self, cat: dict):
        # 記住選擇
        self._selected_category_id = cat["id"]
        self._recent_category_ids = [cat["id"]] + [i for i in getattr(self, "_recent_category_ids", []) if i != cat["id"]]
        self._recent_category_ids = self._recent_category_ids[:8]

        # 更新 chip 視覺
        try:
            self.cat_chip._icon.icon = cat.get("icon", "shape")
            self.cat_chip._label.text = cat["name"]
        except Exception:
            pass
        self._render()

    def _find_screen_manager(self):
        w = self
        from kivy.uix.screenmanager import ScreenManager
        while w is not None and not isinstance(w, ScreenManager):
            w = w.parent
        return w

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
        # 切幣別：更新 chip、顯示小數位、重排現值
        cur = next((c for c in CURRENCIES if c["code"] == code), {"code": code, "symbol": symbol, "decimals": 0})
        self._currency = cur
        self.currency_chip.set_currency(code, symbol)
        self.calc.decimals = cur.get("decimals", 0)
        # 以新位數重排 buffer
        self._render()
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

        # 固定 NEXT/＝ 的大小（避免文字長度影響）
        self._size_next_button()

        # 讓 category chip 視覺寬度對齊左下那格
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

        # 切換模式時，同步左下角圖示與文字
        # 支出: 餐具 + CATEGORY；收入: income 圖示 + CATEGORY；轉帳: 錢包 + "Accounts"
        ICONS_BY_MODE = {
            "expense": ("silverware-fork-knife", _t("CATEGORY")),
            "income":  ("cash-plus",             _t("CATEGORY")),
            "transfer":("wallet",                _t("ACCOUNTS")),  # 你說用英文就好
        }
        icon, caption = ICONS_BY_MODE.get(m, ("silverware-fork-knife", _t("CATEGORY")))
        try:
            # 直接設定 CategoryChip 的內部控件
            self.cat_chip._icon.icon = icon
            self.cat_chip._label.text = caption
        except Exception:
            pass

    def _highlight_op(self, symbol: str | None):
        """圓形高亮對應的運算符；symbol=None 則全部取消。"""
        for sym, widget in self.op_widgets.items():
            # 需要你的 widgets/key.py 支援 selected 屬性與 mark_rgba
            try:
                widget.selected = (sym == symbol) if symbol else False
            except Exception:
                pass

    def _set_equals_mode(self, on: bool):
        self._equals_mode = bool(on)
        self.btn_next.text = "=" if self._equals_mode else _t("NEXT")
        Clock.schedule_once(lambda *_: self._size_next_button(), 0)

    def _size_next_button(self, *_):
        # 依 overlay 大小固定寬高，避免被文字長度影響
        w = self.next_overlay.width * 0.92
        h = self.next_overlay.height * 0.70
        self.btn_next.width  = min(dp(420), max(dp(140), w))
        self.btn_next.height = min(dp(56),  max(dp(36),  h))

    # ────────────────────────── render & events ────────────────────────
    def _render(self):
        self.lbl_amount.text = self.calc.buffer

    def _on_next_pressed(self, *_):
        if self._equals_mode:
            self.calc.equals()
            self._highlight_op(None)
            self._set_equals_mode(False)
            self._render()
        else:
            self._commit()

    # 數字 / 00 / . / 運算子 / 退格
    def _tap_num(self, n, *_):
        self.calc.input_digit(str(n))
        self._refresh_amount_label()
    
    def _tap_double_zero(self, *_):
        self.calc.input_double_zero()
        self._refresh_amount_label()

    def _tap_dot(self, *_):
        self.calc.input_dot()
        self._refresh_amount_label()

    def _tap_op(self, sym: str):
        op = {"+": "+", "−": "-", "×": "*", "÷": "/"}[sym]
        self.calc.op_press(op)
        self._highlight_op(sym)                 # 視覺高亮
        self._set_equals_mode(self.calc.equals_mode)
        self._render()

    def _refresh_amount_label(self):
        # 這裡請直接顯示 buffer
        self.lbl_amount.text = self.calc.buffer

    def _tap_backspace(self, *_):
        self.calc.backspace()
        self._refresh_amount_label()

    def _tap_next_or_equals(self, *_):
        if self.calc.equals_mode:
            shown = self.calc.equals()  # 這裡會用 _fmt_amount(decimals)
        else:
            shown = self.calc._fmt_amount(float(self.calc.buffer or "0"))
        self.lbl_amount.text = shown
        # 然後進入下一步（類別/帳戶等頁面）
    
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
            # TODO: 若你的 usecase/DAO 支援幣別，可把 self._currency["code"] 一起傳下去
            self._record_expense_cb(final, category_id=1)

        # 重置狀態 / 視覺
        self.calc.reset()
        self._highlight_op(None)
        self._set_equals_mode(False)
        self._render()
