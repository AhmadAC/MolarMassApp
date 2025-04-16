# chem_calc_gui.py
# Purpose: Provides a PySide6 GUI for calculating Molecular Mass and Electronegativity Difference.
# Replaces the Kivy version.
# v1.3: Corrected special case check for "CO" to be case-sensitive.

import sys
import logging
from pathlib import Path

# --- Qt Imports ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QStackedWidget, QSizePolicy
)
from PySide6.QtGui import QFont, QClipboard, QIcon
from PySide6.QtCore import Qt, Slot, QMetaObject, Q_ARG

# --- Calculation Logic Imports ---
from molmass import Formula, FormulaError, elements

# --- Configure basic logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions (Remain the same as v1.2 - the parser correctly handles 'Co' already) ---

def _get_electronegativity(element_symbol):
    """Safely retrieves electronegativity for a capitalized element symbol."""
    if not element_symbol or not element_symbol.isalpha():
        return None
    try:
        symbol_cap = element_symbol.capitalize()
        el = elements.ELEMENTS[symbol_cap]
        en = getattr(el, 'eleneg', None)
        if en is None:
            logging.warning(f"Electronegativity data missing for {symbol_cap}")
        return en
    except KeyError:
        return None
    except Exception as e:
        logging.error(f"Unexpected error getting EN for {element_symbol}: {e}")
        return None

def _split_elements_for_en(compound_str):
    """
    Parses a string expecting exactly two adjacent element symbols (e.g., "NaCl", "HF").
    It identifies the first valid element (1 or 2 letters), then the second
    valid element immediately after, ensuring the entire string is consumed.
    Raises ValueError if input format is incorrect or only one element is found.
    """
    text = compound_str.strip()
    n = len(text)
    if n < 1 or n > 4: # Relaxed initial check, more specific errors later
        raise ValueError("Input must contain one or two adjacent element symbols (e.g., 'Na', 'Cl', 'NaCl', 'HF').")

    elements_found = []
    current_pos = 0

    # Find first element
    first_el = None
    if current_pos + 2 <= n: # Try 2 letters first
        potential_el_2 = text[current_pos:current_pos+2]
        if _get_electronegativity(potential_el_2) is not None:
            first_el = potential_el_2
            current_pos += 2
    if first_el is None and current_pos + 1 <= n: # Try 1 letter
        potential_el_1 = text[current_pos:current_pos+1]
        if _get_electronegativity(potential_el_1) is not None:
            first_el = potential_el_1
            current_pos += 1

    if first_el is None:
        raise ValueError(f"Could not identify a valid first element symbol starting with '{text[0]}'.")
    elements_found.append(first_el.capitalize())

    # Check if only one element was found and it consumed the whole string
    if current_pos == n:
         raise ValueError("Input contains only one element symbol. Expected two for EN difference.")

    # Find second element immediately following
    second_el = None
    remaining_len = n - current_pos
    if remaining_len == 0: # Should be caught above, but defensive check
         raise ValueError("Found first element, but no characters remaining for the second.")

    if current_pos + 2 <= n: # Try 2 letters second if possible
        potential_el_2 = text[current_pos:current_pos+2]
        if _get_electronegativity(potential_el_2) is not None:
            second_el = potential_el_2
            current_pos += 2
    if second_el is None and current_pos + 1 <= n: # Try 1 letter second
        potential_el_1 = text[current_pos:current_pos+1]
        if _get_electronegativity(potential_el_1) is not None:
            second_el = potential_el_1
            current_pos += 1

    if second_el is None:
        raise ValueError(f"Found '{first_el}', but could not identify a valid second element symbol starting at index {len(first_el)}.")
    elements_found.append(second_el.capitalize())

    if current_pos != n: # Final check: Did we consume the entire string?
        raise ValueError("Input contains extra characters after the two expected element symbols.")

    return elements_found


# --- Screen Widgets (BaseScreen, MMCalculatorScreen remain unchanged) ---

