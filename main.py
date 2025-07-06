import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QVBoxLayout, QMessageBox, QTabWidget, QHBoxLayout
)

DB_PATH = 'mnemonic.db'

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mnemonic_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            story TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_mnemonic(word, story):
    conn = sqlite3.connect('mnemonic.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO mnemonic_words (word, story) VALUES (?, ?)",
            (word, story)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"The word '{word}' already exists.")
    finally:
        conn.close()

def get_mnemonic_story(word):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT story FROM mnemonic_words WHERE word = ?', (word,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

class InsertTab(QWidget):
    def __init__(self):
        super().__init__()

        self.word_label = QLabel("Word:")
        self.word_input = QLineEdit()

        self.story_label = QLabel("Mnemonic Story:")
        self.story_input = QTextEdit()

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.submit_form)

        layout = QVBoxLayout()
        layout.addWidget(self.word_label)
        layout.addWidget(self.word_input)
        layout.addWidget(self.story_label)
        layout.addWidget(self.story_input)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)

    def submit_form(self):
        word = self.word_input.text().strip()
        story = self.story_input.toPlainText().strip()
        if not word or not story:
            QMessageBox.warning(self, "Input Error", "Please enter both word and story.")
            return
        try:
            save_mnemonic(word, story)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        
        QMessageBox.information(self, "Success", f"Mnemonic for '{word}' saved!")
        self.word_input.clear()
        self.story_input.clear()

class SearchTab(QWidget):
    def __init__(self):
        super().__init__()

        self.word_label = QLabel("Enter Word to Search:")
        self.word_input = QLineEdit()

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_story)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.word_label)
        top_layout.addWidget(self.word_input)
        top_layout.addWidget(self.search_btn)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def search_story(self):
        word = self.word_input.text().strip()
        if not word:
            QMessageBox.warning(self, "Input Error", "Please enter a word to search.")
            return
        
        story = get_mnemonic_story(word)
        if story:
            self.result_label.setText(f"Mnemonic for '{word}':\n\n{story}")
        else:
            self.result_label.setText(f"No mnemonic story found for '{word}'.")

class MnemonicApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GRE Mnemonic Stories")
        self.setGeometry(100, 100, 600, 400)

        self.tabs = QTabWidget()
        self.insert_tab = InsertTab()
        self.search_tab = SearchTab()

        self.tabs.addTab(self.insert_tab, "Add Mnemonic")
        self.tabs.addTab(self.search_tab, "Search Mnemonic")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)


def main():
    create_table()
    app = QApplication(sys.argv)
    window = MnemonicApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
