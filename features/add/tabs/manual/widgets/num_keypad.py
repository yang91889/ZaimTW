# features/add/tabs/manual/widgets/num_keypad.py
from __future__ import annotations

from typing import Callable, Optional

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton

# 你現有的小元件
from .key import Key
from .category_chip import CategoryChip


class NumKeypad(FloatLayout):
    """
    共用數字鍵盤（Manual 與詳情頁都用）
      - 底列： [Category] [  覆蓋 NEXT/=  ] [Backspace]
      - set_equals_mode(True) 時，NEXT 文字會變成 '='
    """

    def __init__(
        self,
        on_digit: Callable[[str], None],
        on_double_zero: Callable[[], None],
        on_dot: Callable[[], None],
        on_op: Callable[[str], None],
        on_backspace: Callable[[], None],
        on_ok_or_equals: Callable[[], None],
        on_category: Optional[Callable[[], None]] = None,
        *,
        show_category: bool = True,
        ok_text: str = "NEXT",
        **kwargs,
    ):
        super().__init__(**kwargs)

        # 回呼
        self._on_digit = on_digit
        self._on_double_zero = on_double_zero
        self._on_dot = on_dot
        self._on_op = on_op
        self._on_backspace = on_backspace
        self._on_ok = on_ok_or_equals
        self._on_category = on_category or (lambda: None)

        self._equals_mode = False
        self._ok_text_default = ok_text

        # 4x5 鍵盤網格
        self.grid = MDGridLayout(
            cols=4,
            spacing=(dp(12), dp(16)),
            padding=(dp(0), dp(8), dp(0), dp(8)),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self.grid)

        # 運算子高亮需要記住對應的 Key
        self.op_widgets = {}

        self._build_keys(show_category)
        self._build_next_overlay()

        # 位置/尺寸變更時重新擺放 NEXT/=
        self.bind(size=self._place_next, pos=self._place_next)
        self.grid.bind(size=self._place_next, pos=self._place_next)
        Window.bind(on_resize=lambda *_: self._place_next())

    # ────────────────────────── build ──────────────────────────
    def _build_keys(self, show_category: bool):
        op_symbols = ("+", "−", "×", "÷")

        def add(text: str, handler, scale: float = 0.42):
            k = Key(text=text, on_tap=lambda s, h=handler: h(s) if text not in op_symbols else h(text), scale=scale)
            self.grid.add_widget(k)
            if text in op_symbols:
                self.op_widgets[text] = k

        # 4x4 主鍵
        add("7", self._tap_digit)
        add("8", self._tap_digit)
        add("9", self._tap_digit)
        add("÷", self._tap_op, 0.36)

        add("4", self._tap_digit)
        add("5", self._tap_digit)
        add("6", self._tap_digit)
        add("×", self._tap_op, 0.36)

        add("1", self._tap_digit)
        add("2", self._tap_digit)
        add("3", self._tap_digit)
        add("−", self._tap_op, 0.36)

        add("00", lambda *_: self._fire(self._on_double_zero))
        add("0", self._tap_digit)
        add(".", lambda *_: self._fire(self._on_dot))
        add("+", self._tap_op, 0.36)

        # 底列： [Category] [空] [空] [Backspace]
        if show_category:
            self._add_category_cell()
        else:
            self.grid.add_widget(Widget())

        self.grid.add_widget(Widget())  # 這兩格留給 NEXT/=
        self.grid.add_widget(Widget())

        self._add_backspace_cell()

    def _add_category_cell(self):
        wrap = AnchorLayout(anchor_x="center", anchor_y="center")
        self.cat_chip = CategoryChip(text="Category")
        # 文字單行縮略
        try:
            self.cat_chip._label.shorten = True
            self.cat_chip._label.shorten_from = "right"
            self.cat_chip._label.halign = "center"
        except Exception:
            pass

        # a) 正常情況：chip 會發 on_release
        self.cat_chip.bind(on_release=lambda *_: self._fire(self._on_category))

        # b) 保險：若 a) 沒被觸發，點到整個 wrap 也視為點 chip
        def _maybe_fire(inst, touch):
            if inst.collide_point(*touch.pos):
                # 避免把鍵盤其它格的 up 事件也算進來
                if touch.grab_current in (None, inst, self.cat_chip):
                    self._fire(self._on_category)
                    return True
            return False
        wrap.bind(on_touch_up=_maybe_fire)

        wrap.add_widget(self.cat_chip)
        self.grid.add_widget(wrap)

    def _add_backspace_cell(self):
        wrap = AnchorLayout(anchor_x="center", anchor_y="center")
        from kivymd.uix.button import MDIconButton

        btn = MDIconButton(icon="backspace-outline", size_hint=(None, None), size=(dp(44), dp(44)))
        btn.bind(on_release=lambda *_: self._fire(self._on_backspace))
        wrap.add_widget(btn)
        self.grid.add_widget(wrap)

    def _build_next_overlay(self):
        # 覆蓋底列中間兩格
        self.next_overlay = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(None, None))
        self.btn_ok = MDRaisedButton(text=self._ok_text_default, size_hint=(None, None), height=dp(40))
        self.btn_ok.bind(on_release=lambda *_: self._fire(self._on_ok))
        self.next_overlay.add_widget(self.btn_ok)
        self.add_widget(self.next_overlay)

    # ────────────────────────── events ─────────────────────────
    def _tap_digit(self, s: str):
        self._fire(lambda: self._on_digit(str(s)))

    def _tap_op(self, sym_vis: str):
        # 轉為運算子
        op = {"+": "+", "−": "-", "×": "*", "÷": "/"}[sym_vis]
        self._fire(lambda: self._on_op(op))

    def _fire(self, cb: Callable[[], None] | None):
        if callable(cb):
            cb()

    # ────────────────────────── layout ─────────────────────────
    def _place_next(self, *_):
        grid = self.grid
        cols, rows = 4, 5

        # spacing
        sp = grid.spacing
        sx, sy = (sp if isinstance(sp, (list, tuple)) else (sp, sp))

        # padding: (l, t, r, b) 或單值
        pad = grid.padding
        if isinstance(pad, (list, tuple)) and len(pad) == 4:
            pl, pt, pr, pb = pad
        else:
            pl = pt = pr = pb = float(pad or 0)

        cw = (grid.width  - pl - pr - sx * (cols - 1)) / cols if cols else 0
        ch = (grid.height - pb - pt - sy * (rows - 1)) / rows if rows else 0

        # 讓 overlay 完全只覆蓋「底列中間兩格」（第 2、3 欄）
        x = grid.x + pl + (cw + sx) * 1
        y = grid.y + pb + (ch + sy) * 0  # 底列
        self.next_overlay.pos  = (x, y)
        self.next_overlay.size = (cw * 2 + sx, ch)

        # 確保按鈕尺寸穩定
        self._size_next_button()

        # 左下 Category chip 的寬度對齊第 1 欄
        if hasattr(self, "cat_chip"):
            self.cat_chip.width = max(0, cw)

    def _size_next_button(self):
        w = self.next_overlay.width * 0.92
        h = self.next_overlay.height * 0.70
        self.btn_ok.width = max(dp(140), min(dp(420), w))
        self.btn_ok.height = max(dp(36), min(dp(56), h))

    # ────────────────────────── visuals ────────────────────────
    def set_equals_mode(self, on: bool):
        self._equals_mode = bool(on)
        self.btn_ok.text = "=" if self._equals_mode else self._ok_text_default
        # 等下一幀再依新的 overlay 尺寸重算一次
        self._size_next_button()

    def highlight_op(self, symbol: str | None):
        """圓形高亮運算子；symbol=None 取消全部。"""
        for sym, widget in self.op_widgets.items():
            try:
                widget.selected = (sym == symbol) if symbol else False
            except Exception:
                pass
