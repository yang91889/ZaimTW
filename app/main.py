from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager

KV = """
ScreenManager:
    HomeScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"
        Label:
            text: "ZaimTW - Hello!"
            font_size: "20sp"
        Button:
            text: "按我測試"
            on_release: app.on_press_demo()
"""

class HomeScreen(Screen):
    pass

class ZaimTWApp(App):
    def build(self):
        return Builder.load_string(KV)

    def on_press_demo(self):
        print("Button pressed!")

if __name__ == "__main__":
    ZaimTWApp().run()