class BaseScreen(QWidget):
    """ Base class for common screen elements """
    def __init__(self, switch_button_text, switch_callback, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(15, 15, 15, 15)

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch(1)
        self.switch_button = QPushButton(switch_button_text)
        self.switch_button.setMinimumSize(60, 40)
        self.switch_button.setMaximumWidth(80)
        self.switch_button.clicked.connect(switch_callback)
        top_bar_layout.addWidget(self.switch_button)
        self.layout.addLayout(top_bar_layout)

        self.input_field = QLineEdit()
        font_input = QFont(); font_input.setPointSize(18)
        self.input_field.setFont(font_input)
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_field.setMinimumHeight(50)
        self.input_field.setPlaceholderText("Enter value here")
        self.layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        self.calc_button = QPushButton("Calculate")
        font_button = QFont(); font_button.setPointSize(14)
        self.calc_button.setFont(font_button)
        self.calc_button.setMinimumHeight(50)
        self.layout.addWidget(self.calc_button)

        self.result_label = QLabel("")
        font_label = QFont(); font_label.setPointSize(16)
        self.result_label.setFont(font_label)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)
        self.result_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.result_label, stretch=1)

    def clear_fields(self):
        self.input_field.clear()
        self.result_label.clear()
        self.result_label.setStyleSheet("")

class MMCalculatorScreen(BaseScreen):
    """ Screen for Molecular Mass calculation """
    def __init__(self, switch_callback, parent=None):
        super().__init__("EN", switch_callback, parent)
        self.input_field.setPlaceholderText("Enter formula (e.g., H2O, 2NaCl)")
        self.input_field.returnPressed.connect(self.calculate_mm)
        self.calc_button.setText("Calculate Molecular Mass")
        self.calc_button.clicked.connect(self.calculate_mm)

    @Slot()
    def calculate_mm(self):
        self.result_label.setStyleSheet("")
        input_text = self.input_field.text().strip()
        logging.info(f"MM Calculation requested for input: '{input_text}'")
        if not input_text:
            self.result_label.setText("Please enter a formula.")
            return
        try:
            f = Formula(input_text)
            mass_value = f.mass
            mass_str = f"{mass_value:.3f}"
            self.result_label.setText(f"Molecular Mass:\n{mass_str} g/mol")
            clipboard = QApplication.clipboard()
            if clipboard: clipboard.setText(mass_str)
            else: logging.warning("Could not access clipboard.")
        except FormulaError as e:
            logging.error(f"FormulaError for input '{input_text}': {e}")
            self.result_label.setText(f"Invalid Formula:\n{e}")
            self.result_label.setStyleSheet("color: red;")
        except Exception as e:
            logging.exception(f"Unexpected error calculating mass for '{input_text}':")
            self.result_label.setText("An unexpected error occurred.\nPlease check the input and logs.")
            self.result_label.setStyleSheet("color: red;")


