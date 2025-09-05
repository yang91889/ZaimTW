from __future__ import annotations
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon


class CategoryChip(ButtonBehavior, MDBoxLayout):
    """上 icon、下文字，兩者皆水平置中；寬度由父層決定。"""
    def __init__(self, text: str = "CATEGORY", icon: str = "silverware-fork-knife", **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.spacing = dp(2)
        self.padding = (0, 0, 0, 0)

        # 讓父層（格子）控制寬高；這裡給一個基礎值
        self.size_hint = (None, None)
        self.width = dp(56)
        self.height = dp(56)

        # --- 上：圖示，放進 AnchorLayout 才能真正水平置中 ---
        self._icon_wrap = AnchorLayout(anchor_x="center", anchor_y="center",
                                       size_hint_y=None, height=dp(32))
        self._icon = MDIcon(icon=icon, size_hint=(None, None))
        self._icon.font_size = sp(24)
        self._icon_wrap.add_widget(self._icon)
        self.add_widget(self._icon_wrap)

        # --- 下：文字，利用 text_size=自身寬度 來置中 ---
        self._label = MDLabel(text=text, halign="center",
                              theme_text_color="Secondary",
                              font_size=sp(12),
                              size_hint_y=None)
        # 高度跟著文字
        self._label.bind(texture_size=lambda *_:
                         setattr(self._label, "height", self._label.texture_size[1]))
        # 當 chip 寬度變動時，維持置中
        self.bind(width=lambda *_: setattr(self._label, "text_size", (self.width, None)))
        self.add_widget(self._label)

    # 對外 API：改 icon/文字
    def set_icon(self, icon_name: str):
        self._icon.icon = icon_name

    def set_text(self, text: str):
        self._label.text = text
