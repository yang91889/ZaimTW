from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
import os

# 設定字體路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")
resource_add_path(FONTS_DIR)

# 註冊字體 (使用 TTF)
LabelBase.register(
    name="NotoSansTC",
    fn_regular="NotoSansTC-Regular.ttf",
    fn_bold="NotoSansTC-Bold.ttf",
)


class HomeScreen(Screen):
    pass


class WindowManager(ScreenManager):
    pass


class DemoApp(MDApp):
    def build(self):
        # 修改 KivyMD 全域字體樣式
        for k, v in self.theme_cls.font_styles.items():
            v[0] = "NotoSansTC"  # [字體名稱, size, bold, spacing]

        return Builder.load_file("main.kv")


if __name__ == "__main__":
    DemoApp().run()
