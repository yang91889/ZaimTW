# features/add/tabs/manual/tx_detail/screen_tx_detail.py
from __future__ import annotations

from typing import Callable, Dict, Any, Optional

from kivy.metrics import dp, sp
from kivy.uix.screenmanager import Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.modalview import ModalView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.menu import MDDropdownMenu

try:
    from kivymd.uix.toolbar import MDTopAppBar
except Exception:
    from kivymd.uix.toolbar import MDToolbar as MDTopAppBar

from core.i18n import t as _t

# 與 Manual 共用的元件 / 邏輯
from ..logic import ManualCalc
from ..currencies import CURRENCIES
from ..widgets.currency_chip import CurrencyChip
from ..widgets.num_keypad import NumKeypad


class TxDetailScreen(Screen):
    """
    詳情頁（Expense/Income/Transfer 通用）
    ctx: {
        "type": "expense" | "income" | "transfer",
        "currency": "JPY",
        "amount": 0.0,
        "category_path": "Expense > Category"
    }
    on_submit: Callable[[dict], None]
    """
    def __init__(self, ctx: Dict[str, Any], on_submit: Callable[[Dict[str, Any]], None], **kwargs):
        super().__init__(name="tx_detail", **kwargs)

        self._ctx = ctx or {}
        self._on_submit_cb = on_submit

        with self.canvas.before:
            Color(1, 1, 1, 1)               # 100% 不透明白
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._sync_screen_bg, pos=self._sync_screen_bg)

        # 狀態：幣別、小數位、計算器
        cur_code = self._ctx.get("currency", (CURRENCIES[0]["code"] if CURRENCIES else "JPY"))
        cur = next((c for c in CURRENCIES if c["code"] == cur_code),
                   {"code": cur_code, "symbol": "¥", "decimals": 0})
        self._currency = cur
        self.calc = ManualCalc(decimals=cur.get("decimals", 0))

        start_amt = float(self._ctx.get("amount", 0) or 0)
        self.calc.buffer = self._fmt_amount(start_amt)

        # Root
        self.root = MDBoxLayout(orientation="vertical")
        self.add_widget(self.root)

        self._build_appbar()
        self._build_header()
        self._build_form()
        self._build_bottom_bar()

        # 金額顯示
        self._sync_amount_from_calc()

    def _dismiss_overlays(self):
        """關掉本頁可能開啟的任何覆蓋層/彈出元件。"""
        # 1) 關數字鍵盤覆蓋層
        if getattr(self, "overlay", None):
            self._hide_editor()

        # 2) 關下拉選單（例如幣別選單）
        try:
            if getattr(self, "currency_menu", None):
                self.currency_menu.dismiss()
        except Exception:
            pass

        # 3) 安全網：若還有遺留的 ModalView（Kivy/KivyMD 的 scrim/遮罩）
        #    就把它們逐一 dismiss（或移除）
        for w in list(Window.children):
            if isinstance(w, ModalView):
                try:
                    w.dismiss()
                except Exception:
                    try:
                        Window.remove_widget(w)
                    except Exception:
                        pass

    def on_pre_leave(self, *args):
        # 離開畫面前，確保清掉所有覆蓋物
        self._dismiss_overlays()
        return super().on_pre_leave(*args)

    def _sync_screen_bg(self, *_):
        if hasattr(self, "_bg_rect") and self._bg_rect is not None:
            self._bg_rect.size = self.size
            self._bg_rect.pos = self.pos

    # ────────────────────── AppBar ──────────────────────
    def _build_appbar(self):
        title_map = {
            "expense": _t("EXPENSE_DETAIL") if _t else "Expense detail",
            "income":  _t("INCOME_DETAIL")  if _t else "Income detail",
            "transfer":_t("TRANSFER_DETAIL")if _t else "Transfer detail",
        }
        title = title_map.get(self._ctx.get("type", "expense"), "Expense detail")

        self.appbar = MDTopAppBar(
            title=title,
            left_action_items=[["arrow-left", lambda *_: self._go_back()]],
        )
        self.root.add_widget(self.appbar)

        from kivy.uix.widget import Widget
        self.root.add_widget(Widget(size_hint_y=None, height=dp(8)))

    def _go_back(self, *_):
        # 先把覆蓋物、菜單都關掉
        self._dismiss_overlays()

        sm = self.manager
        if sm:
            prev = getattr(sm, "previous", None)
            prev_name = prev() if callable(prev) else prev
            if prev_name and prev_name != self.name:
                sm.current = prev_name
            elif sm.screen_names:
                sm.current = sm.screen_names[0]
            if self in sm.screens:
                sm.remove_widget(self)
            return True

        # 非 ScreenManager 情境下保底
        try:
            if self.parent:
                self.parent.remove_widget(self)
        except Exception:
            pass
        return True

    # ────────────────────── Header（金額/幣別） ──────────────────────
    def _build_header(self):
        row = MDBoxLayout(orientation="horizontal", padding=(dp(16), dp(10), dp(16), dp(8)), size_hint_y=None, height=dp(72))
        # Currency chip（點擊可開選單）
        self.currency_chip = CurrencyChip(code=self._currency["code"], symbol=self._currency.get("symbol", "¥"))
        self.currency_chip.bind(on_release=lambda *_: self._open_currency_menu())

        # 右側金額
        self.lbl_amount = MDLabel(text="0", halign="right", font_size=sp(46),
                                  shorten=True, shorten_from="left")
        self.lbl_amount.bind(on_touch_down=lambda inst, touch:
                             self._open_editor() if self.lbl_amount.collide_point(*touch.pos) else None)

        row.add_widget(self.currency_chip)
        row.add_widget(self.lbl_amount)
        self.root.add_widget(row)

        self._build_currency_menu()

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
        cur = next((c for c in CURRENCIES if c["code"] == code),
                   {"code": code, "symbol": symbol, "decimals": 0})
        self._currency = cur
        self.currency_chip.set_currency(code, symbol)
        self.calc.decimals = cur.get("decimals", 0)
        # 以新位數重排顯示
        self.calc.buffer = self._fmt_amount(self.calc._to_float(self.calc.buffer))
        self._sync_amount_from_calc()
        if hasattr(self, "currency_menu"):
            self.currency_menu.dismiss()

    # ────────────────────── 表單（靜態/示意） ──────────────────────
    def _build_form(self):
        # Category 路徑（唯讀）
        self._row_category = self._build_line(icon="silverware-fork-knife",
                                              text=self._ctx.get("category_path", "Expense > Category"))
        self.root.add_widget(self._row_category)

        # Date & Time（示意）
        self._row_dt = self._build_line(icon="calendar", text=_t("DATE_TIME") if _t else "Date & Time")
        self.root.add_widget(self._row_dt)

        # From account（示意）
        self._row_from = self._build_line(icon="credit-card", text=_t("FROM_ACCOUNT") if _t else "From account")
        self.root.add_widget(self._row_from)

        # Merchant（示意）
        self._row_merchant = self._build_line(icon="store", text=_t("MERCHANT") if _t else "Merchant")
        self.root.add_widget(self._row_merchant)

        # Memo 區塊
        pad = MDBoxLayout(orientation="vertical", padding=(dp(16), dp(8), dp(16), dp(0)))
        pad.add_widget(MDLabel(text=_t("MEMO") if _t else "Memo", theme_text_color="Secondary"))
        self.memo = MDTextField(hint_text=_t("WRITE_A_NOTE") if _t else "Write a note...",
                                size_hint_x=1, mode="rectangle")
        pad.add_widget(self.memo)
        # tags（用輕量按鈕示意）
        tag_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), padding=(0, dp(8), 0, 0), size_hint_y=None, height=dp(40))
        for txt in ["# good buy", "# deal", "# treat"]:
            b = MDFlatButton(text=txt, disabled=True, size_hint=(None, None), height=dp(32))
            tag_row.add_widget(b)
        pad.add_widget(tag_row)

        # Include in reports
        reports_row = MDBoxLayout(orientation="horizontal", padding=(0, dp(8), 0, 0), size_hint_y=None, height=dp(40))
        reports_row.add_widget(MDLabel(text=_t("INCLUDE_IN_REPORTS") if _t else "Include in reports"))
        self.include_switch = MDSwitch(size_hint=(None, None), height=dp(32))
        reports_row.add_widget(self.include_switch)
        pad.add_widget(reports_row)
        Clock.schedule_once(lambda *_: setattr(self.include_switch, "active", True), 0)

        # Add photo 區（示意）
        photo_row = MDBoxLayout(orientation="horizontal", spacing=dp(12), padding=(0, dp(8), 0, 0),
                                size_hint_y=None, height=dp(56))
        photo_row.add_widget(MDIconButton(icon="image-plus"))
        photo_row.add_widget(MDLabel(text=_t("ADD_PHOTO") if _t else "Add photo", valign="center"))
        pad.add_widget(photo_row)

        self.root.add_widget(pad)

    def _build_line(self, icon: str, text: str) -> MDBoxLayout:
        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
                          padding=(dp(16), 0))
        row.add_widget(MDIconButton(icon=icon, disabled=True))
        lbl = MDLabel(text=text, halign="left")
        row.add_widget(lbl)

        # 底部分隔線
        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas.after:
            Color(0, 0, 0, 0.12)
            r = Rectangle(size=sep.size, pos=sep.pos)
        sep.bind(size=lambda *_: self._sync_rect(r, sep), pos=lambda *_: self._sync_rect(r, sep))

        wrap = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(52))
        wrap.add_widget(row)
        wrap.add_widget(sep)
        return wrap

    # ────────────────────── Bottom 「Add」 ──────────────────────
    def _build_bottom_bar(self):
        holder = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint=(1, 1))
        self.root.add_widget(holder)

        self.btn_submit = MDRaisedButton(text=_t("ADD") if _t else "Add",
                                         md_bg_color=(0.12, 0.65, 0.25, 1),
                                         size_hint=(1, None), height=dp(44))
        self.btn_submit.bind(on_release=lambda *_: self._submit())
        # 讓按鈕左右有點邊距
        pad = MDBoxLayout(orientation="horizontal", padding=(dp(12), dp(6), dp(12), dp(12)),
                          size_hint=(1, None), height=dp(66))
        pad.add_widget(self.btn_submit)
        holder.add_widget(pad)

    def _submit(self):
        payload = {
            "type": self._ctx.get("type", "expense"),
            "currency": self._currency["code"],
            "amount": float(self.calc._to_float(self.calc.buffer)),
            "category_path": self._ctx.get("category_path"),
            "memo": self.memo.text or "",
            "include": bool(self.include_switch.active),
        }
        try:
            if callable(self._on_submit_cb):
                self._on_submit_cb(payload)
        finally:
            self._go_back()

    # ────────────────────── 金額編輯（覆蓋，不透明） ──────────────────────
    def _open_editor(self):
        if getattr(self, "overlay", None):
            return
        self._build_amount_editor_overlay()
        self.add_widget(self.overlay)

    def _hide_editor(self, *_):
        if getattr(self, "overlay", None):
            self.remove_widget(self.overlay)
            self.overlay = None

    def _build_amount_editor_overlay(self):
        self.overlay = FloatLayout(size_hint=(1, 1))

        # 不透明白底（鋪滿）
        bg = Widget(size_hint=(1, 1))
        with bg.canvas.before:
            Color(1, 1, 1, 1)   # 不透明白
            rect = Rectangle(size=bg.size, pos=bg.pos)
        bg.bind(size=lambda *_: self._sync_rect(rect, bg), pos=lambda *_: self._sync_rect(rect, bg))
        self.overlay.add_widget(bg)

        # 底部數字鍵盤
        holder = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint=(1, 1))
        self.overlay.add_widget(holder)

        self.keypad = NumKeypad(
            on_digit=lambda s: (self.calc.input_digit(s), self._sync_amount_from_calc()),
            on_double_zero=lambda: (self.calc.input_double_zero(), self._sync_amount_from_calc()),
            on_dot=lambda: (self.calc.input_dot(), self._sync_amount_from_calc()),
            on_op=self._on_keypad_op,
            on_backspace=lambda: (self.calc.backspace(), self._sync_amount_from_calc()),
            on_ok_or_equals=self._on_keypad_ok_or_equals,
            on_category=lambda *_: None,
            show_category=False,
            ok_text="OK",
            size_hint=(1, None),
            height=dp(360),
        )
        holder.add_widget(self.keypad)

        # 右下角一個關閉小鈕（可選）
        close_wrap = AnchorLayout(anchor_x="right", anchor_y="bottom", size_hint=(1, 1),
                                  padding=(dp(8), dp(8), dp(12), dp(12)))
        btn_close = MDIconButton(icon="close", on_release=self._hide_editor)
        close_wrap.add_widget(btn_close)
        self.overlay.add_widget(close_wrap)

    def _on_keypad_ok_or_equals(self, *_):
        if self.calc.equals_mode:
            # 等號模式：先計算，清除高亮與等號狀態
            self.calc.equals()
            self.keypad.highlight_op(None)
            self.keypad.set_equals_mode(False)
            self._sync_amount_from_calc()
        else:
            # 非等號模式：視為「下一步」→ 關閉數字鍵盤
            self._hide_editor()

    def _on_keypad_op(self, op: str):
        self.calc.op_press(op)
        self.keypad.set_equals_mode(self.calc.equals_mode)  # 會把 OK 文字切成 '='
        sym_map = {"+": "+", "-": "−", "*": "×", "/": "÷"}
        self.keypad.highlight_op(sym_map.get(op))
        self._sync_amount_from_calc()

    # ────────────────────── utils ──────────────────────
    def _sync_amount_from_calc(self):
        self.lbl_amount.text = self.calc.buffer

    @staticmethod
    def _sync_rect(rect: Rectangle, widget: Widget):
        rect.size = widget.size
        rect.pos = widget.pos

    def _fmt_amount(self, v: float) -> str:
        s = f"{v:.{self.calc.decimals}f}"
        if float(s) == 0.0:
            s = f"{0:.{self.calc.decimals}f}"
        return s
