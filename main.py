from kivy.app import App 
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout



class HOLLOW_PURPLE(App):
    def build(slef):
        f = FloatLayout()
        s = Scatter()
        l = Label (text = "HOLLOW PURPLE", font_size = 100)

        f.add_widget(s)
        s.add_widget(l)
        return f
    
    
if __name__ == "__main__":
    HOLLOW_PURPLE().run()