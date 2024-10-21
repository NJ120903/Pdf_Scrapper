import sys
import re
import fitz  # PyMuPDF
import pdfplumber  # pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract_text
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, 
                             QVBoxLayout, QWidget, QHBoxLayout, QLabel, QComboBox, QLineEdit, QDialog, QListWidget, QScrollArea)

class SearchResultDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Results")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # Create a scroll area for the results
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        # Create a widget to hold the results
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)

        for result in results:
            self.results_layout.addWidget(QLabel(result))

        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)


class AdvancedPDFScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Scraper")
        self.setGeometry(100, 100, 1000, 700)

        # Layout and widgets
        layout = QVBoxLayout()
        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)
        layout.addWidget(self.textEdit)

        # Buttons and options layout
        options_layout = QHBoxLayout()

        self.extract_button = QPushButton('Extract PDF', self)
        self.extract_button.clicked.connect(self.open_pdf)
        options_layout.addWidget(self.extract_button)

        self.method_label = QLabel("Select Extraction Method:")
        options_layout.addWidget(self.method_label)

        self.method_combo = QComboBox(self)
        self.method_combo.addItems(["PyMuPDF", "PDFMiner", "pdfplumber", "All (Compare)"])
        options_layout.addWidget(self.method_combo)

        layout.addLayout(options_layout)

        # Search bar and button layout
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter search query...")
        search_layout.addWidget(self.search_bar)

        self.search_button = QPushButton('Search', self)
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.extracted_text = ""  # To hold the extracted text for search functionality

    def open_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_name:
            selected_method = self.method_combo.currentText()
            if selected_method == "PyMuPDF":
                self.extract_text_pymupdf(file_name)
            elif selected_method == "PDFMiner":
                self.extract_text_pdfminer(file_name)
            elif selected_method == "pdfplumber":
                self.extract_text_pdfplumber(file_name)
            elif selected_method == "All (Compare)":
                self.extract_text_all(file_name)

    def extract_text_pymupdf(self, file_name):
        """Extract text using PyMuPDF"""
        doc = fitz.open(file_name)  # Open the PDF file
        self.extracted_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)  # Load each page
            self.extracted_text += page.get_text("text")  # Extract text from each page

        self.textEdit.setText(self.extracted_text)  # Display in the textEdit widget

    def extract_text_pdfminer(self, file_name):
        """Extract text using PDFMiner"""
        self.extracted_text = pdfminer_extract_text(file_name)  # Extract text from PDF
        self.textEdit.setText(self.extracted_text)  # Display in the textEdit widget

    def extract_text_pdfplumber(self, file_name):
        """Extract text using pdfplumber"""
        self.extracted_text = ""
        with pdfplumber.open(file_name) as pdf:
            for page in pdf.pages:
                self.extracted_text += page.extract_text()  # Extract text from each page
        self.textEdit.setText(self.extracted_text)  # Display in the textEdit widget

    def extract_text_all(self, file_name):
        """Extract text using all methods for comparison"""
        # PyMuPDF extraction
        doc = fitz.open(file_name)
        pymupdf_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pymupdf_text += page.get_text("text")

        # PDFMiner extraction
        pdfminer_text = pdfminer_extract_text(file_name)

        # pdfplumber extraction
        pdfplumber_text = ""
        with pdfplumber.open(file_name) as pdf:
            for page in pdf.pages:
                pdfplumber_text += page.extract_text()

        # Combine all results for comparison
        self.extracted_text = "--- Text Extracted using PyMuPDF ---\n" + pymupdf_text
        self.extracted_text += "\n\n--- Text Extracted using PDFMiner ---\n" + pdfminer_text
        self.extracted_text += "\n\n--- Text Extracted using pdfplumber ---\n" + pdfplumber_text

        self.textEdit.setText(self.extracted_text)  # Display in the textEdit widget

    def search_text(self):
        """Search for a query in the extracted text and display results in a dialog."""
        query = self.search_bar.text()
        if query:
            result = self.extract_section(self.extracted_text, query)
            if result:
                self.show_search_results([result])
            else:
                self.show_search_results(["No matches found."])

    def extract_section(self, text, section_title):
        """Extract a specific section based on a general section title, stop when encountering another section."""
        section_text = ""
        lines = text.splitlines()
        section_found = False

        for line in lines:
            if section_title.upper() in line.upper():
                section_found = True
                section_text += line + "\n"
            elif section_found:
                if self.is_new_section(line) or line.strip() == "":
                    break  # Stop when encountering a new section or empty line
                section_text += line + "\n"

        return section_text.strip()

    def is_new_section(self, line):
        """Determine if a line marks the beginning of a new section (e.g., all uppercase or specific patterns)."""
        return bool(re.match(r'^[A-Z\s]+$', line.strip()))

    def show_search_results(self, results):
        """Open a new dialog to show search results"""
        dialog = SearchResultDialog(results, self)
        dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdvancedPDFScraperApp()
    window.show()
    sys.exit(app.exec_())
