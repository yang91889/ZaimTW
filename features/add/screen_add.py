# features/add/screen_add.py
from __future__ import annotations

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.tab import MDTabs
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty

from core.i18n import t
from domain.usecases import UseCases
from data.dao import TxDao

# 分頁元件（已分檔）
from features.add.tabs import InvoiceTab, ManualTab, CommonTab, QuickTab


class AddScreen(MDScreen):
    """Add 主畫面：自訂 4 分 header + 2dp 指示器 + 內容以 MDTabs 承載。"""
    name = "add"

    # 用來驅動 header 內 2dp 指示器的 X 位置（px，從 header 左側起算）
    _ind_x = NumericProperty(0.0)

    def __init__(self, usecases: UseCases, switch_tab, **kwargs):
        super().__init__(**kwargs)
        self.usecases = usecases
        self.switch_tab = switch_tab
        self.txdao = TxDao()
        self._active_index = 0

        # ===== 根容器 =====
        root = MDBoxLayout(orientation="vertical", padding=0, spacing=0)
        self.add_widget(root)

        # ===== 自訂 Header（等寬四個） =====
        theme = MDApp.get_running_app().theme_cls
        primary = theme.primary_color
        indicator_rgba = (1.0, 0.76, 0.03, 1)  # 琥珀色，對藍底可見

        # 48dp 文字列 + 2dp 指示器
        self._header_wrap = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(50))
        self._header_wrap.md_bg_color = primary

        self._titles = [
            t("ADD_TAB_INVOICE"),
            t("ADD_TAB_MANUAL"),
            t("ADD_TAB_COMMON"),
            t("ADD_TAB_QUICK"),
        ]

        # 上排：四個等寬按鈕
        self.header = MDBoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(48), padding=0, spacing=0)
        self.header_btns: list[MDFlatButton] = []
        for i, title in enumerate(self._titles):
            btn = MDFlatButton(
                text=title,
                size_hint=(1, 1),  # ★ 等分寬度
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1 if i == 0 else 0.75),
                halign="center",
            )
            btn.bind(on_release=lambda _w, idx=i: self._switch_to_index(idx))
            self.header.add_widget(btn)
            self.header_btns.append(btn)
        self._header_wrap.add_widget(self.header)

        # 下排：2dp 指示器（畫在 header_wrap 的 canvas.after）
        with self._header_wrap.canvas.after:
            Color(*indicator_rgba)
            self._ind_rect = Rectangle(size=(0, dp(2)), pos=(0, 0))

        root.add_widget(self._header_wrap)

        # ===== Tabs（隱藏原生 tab bar） =====
        self.tabs = MDTabs()
        self.tabs.tab_bar_height = 0
        root.add_widget(self.tabs)

        # 內容分頁（使用外部檔案）
        self.tabs.add_widget(InvoiceTab(record_expense=self._record_expense))
        self.tabs.add_widget(ManualTab(record_expense=self._record_expense))
        self.tabs.add_widget(CommonTab(dao=self.txdao, record_expense=self._record_expense))
        self.tabs.add_widget(QuickTab(record_expense=self._record_expense))

        # 切換事件：同步 header 高亮與指示器
        self.tabs.bind(on_tab_switch=self._on_tabs_switched)

        # 尺寸 / 位置改變時更新指示器
        self.bind(size=self._update_ind_rect, pos=self._update_ind_rect)
        self._header_wrap.bind(size=self._update_ind_rect, pos=self._update_ind_rect)
        self.header.bind(size=self._update_ind_rect, pos=self._update_ind_rect)
        self.bind(_ind_x=self._update_ind_rect)

        # 初始定位
        self._update_ind_rect()
        self._set_active(0)

    # ===== Header/Indicator =====
    def _segment_width(self) -> float:
        n = max(1, len(self.header_btns))
        return float(self.header.width) / n

    def _header_bottom_y(self) -> float:
        return self._header_wrap.y

    def _header_left_x(self) -> float:
        return self._header_wrap.x

    def _update_ind_rect(self, *_):
        seg = self._segment_width()
        self._ind_rect.size = (seg, dp(2))
        self._ind_rect.pos = (self._header_left_x() + self._ind_x, self._header_bottom_y())

    def _animate_indicator(self):
        seg = self._segment_width()
        target = seg * self._active_index
        Animation.cancel_all(self, '_ind_x')
        Animation(_ind_x=target, d=0.2, t="out_quad").start(self)

    def _set_active(self, index: int):
        self._active_index = int(index)
        for i, b in enumerate(self.header_btns):
            b.text_color = (1, 1, 1, 1 if i == self._active_index else 0.75)
        self._animate_indicator()

    def _switch_to_index(self, index: int):
        title = self._titles[index]
        # 先用官方 API
        try:
            self.tabs.switch_tab(title)
        except Exception:
            # 版本 fallback
            try:
                slides = getattr(self.tabs, "get_slides", lambda: None)()
                carousel = getattr(self.tabs, "carousel", None) or self.tabs.ids.get("carousel")
                if slides and carousel:
                    carousel.load_slide(slides[index])
            except Exception:
                pass
        self._set_active(index)

    def _on_tabs_switched(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        # MDTabs.on_tab_switch 正確簽名
        try:
            idx = self._titles.index(tab_text)
        except Exception:
            try:
                slides = getattr(instance_tabs, "get_slides", lambda: None)()
                idx = slides.index(instance_tab) if slides else 0
            except Exception:
                idx = 0
        self._set_active(idx)

    # ===== Domain helper =====
    def _record_expense(self, amount: float, category_id: int | None = 1, note: str | None = None):
        tx_id = self.usecases.quick_add_tx(amount=amount, category_id=category_id, note=note)
        self.switch_tab(t("TAB_HOME"))  # 完成後回首頁
        return tx_id
