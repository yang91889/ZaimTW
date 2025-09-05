from __future__ import annotations

from kivy.metrics import sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Ellipse

from kivymd.uix.label import MDLabel


class Key(ButtonBehavior, MDLabel):
    """Borderless keypad key with auto-scaling font + optional circular highlight."""
    scale = NumericProperty(0.42)
    selected = BooleanProperty(False)                # 是否高亮（給運算符用）
    mark_rgba = ListProperty([0, 0, 0, 0.16])        # 高亮圓形顏色

    def __init__(self, text: str, on_tap, scale: float | None = None,
                 mark_rgba: list[float] | None = None, **kw):
        super().__init__(**kw)
        self.text = text
        self.halign = "center"
        self.valign = "center"
        self.theme_text_color = "Primary"
        if scale is not None:
            self.scale = scale
        if mark_rgba is not None:
            self.mark_rgba = mark_rgba
        self.bind(size=lambda *_: self._fit())

        # 圓形底（在文字下方）
        with self.canvas.before:
            self._mark_color = Color(0, 0, 0, 0)
            self._mark = Ellipse(pos=self.pos, size=(0, 0))
        self.bind(pos=self._update_mark, size=self._update_mark,
                  selected=self._update_mark, mark_rgba=self._update_mark)

        self.on_tap = on_tap

    def _fit(self):
        s = min(self.width, self.height) * self.scale
        self.font_size = max(sp(18), s)
        self.text_size = (self.width, self.height)

    def _update_mark(self, *_):
        if self.selected:
            rgba = list(self.mark_rgba)
            if len(rgba) != 4:
                rgba = [rgba[0], rgba[1], rgba[2], 0.16]
            self._mark_color.rgba = rgba
            d = min(self.width, self.height) * 0.66
            self._mark.size = (d, d)
            self._mark.pos = (self.center_x - d / 2.0, self.center_y - d / 2.0)
        else:
            self._mark_color.rgba = (0, 0, 0, 0)
            self._mark.size = (0, 0)

    def on_release(self):
        if callable(self.on_tap):
            self.on_tap(self.text)
