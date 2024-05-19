#rebuild test
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from molmass import Formula
from molmass import elements
from kivy.core.clipboard import Clipboard
import re

def get_electronegativity(element_symbol):
    try:
        el = elements.ELEMENTS[element_symbol.capitalize()]
        return el.eleneg
    except:
        return None  # Return None if the element symbol is not valid

def split_elements(compound):
    elements = []
    i = 0
    while i < len(compound):
        # Check for a two-letter element symbol first
        if i + 1 < len(compound):
            symbol = compound[i:i+2].capitalize()
            if get_electronegativity(symbol) is not None:
                elements.append(symbol)
                i += 2
                continue
        # Check for a one-letter element symbol
        symbol = compound[i].capitalize()
        if get_electronegativity(symbol) is not None:
            elements.append(symbol)
        i += 1
    # If the compound is two characters long and only one element was found, split into two one-letter elements
    if len(compound) == 2 and len(elements) == 1:
        elements = [compound[0].capitalize(), compound[1].capitalize()]
    return elements

class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        button = Button(text='EN', size_hint=(.2, .2), pos_hint={'right': 1})
        button.bind(on_release=self.change_screen)
        layout.add_widget(button)

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

        self.add_widget(layout)

    def change_screen(self, instance):
        self.manager.current = 'second_screen'

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

class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        button = Button(text='MM', size_hint=(.2, .2), pos_hint={'right': 1})
        button.bind(on_release=self.change_screen)
        layout.add_widget(button)

        self.input = TextInput(hint_text='Enter two elements i.e HO', multiline=False, halign="center", font_size=50, padding=[20, 270, 20, 20]) 
        self.input.bind(on_text_validate=self.get_electronegativity_difference) 
        layout.add_widget(self.input)
        button_layout = BoxLayout(padding=[100,100,100,100]) 
        button = Button(text='Calculate Electronegativity Difference', font_size=50)
        button.bind(on_press=self.get_electronegativity_difference)
        button_layout.add_widget(button) 
        layout.add_widget(button_layout) 
        self.label = Label(text='', halign="center", font_size=50)
        layout.add_widget(self.label)

        self.add_widget(layout)

    def get_electronegativity_difference(self, instance=None):
        input_text = self.input.text
        try:
            elements = split_elements(input_text)
            if len(elements) != 2:
                self.label.text = "Invalid input." 
                return
            en1 = get_electronegativity(elements[0])
            en2 = get_electronegativity(elements[1])
            if en1 is None or en2 is None:
                raise ValueError("Invalid input.")
            en_difference = abs(en1 - en2)
            bond_type = ""
            if en_difference < 0.4:
                bond_type = "non-polar covalent"
            elif en_difference < 1.7:
                bond_type = "polar covalent"
            else:
                bond_type = "ionic"
            self.label.text = f"EN Difference between {elements[0]} and {elements[1]} is: \n |{en1:.1f} - {en2:.1f}| = {en_difference:.1f} \n{bond_type}"
            Clipboard.copy(str(f'{en_difference:.1f}'))
        except ValueError as e:
            self.label.text = f"Invalid Input"
        except Exception as e:
            self.label.text = f"An error occurred: {e}"
            Clipboard.copy(self.label.text)

    def change_screen(self, instance):
        self.manager.current = 'first_screen'

class MyApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(FirstScreen(name='first_screen'))
        sm.add_widget(SecondScreen(name='second_screen'))
        return sm

if __name__ == '__main__':
    MyApp().run()
