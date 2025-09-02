from __future__ import annotations
from kivy.lang import Builder
from kivy.factory import Factory
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

from core.eventbus import EventBus
from core.i18n import t   # ← 新增
from data.db import init_db
from data.seed import seed_if_empty
from domain.usecases import UseCases

from features.home.screen_home import HomeScreen
from features.balance.screen_balance import BalanceScreen
from features.add.screen_add import AddScreen
from features.history.screen_history import HistoryScreen
from features.analysis.screen_analysis import AnalysisScreen

KV = """
<MDRoot@MDBoxLayout>:
    orientation: 'vertical'
    MDTopAppBar:
        title: "LedgerLite"
        elevation: 2
    MDBottomNavigation:
        id: tabs
        text_color_active: 1, 1, 1, 1
"""

class App(MDApp):
    def build(self):
        self.title = "LedgerLite"
        Builder.load_string(KV)
        root = Factory.MDRoot()
        init_db(); seed_if_empty()

        self.bus = EventBus()
        self.uc = UseCases(self.bus)

        tabs: MDBottomNavigation = root.ids.tabs
        switch_tab = lambda name: tabs.switch_tab(name)

        home = HomeScreen()
        bal = BalanceScreen()
        add = AddScreen(usecases=self.uc, switch_tab=switch_tab)
        his = HistoryScreen()
        ana = AnalysisScreen()

        # 英文分頁（用 i18n）
        self._add_tab(tabs, t("TAB_HOME"), "home", home)
        self._add_tab(tabs, t("TAB_BALANCE"), "wallet", bal)
        self._add_tab(tabs, t("TAB_ADD"), "plus", add)
        self._add_tab(tabs, t("TAB_HISTORY"), "history", his)
        self._add_tab(tabs, t("TAB_ANALYSIS"), "chart-line", ana)
        return root

    def _add_tab(self, tabs: MDBottomNavigation, text: str, icon: str, screen):
        item = MDBottomNavigationItem(name=text, text=text, icon=icon)
        item.add_widget(screen)
        tabs.add_widget(item)

if __name__ == "__main__":
    App().run()