class ENCalculatorScreen(BaseScreen):
    """ Screen for Electronegativity Difference calculation """
    def __init__(self, switch_callback, parent=None):
        super().__init__("MM", switch_callback, parent)
        self.input_field.setPlaceholderText("Enter two elements (e.g., HF, NaCl, CO)")
        self.input_field.returnPressed.connect(self.calculate_en_difference)
        self.calc_button.setText("Calculate EN Difference")
        self.calc_button.clicked.connect(self.calculate_en_difference)

    @Slot()
    def calculate_en_difference(self):
        self.result_label.setStyleSheet("") # Reset potential error state
        input_text = self.input_field.text().strip()
        logging.info(f"EN Difference calculation requested for input: '{input_text}'")
        if not input_text:
            self.result_label.setText("Please enter two element symbols.")
            return

        try:
            elements_list = None
            # --- CORRECTED SPECIAL CASE CHECK for "CO" (Case-Sensitive) ---
            if input_text == 'CO': # Check for exact match "CO"
                logging.info("Applying special case elements for 'CO': ['C', 'O']")
                elements_list = ['C', 'O']
            else:
                # Use the standard helper function for other inputs
                logging.debug(f"Using standard parser for '{input_text}'")
                elements_list = _split_elements_for_en(input_text)
            # --- End Special Case ---

            # --- Proceed with elements_list ---
            # (The _split_elements_for_en function now raises appropriate errors if not exactly 2 elements)
            if not elements_list: # Should not happen if parser/case worked, but defensive check
                 raise ValueError("Internal error: Element list not determined.")

            el1_sym, el2_sym = elements_list[0], elements_list[1] # Already capitalized

            en1 = _get_electronegativity(el1_sym)
            en2 = _get_electronegativity(el2_sym)

            missing_en = []
            if en1 is None: missing_en.append(el1_sym)
            if en2 is None: missing_en.append(el2_sym)
            if missing_en:
                raise ValueError(f"Electronegativity data unavailable for: {', '.join(missing_en)}")

            en_difference = abs(en1 - en2)
            bond_type = ""
            if en_difference <= 0.4: bond_type = "Nonpolar Covalent"
            elif en_difference < 1.7: bond_type = "Polar Covalent"
            else: bond_type = "Ionic"

            result_text = (
                f"Symbols: {el1_sym}, {el2_sym}\n"
                f"EN Values: {en1:.2f}, {en2:.2f}\n"
                f"Difference (|ΔEN|): |{en1:.2f} - {en2:.2f}| = {en_difference:.2f}\n"
                f"Predicted Bond Type: {bond_type}"
            )
            self.result_label.setText(result_text)
            clipboard = QApplication.clipboard()
            if clipboard: clipboard.setText(f"{en_difference:.2f}")
            else: logging.warning("Could not access clipboard.")

        except ValueError as e: # Catches errors from _split_elements_for_en or missing EN data
            logging.error(f"ValueError getting EN difference for '{input_text}': {e}")
            self.result_label.setText(f"Invalid Input:\n{e}") # Show the specific error
            self.result_label.setStyleSheet("color: red;")
        except Exception as e:
            logging.exception(f"Unexpected error getting EN difference for '{input_text}':")
            self.result_label.setText("An unexpected error occurred.\nPlease check the input and logs.")
            self.result_label.setStyleSheet("color: red;")


# --- Main Application Window (ChemCalcApp remains unchanged) ---

class ChemCalcApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemistry Calculator")
        self.setGeometry(200, 200, 480, 500)

        icon_path = Path(__file__).resolve().parent / "chem_icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
            logging.info(f"Loaded icon from: {icon_path}")
        else:
            logging.info(f"Icon file not found: {icon_path} (optional)")

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.mm_screen = MMCalculatorScreen(switch_callback=self.show_en_screen)
        self.en_screen = ENCalculatorScreen(switch_callback=self.show_mm_screen)

        self.stacked_widget.addWidget(self.mm_screen) # Index 0
        self.stacked_widget.addWidget(self.en_screen) # Index 1

        self.setCentralWidget(self.central_widget)
        self.show_mm_screen() # Start on MM screen

    @Slot()
    def show_mm_screen(self):
        if self.stacked_widget.currentIndex() != 0:
            logging.info("Switching to MM Screen")
            self.stacked_widget.setCurrentIndex(0)
            self.en_screen.clear_fields()
            self.mm_screen.input_field.setFocus()

    @Slot()
    def show_en_screen(self):
        if self.stacked_widget.currentIndex() != 1:
            logging.info("Switching to EN Screen")
            self.stacked_widget.setCurrentIndex(1)
            self.mm_screen.clear_fields()
            self.en_screen.input_field.setFocus()

    def closeEvent(self, event):
        logging.info("Closing Chem Calculator.")
        super().closeEvent(event)


# --- Main Execution (remains unchanged) ---
if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = ChemCalcApp()
    window.show()
    sys.exit(app.exec())
