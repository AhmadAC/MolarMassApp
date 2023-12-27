from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from molmass import Formula
from kivy.core.clipboard import Clipboard

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=[100,300,100,100])  # Added padding to layout

        self.input = TextInput(hint_text='Enter a compound', multiline=False, halign="center", font_size=50, padding=[20, 270, 20, 20])  # Added padding to TextInput
        layout.add_widget(self.input)

        button_layout = BoxLayout(padding=[100,100,100,100])  # New layout for button
        button = Button(text='Calculate Molecular Mass', font_size=50)
        button.bind(on_press=self.calculate)
        button_layout.add_widget(button)  # Add button to new layout
        layout.add_widget(button_layout)  # Add new layout to main layout

        self.label = Label(text='', halign="center", font_size=50)
        layout.add_widget(self.label)

        return layout

    def calculate(self, instance):
        compound = self.input.text
        try:
            f = Formula(compound)
            t = f"{f.mass:.3f}"
            self.label.text = f"Molecular Mass: {t}"
            Clipboard.copy(t)
        except Exception as e:
            self.label.text = "Invalid input."

if __name__ == '__main__':
    MyApp().run()
