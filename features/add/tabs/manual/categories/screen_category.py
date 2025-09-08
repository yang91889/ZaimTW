# features/add/tabs/manual/categories/screen_category.py
from __future__ import annotations

from typing import Callable, List, Dict
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IRightBodyTouch
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton

from core.i18n import t as _t


# ───────── Compact header (no double AppBar) ─────────
class CompactHeader(MDBoxLayout):
    def __init__(self, title: str, on_back, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None, height=dp(56),
            padding=(dp(4), dp(8), dp(12), dp(8)),
            spacing=dp(8), **kwargs
        )
        btn = MDIconButton(icon="arrow-left")
        btn.bind(on_release=lambda *_: on_back())
        lbl = MDLabel(text=title, font_style="H6", halign="left", valign="middle")
        self.add_widget(btn)
        self.add_widget(lbl)


class Chevron(IRightBodyTouch, MDIconButton):
    pass


class Divider(Widget):
    """1dp divider independent of KivyMD version."""
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(1), **kwargs)
        with self.canvas.after:
            Color(0, 0, 0, 0.12)
            self._rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._sync, pos=self._sync)

    def _sync(self, *_):
        self._rect.size = self.size
        self._rect.pos = self.pos


class CategorySelectScreen(Screen):
    """
    Full-screen Category Picker (English-first).
    on_pick will receive the picked category dict but with
    'name'/'subtitle' overridden to English if available.
    """

    def __init__(
        self,
        name: str,
        on_pick: Callable[[Dict], None],
        categories: List[Dict],
        recents: List[int] | None = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.on_pick = on_pick
        self.all_categories = categories[:] if categories else []
        self.recents = recents or []

        root = MDBoxLayout(orientation="vertical", padding=(0, 0, 0, 0), spacing=0)
        self.add_widget(root)

        # Solid page background so modal overlay isn't transparent
        with self.canvas.before:
            r, g, b, a = self._theme_bg()
            self._bg_color = Color(r, g, b, a)
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._sync_bg, pos=self._sync_bg)

        # Header
        header = CompactHeader(_t("CATEGORY_SELECT"), self._go_back)
        root.add_widget(header)

        # Search row (fixed height – avoids large gap)
        pad = MDBoxLayout(
            orientation="horizontal",
            padding=(dp(12), dp(6), dp(12), dp(6)),
            size_hint_y=None, height=dp(56),
        )
        self.search = MDTextField(
            hint_text=_t("SEARCH_CATEGORY"),
            size_hint_x=1,
            size_hint_y=None, height=dp(44),
            mode="round",
            icon_left="magnify",
            on_text=self._on_search_text,
        )
        pad.add_widget(self.search)
        root.add_widget(pad)

        # List
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        root.add_widget(scroll)
        self.list_box = MDList()
        scroll.add_widget(self.list_box)

        self._rebuild_list()

    # ───────── helpers ─────────
    def _theme_bg(self):
        app = MDApp.get_running_app()
        for k in ("backgroundColor", "bg_normal", "bg_darkest", "bg_dark"):
            v = getattr(getattr(app, "theme_cls", object()), k, None)
            if v:
                return tuple(v)
        return (1, 1, 1, 1)

    def _sync_bg(self, *_):
        self._bg_rect.size = self.size
        self._bg_rect.pos = self.pos

    def _go_back(self, *_):
        # If embedded in a ModalView, just dismiss it
        try:
            from kivy.uix.modalview import ModalView
            if isinstance(self.parent, ModalView):
                self.parent.dismiss()
                return
        except Exception:
            pass

        sm = self._find_screen_manager()
        if sm:
            try:
                sm.current = sm.previous()
            except Exception:
                pass
            sm.remove_widget(self)
            return

        try:
            from kivy.core.window import Window
            if self.parent is Window:
                Window.remove_widget(self)
            elif self.parent is not None:
                self.parent.remove_widget(self)
        except Exception:
            if self.parent is not None:
                self.parent.remove_widget(self)

    def _find_screen_manager(self) -> ScreenManager | None:
        w = self.parent
        while w is not None and not isinstance(w, ScreenManager):
            w = w.parent
        if isinstance(w, ScreenManager):
            return w
        app = App.get_running_app()
        if hasattr(app, "root") and isinstance(app.root, ScreenManager):
            return app.root
        return None

    def _on_search_text(self, *args):
        self._rebuild_list(self.search.text or "")

    # Prefer English fields if present; otherwise fall back
    def _display_text(self, cat: Dict) -> tuple[str, str]:
        name = cat.get("name_en") or cat.get("name") or ""
        sub  = cat.get("subtitle_en") or cat.get("subtitle", "")
        return name, sub

    def _add_section_header(self, text: str):
        box = MDBoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(8), dp(12), dp(4)),
            size_hint_y=None, height=dp(36),
        )
        lbl = MDLabel(text=text, theme_text_color="Hint")
        box.add_widget(lbl)
        self.list_box.add_widget(box)
        self.list_box.add_widget(Divider())

    def _add_item(self, cat: Dict):
        name, sub = self._display_text(cat)
        item = TwoLineAvatarIconListItem(text=name, secondary_text=sub)
        icon = IconLeftWidget(icon=cat.get("icon", "shape"))
        icon.theme_text_color = "Custom"
        icon.text_color = cat.get("color", (0.5, 0.5, 0.5, 1))
        chev = Chevron(icon="chevron-right")
        item.add_widget(icon)
        item.add_widget(chev)
        item.bind(on_release=lambda *_: self._pick(cat))
        self.list_box.add_widget(item)

    def _pick(self, cat: Dict):
        # Return English name/subtitle in the same keys Manual already reads
        out = dict(cat)
        name, sub = self._display_text(cat)
        out["name"] = name
        out["subtitle"] = sub
        try:
            if callable(self.on_pick):
                self.on_pick(out)
        finally:
            self._go_back()

    def _rebuild_list(self, query: str = ""):
        self.list_box.clear_widgets()

        q = (query or "").strip().lower()
        cats = self.all_categories
        if q:
            def matches(c):
                fields = [
                    c.get("name_en") or c.get("name", ""),
                    c.get("subtitle_en") or c.get("subtitle", ""),
                ]
                return q in " ".join(fields).lower()
            cats = [c for c in cats if matches(c)]

        # Recently Used
        if not q and self.recents:
            recent_objs = [c for c in self.all_categories if c.get("id") in self.recents]
            if recent_objs:
                self._add_section_header(_t("RECENTLY_USED"))
                for c in recent_objs:
                    self._add_item(c)
                self.list_box.add_widget(Divider())

        # All Categories
        self._add_section_header(_t("ALL_CATEGORIES"))
        for c in cats:
            self._add_item(c)

        if not cats:
            none = MDLabel(
                text=_t("NO_MATCHES"),
                halign="center", theme_text_color="Hint",
                padding=(0, dp(24)),
            )
            wrap = AnchorLayout(
                anchor_x="center", anchor_y="center",
                size_hint_y=None, height=dp(80)
            )
            wrap.add_widget(none)
            self.list_box.add_widget(wrap)
