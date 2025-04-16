# rebuild test
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
# Import FormulaError for specific exception handling
from molmass import Formula, FormulaError, elements
from kivy.core.clipboard import Clipboard
# Import dp for density-independent pixels
from kivy.metrics import dp
import re
import logging # Optional: for better error logging

# Configure basic logging (optional, but helpful for debugging)
logging.basicConfig(level=logging.INFO)

# Helper function to get electronegativity safely
def _get_electronegativity(element_symbol):
    """Safely retrieves electronegativity for a capitalized element symbol."""
    try:
        # molmass element symbols are typically capitalized (e.g., 'He', 'Cl')
        symbol_cap = element_symbol.capitalize()
        el = elements.ELEMENTS[symbol_cap]
        return el.eleneg
    except KeyError:
        # Element symbol not found in molmass data
        return None
    except AttributeError:
        # Element exists but might not have electronegativity data (unlikely for common elements)
        logging.warning(f"Electronegativity data missing for {symbol_cap}")
        return None

# Revised helper function specifically for splitting two element symbols for EN screen
def _split_elements_for_en(compound_str):
    """
    Parses a string expecting exactly two element symbols (e.g., "NaCl", "HF").
    Prioritizes valid two-letter symbols over one-letter symbols.
    Raises ValueError if input is not exactly two valid symbols.
    """
    found_elements = []
    i = 0
    n = len(compound_str)
    if not n:
        raise ValueError("Input cannot be empty.")

    while i < n:
        # Check for two-letter symbol first
        if i + 1 < n:
            potential_symbol = compound_str[i:i+2]
            # Check if it looks like a symbol (isalpha) and exists in molmass
            if potential_symbol.isalpha() and _get_electronegativity(potential_symbol) is not None:
                found_elements.append(potential_symbol.capitalize())
                i += 2
                continue # Skip one-letter check

        # Check for one-letter symbol
        potential_symbol = compound_str[i]
        if potential_symbol.isalpha() and _get_electronegativity(potential_symbol) is not None:
            found_elements.append(potential_symbol.capitalize())
            i += 1
            continue # Move to next character

        # If neither a valid 1-letter nor 2-letter symbol starts here, it's an error
        raise ValueError(f"Invalid character or sequence: '{compound_str[i]}'")

    # Final check - ensure exactly two elements were found
    if len(found_elements) != 2:
        raise ValueError("Input must contain exactly two valid element symbols (e.g., 'NaCl', 'HF').")

    return found_elements


class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)) # Add spacing and padding

        # Top Bar for Navigation Button
        top_bar = BoxLayout(size_hint_y=None, height=dp(50))
        # Spacer to push button right
        top_bar.add_widget(BoxLayout(size_hint_x=0.8))
        switch_button = Button(
            text='EN',
            size_hint=(None, None),
            size=(dp(60), dp(40)),
            pos_hint={'top': 1} # Anchor to top within its layout space
        )
        switch_button.bind(on_release=self.change_screen)
        top_bar.add_widget(switch_button)
        layout.add_widget(top_bar)

        # Input field
        self.input = TextInput(
            hint_text='Enter formula (e.g., H2O, 2NaCl, Ca(OH)2)',
            multiline=False,
            halign="center",
            font_size='30sp', # Use sp for scalable fonts
            size_hint_y=None, # Disable vertical size hinting
            height=dp(80),    # Set explicit height
            padding=[dp(10)]  # Use dp for padding
        )
        self.input.bind(on_text_validate=self.calculate)
        layout.add_widget(self.input)

        # Calculate Button in its own layout for positioning
        button_layout = BoxLayout(size_hint_y=None, height=dp(80), padding=(dp(20), dp(10))) # Add padding
        calc_button = Button(
            text='Calculate Molecular Mass',
            font_size='20sp', # Adjust as needed
            size_hint=(1, 1) # Fill the button_layout
        )
        calc_button.bind(on_press=self.calculate)
        button_layout.add_widget(calc_button)
        layout.add_widget(button_layout)

        # Result Label
        self.label = Label(
            text='',
            halign="center",
            valign="top", # Align text to top
            font_size='25sp', # Adjust as needed
            size_hint_y=1 # Allow label to take remaining vertical space
            )
        layout.add_widget(self.label)

        self.add_widget(layout)

    def change_screen(self, instance):
        self.manager.current = 'second_screen'
        self.label.text = '' # Clear label on screen change
        self.input.text = '' # Clear input on screen change

    def calculate(self, instance):
        input_text = self.input.text.strip() # Remove leading/trailing whitespace
        if not input_text:
            self.label.text = "Please enter a formula."
            return
        try:
            # Let molmass handle the parsing directly
            f = Formula(input_text)
            mass_value = f.mass
            mass_str = f"{mass_value:.3f}" # Format to 3 decimal places
            self.label.text = f"Molecular Mass:\n{mass_str} g/mol" # Added units
            Clipboard.copy(mass_str)
            # Optional: add feedback like "Copied!" temporarily
        except FormulaError as e:
            # Catch specific molmass error
            logging.error(f"FormulaError for input '{input_text}': {e}")
            self.label.text = f"Invalid Formula:\n{e}"
        except Exception as e:
            # Catch any other unexpected errors during calculation
            logging.exception(f"Unexpected error calculating mass for '{input_text}':") # Log full traceback
            self.label.text = "An unexpected error occurred.\nPlease check the input."


