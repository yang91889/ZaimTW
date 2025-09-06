# features/add/tabs/manual/components/keypad_stack.py
from __future__ import annotations

from typing import Callable, Optional

from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout

from kivymd.app import MDApp
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton

from ..widgets.key import Key
from ..widgets.category_chip import CategoryChip


class KeypadStack(FloatLayout):
    """
    4x5 的數字鍵盤堆疊區（底行中間兩格留白，覆蓋一顆 NEXT/＝ 按鈕）。
    - 提供運算符高亮（圓形標記）
    - 提供 set_equals_mode(True/False) 切換 NEXT 與 '=' 顯示，並避免縮水
    - 將左下角做成 CategoryChip（圖示＋文字置中），暴露 set_category() 供外部切換
    """

    def __init__(
        self,
        on_num: Callable[[str], None],
        on_dot: Callable[[], None],
        on_op: Callable[[str], None],          # 參數為 '+', '-', '*', '/'
        on_backspace: Callable[[], None],
        on_next: Callable[[bool], None],       # 參數 is_equals: True 表 '='，False 表 NEXT
        t: Callable[[str], str],               # i18n 取字函式
        **kwargs,
    ):
        """
        傳入的 callback 說明：
          - on_num(token)          : 點擊數字或 '00'
          - on_dot()               : 點擊 '.'
          - on_op(op)              : 點 '+','-','*','/'（注意是實際運算子）
          - on_backspace()         : 點退格
          - on_next(is_equals)     : 點覆蓋鍵。is_equals=True 表示目前是 '=' 模式；False 表示 NEXT。
          - t(key)                 : i18n 取字，例如 t("NEXT"), t("CATEGORY")

        注意：本元件只負責 UI 與事件派送，不做計算邏輯。
        """
        super().__init__(**kwargs)
        self.on_num = on_num
        self.on_dot = on_dot
        self.on_op = on_op
        self.on_backspace = on_backspace
        self.on_next = on_next
        self._t = t

        # 取主題色（相容不同 KivyMD 版本）
        app = MDApp.get_running_app()
        theme_cls = getattr(app, "theme_cls", None)
        primary_color = getattr(theme_cls, "primary_color", (0.2, 0.6, 1, 1))
        mark_rgba = list(primary_color)
        mark_rgba[3] = 0.22
        self._mark_rgba = mark_rgba

        # 內部狀態
        self._equals_mode = False
        self._op_widgets = {}  # UI 符號 → Key widget 映射（'+','−','×','÷'）

        # ── Grid 與鍵 ─────────────────────────────────────────────────────
        self.grid = MDGridLayout(
            cols=4,
            spacing=(dp(12), dp(16)),
            padding=(dp(0), dp(8), dp(0), dp(8)),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self.grid)

        op_ui = ("+", "−", "×", "÷")
        keys = [
            ("7", self._tap_num), ("8", self._tap_num), ("9", self._tap_num), ("÷", self._tap_op_ui),
            ("4", self._tap_num), ("5", self._tap_num), ("6", self._tap_num), ("×", self._tap_op_ui),
            ("1", self._tap_num), ("2", self._tap_num), ("3", self._tap_num), ("−", self._tap_op_ui),
            ("00", self._tap_num), ("0", self._tap_num), (".", self._tap_dot), ("+", self._tap_op_ui),
        ]
        for text, handler in keys:
            scale = 0.42 if text not in op_ui else 0.36
            k = Key(text=text, on_tap=lambda s, h=handler: h(s), scale=scale, mark_rgba=self._mark_rgba)
            self.grid.add_widget(k)
            if text in op_ui:
                self._op_widgets[text] = k

        # ── 底列： [Category] [空] [空] [Backspace] ────────────────────────
        cat_wrap = AnchorLayout(anchor_x="center", anchor_y="center")
        self.cat_chip = CategoryChip(text=self._t("CATEGORY"))  # 預設文字
        # 沒有外部專屬處理時，暫時讓它當作 "00"
        self.cat_chip.bind(on_release=lambda *_: self.on_num("00"))
        cat_wrap.add_widget(self.cat_chip)
        self.grid.add_widget(cat_wrap)

        self.grid.add_widget(Widget())  # 空
        self.grid.add_widget(Widget())  # 空

        back_cell = AnchorLayout(anchor_x="center", anchor_y="center")
        self.btn_back = MDIconButton(icon="backspace-outline",
                                     size_hint=(None, None), size=(dp(44), dp(44)))
        self.btn_back.bind(on_release=lambda *_: self.on_backspace())
        back_cell.add_widget(self.btn_back)
        self.grid.add_widget(back_cell)

        # ── NEXT / '=' 覆蓋（蓋住底列中間兩格） ──────────────────────────
        self.next_overlay = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(None, None))
        self.btn_next = MDRaisedButton(text=self._t("NEXT"), size_hint=(None, None), height=dp(40))
        self.btn_next.bind(on_release=self._on_next_pressed)
        self.next_overlay.add_widget(self.btn_next)
        self.add_widget(self.next_overlay)

        # 跟著尺寸變化重新定位 overlay
        self.grid.bind(size=lambda *_: self.place_next(), pos=lambda *_: self.place_next())
        self.bind(size=lambda *_: self.place_next())
        Window.bind(on_resize=lambda *_: self.place_next())

    # ────────────────────────── Public API ───────────────────────────────
    def set_equals_mode(self, on: bool):
        """切換 NEXT/＝ 文字，並在下一幀固定按鈕尺寸避免縮水。"""
        self._equals_mode = bool(on)
        self.btn_next.text = "=" if self._equals_mode else self._t("NEXT")
        Clock.schedule_once(lambda *_: self._size_next_button(), 0)

    def highlight_op(self, ui_symbol: Optional[str]):
        """
        高亮 UI 符號（'+','−','×','÷'）；傳 None 取消全部。
        這需要 Key 支援 `selected` 屬性與 `mark_rgba`。
        """
        for sym, widget in self._op_widgets.items():
            try:
                widget.selected = (sym == ui_symbol) if ui_symbol else False
            except Exception:
                pass

    def set_category(self, *, text: Optional[str] = None, icon: Optional[str] = None):
        """外部可切換左下 chip 的文字/圖示。"""
        if text is not None:
            try:
                self.cat_chip.set_text(text)
            except Exception:
                try:
                    self.cat_chip._label.text = text
                except Exception:
                    pass
        if icon is not None:
            try:
                self.cat_chip.set_icon(icon)
            except Exception:
                try:
                    self.cat_chip._icon.icon = icon
                except Exception:
                    pass

    # ────────────────────────── Internal layout ─────────────────────────
    def place_next(self):
        """讓 overlay 橫跨底列中間兩格，並同步 Category chip 的寬度。"""
        grid = self.grid
        cols, rows = 4, 5

        sp = grid.spacing
        sx, sy = (sp if isinstance(sp, (list, tuple)) else (sp, sp))
        pad = grid.padding
        if isinstance(pad, (list, tuple)) and len(pad) == 4:
            pl, pt, pr, pb = pad
        else:
            pl = pt = pr = pb = float(pad or 0)

        cw = (grid.width - pl - pr - sx * (cols - 1)) / cols if cols else 0
        ch = (grid.height - pb - pt - sy * (rows - 1)) / rows if rows else 0

        # 覆蓋第 2～3 欄（index 1 與 2）
        y = grid.y + pb
        x = grid.x + pl + (cw + sx) * 1

        self.next_overlay.pos = (x, y)
        self.next_overlay.size = (cw * 2 + sx, ch)
        self._size_next_button()

        # 讓左下角 Category chip 的寬度與格寬一致
        try:
            self.cat_chip.width = cw
        except Exception:
            pass

    def _size_next_button(self):
        """固定 NEXT/＝ 實際寬高，避免因文字長度變動造成縮放抖動。"""
        w = self.next_overlay.width * 0.92
        h = self.next_overlay.height * 0.70
        self.btn_next.width = min(dp(420), max(dp(140), w))
        self.btn_next.height = min(dp(56), max(dp(36), h))

    # ────────────────────────── Event handlers ───────────────────────────
    def _on_next_pressed(self, *_):
        # 將目前是否為 '=' 模式傳給外部
        self.on_next(self._equals_mode)

    def _tap_num(self, token: str):
        self.on_num(token)

    def _tap_dot(self, _):
        self.on_dot()

    def _tap_op_ui(self, ui_symbol: str):
        """點了 UI 符號：轉換為實際運算子，交給外部；並高亮與切 '=' 模式。"""
        op = {"+": "+", "−": "-", "×": "*", "÷": "/"}[ui_symbol]
        self.on_op(op)
        self.highlight_op(ui_symbol)
        self.set_equals_mode(True)
