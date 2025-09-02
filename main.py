from __future__ import annotations
from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel


from core.eventbus import EventBus
from data.db import init_db
from data.seed import seed_if_empty
from domain.usecases import UseCases


from features.home.screen_home import HomeScreen
from features.balance.screen_balance import BalanceScreen
from features.add.screen_add import AddScreen
from features.history.screen_history import HistoryScreen
from features.analysis.screen_analysis import AnalysisScreen


KV = """
<MDRoot>:
orientation: 'vertical'
MDTopAppBar:
title: "LedgerLite"
elevation: 2
MDBottomNavigation:
id: tabs
text_color_active: 1, 1, 1, 1
"""


class MDRoot(MDBoxLayout):
pass


class App(MDApp):
def build(self):
self.title = "LedgerLite"
Builder.load_string(KV)
root = MDRoot()


# DB 準備
init_db()
seed_if_empty()


# DI
self.bus = EventBus()
self.uc = UseCases(self.bus)


# Tabs + Screens
tabs = root.ids.tabs
sm = MDScreenManager()


# 建立各分頁
home = HomeScreen(); home.build()
bal = BalanceScreen(); bal.build()
add = AddScreen(usecases=self.uc); add.build()
his = HistoryScreen(); his.build()
ana = AnalysisScreen(); ana.build()


# 放到 BottomNavigation
self._add_tab(tabs, "首頁", "home", home)
self._add_tab(tabs, "餘額", "cash", bal)
self._add_tab(tabs, "新增", "plus", add)
self._add_tab(tabs, "歷史", "history", his)
self._add_tab(tabs, "分析", "chart-timeline", ana)


root.add_widget(tabs)
return root


def _add_tab(self, tabs: MDBottomNavigation, text: str, icon: str, screen):
item = MDBottomNavigationItem(name=text, text=text, icon=icon)
item.add_widget(screen)
tabs.add_widget(item)


if __name__ == "__main__":
App().run()