class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10)) # Add spacing and padding

        # Top Bar for Navigation Button
        top_bar = BoxLayout(size_hint_y=None, height=dp(50))
         # Spacer to push button right
        top_bar.add_widget(BoxLayout(size_hint_x=0.8))
        switch_button = Button(
            text='MM',
            size_hint=(None, None),
            size=(dp(60), dp(40)),
            pos_hint={'top': 1} # Anchor to top within its layout space
        )
        switch_button.bind(on_release=self.change_screen)
        top_bar.add_widget(switch_button)
        layout.add_widget(top_bar)

        # Input field
        self.input = TextInput(
            hint_text='Enter two elements (e.g., HF, NaCl)',
            multiline=False,
            halign="center",
            font_size='30sp', # Use sp for scalable fonts
            size_hint_y=None, # Disable vertical size hinting
            height=dp(80),    # Set explicit height
            padding=[dp(10)]  # Use dp for padding
        )
        self.input.bind(on_text_validate=self.get_electronegativity_difference)
        layout.add_widget(self.input)

        # Calculate Button in its own layout for positioning
        button_layout = BoxLayout(size_hint_y=None, height=dp(80), padding=(dp(20), dp(10))) # Add padding
        calc_button = Button(
            text='Calculate EN Difference',
            font_size='20sp', # Adjust as needed
            size_hint=(1, 1) # Fill the button_layout
        )
        calc_button.bind(on_press=self.get_electronegativity_difference)
        button_layout.add_widget(calc_button)
        layout.add_widget(button_layout)

        # Result Label
        self.label = Label(
            text='',
            halign="center",
            valign="top", # Align text to top
            font_size='25sp', # Adjust as needed
            size_hint_y=1 # Allow label to take remaining vertical space
        )
        layout.add_widget(self.label)

        self.add_widget(layout)

    def get_electronegativity_difference(self, instance=None):
        input_text = self.input.text.strip() # Remove leading/trailing whitespace
        if not input_text:
            self.label.text = "Please enter two element symbols."
            return
        try:
            # Use the revised helper function to parse exactly two symbols
            elements_list = _split_elements_for_en(input_text)
            el1_sym, el2_sym = elements_list[0], elements_list[1]

            en1 = _get_electronegativity(el1_sym)
            en2 = _get_electronegativity(el2_sym)

            # Should not happen if _split_elements_for_en and _get_electronegativity work, but double check
            if en1 is None or en2 is None:
                raise ValueError("Could not retrieve electronegativity for one or both symbols.")

            en_difference = abs(en1 - en2)
            bond_type = ""
            # Standard Pauling scale cutoffs for bond type based on EN difference
            if en_difference <= 0.4: # Adjusted slightly, sometimes 0.4 is used as boundary
                bond_type = "Nonpolar Covalent"
            elif en_difference < 1.7: # Sometimes 1.7, 1.8 or 2.0 are used as boundary
                bond_type = "Polar Covalent"
            else:
                bond_type = "Ionic"

            # Format output nicely
            result_text = (
                f"Symbols: {el1_sym}, {el2_sym}\n"
                f"EN Values: {en1:.2f}, {en2:.2f}\n"
                f"Difference (|ΔEN|): |{en1:.2f} - {en2:.2f}| = {en_difference:.2f}\n"
                f"Predicted Bond Type: {bond_type}"
            )
            self.label.text = result_text
            Clipboard.copy(f"{en_difference:.2f}") # Copy just the numerical difference

        except ValueError as e:
            # Catch errors from _split_elements_for_en or _get_electronegativity checks
            logging.error(f"ValueError getting EN difference for '{input_text}': {e}")
            self.label.text = f"Invalid Input:\n{e}"
        except Exception as e:
            # Catch any other unexpected errors
            logging.exception(f"Unexpected error getting EN difference for '{input_text}':")
            self.label.text = "An unexpected error occurred.\nPlease check the input."

    def change_screen(self, instance):
        self.manager.current = 'first_screen'
        self.label.text = '' # Clear label on screen change
        self.input.text = '' # Clear input on screen change

class MyApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(FirstScreen(name='first_screen'))
        sm.add_widget(SecondScreen(name='second_screen'))
        return sm

if __name__ == '__main__':
    MyApp().run()