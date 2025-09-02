# features/analysis/screen_analysis.py
from __future__ import annotations
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

class AnalysisScreen(MDScreen):
    name = "analysis"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box = MDBoxLayout(orientation="vertical")
        box.add_widget(MDLabel(text="分析 (V1 佔位)", halign="center"))
        self.add_widget(box)
