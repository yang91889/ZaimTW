from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

class Divider(Widget):
    """1dp hairline separator; KivyMD 版本差異時的通用替代。"""
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(1), **kwargs)
        with self.canvas.after:
            Color(0, 0, 0, 0.12)
            self._rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._sync, pos=self._sync)

    def _sync(self, *_):
        self._rect.size = self.size
        self._rect.pos = self.pos
