from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from molmass import Formula
from kivy.core.clipboard import Clipboard
import re

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=[100,300,100,100]) 
        self.input = TextInput(hint_text='Enter a compound', multiline=False, halign="center", font_size=50, padding=[20, 270, 20, 20]) 
        self.input.bind(on_text_validate=self.calculate) 
        layout.add_widget(self.input)
        button_layout = BoxLayout(padding=[100,100,100,100]) 
        button = Button(text='Calculate Molecular Mass', font_size=50)
        button.bind(on_press=self.calculate)
        button_layout.add_widget(button) 
        layout.add_widget(button_layout) 
        self.label = Label(text='', halign="center", font_size=50)
        layout.add_widget(self.label)
        return layout

    def calculate(self, instance):
        input_text = self.input.text
        try:
            total_mass = 0
            # Split the input text into components
            components = re.findall(r'(\d*\(*[A-Za-z\(][A-Za-z0-9\(\)]*\)*)', input_text)
            for component in components:
                # Check if the component starts with a digit (coefficient)
                match = re.match(r"(\d+)([A-Za-z\(].*)", component)
                if match:
                    coefficient, compound = match.groups()
                    coefficient = int(coefficient)
                else:
                    coefficient = 1
                    compound = component

                # Handle nested parentheses
                while '(' in compound and ')' in compound:
                    innermost = re.search(r'\(([A-Za-z0-9]*)\)', compound).group(1)
                    compound = compound.replace(f'({innermost})', innermost, 1)

                f = Formula(compound)
                total_mass += f.mass * coefficient

            t = f"{total_mass:.3f}"
            self.label.text = f"Molecular Mass: {t}"
            Clipboard.copy(t)
        except Exception as e:
            self.label.text = "Invalid input."

if __name__ == '__main__':
    MyApp().run()
