import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QVBoxLayout, QMessageBox, QTabWidget, QHBoxLayout, QFileDialog, QMenu
)
from PyQt5.QtCore import Qt, QByteArray, QBuffer
from PyQt5.QtGui import QPixmap, QImage
import io

DB_PATH = 'mnemonic.db'

def get_random_word():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT word, story, note, image FROM mnemonic_words ORDER BY RANDOM() LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return row  # (word, story, note, image)
    return None

class RandomWordTab(QWidget):
    def __init__(self):
        super().__init__()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        
        self.word_label = QLabel("Random Word:")
        self.word_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.word_display = QLabel("")
        self.word_display.setStyleSheet("font-size: 28px; font-weight: bold; color: #2a7ae2; padding: 12px; border: 2px solid #2a7ae2; border-radius: 8px; background: #f0f7ff;")
        self.word_display.setAlignment(Qt.AlignCenter)

        self.toggle_btn = QPushButton("Show Story & Note")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setStyleSheet("font-size: 14px; padding: 8px 16px;")
        self.toggle_btn.toggled.connect(self.toggle_details)

        self.story_label = QLabel("Mnemonic Story:")
        self.story_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444;")
        self.story_display = QLabel("")
        self.story_display.setWordWrap(True)
        self.story_display.setStyleSheet("font-size: 14px; background: #f9f9f9; border: 1px solid #ccc; border-radius: 6px; padding: 8px;")
        self.story_label.hide()
        self.story_display.hide()

        self.note_label = QLabel("Note:")
        self.note_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #444;")
        self.note_display = QLabel("")
        self.note_display.setWordWrap(True)
        self.note_display.setStyleSheet("font-size: 13px; background: #f6f6f6; border: 1px dashed #aaa; border-radius: 6px; padding: 8px; color: #555;")
        self.note_label.hide()
        self.note_display.hide()

        self.next_btn = QPushButton("Next Random Word")
        self.next_btn.setStyleSheet("font-size: 14px; padding: 8px 16px; background: #2a7ae2; color: white; border-radius: 6px;")
        self.next_btn.clicked.connect(self.load_random_word)

        # Layouts for better spacing
        word_layout = QVBoxLayout()
        word_layout.addWidget(self.word_label)
        word_layout.addWidget(self.word_display)

        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()

        story_layout = QVBoxLayout()
        story_layout.addWidget(self.story_label)
        story_layout.addWidget(self.story_display)

        note_layout = QVBoxLayout()
        note_layout.addWidget(self.note_label)
        note_layout.addWidget(self.note_display)

        main_layout = QVBoxLayout()
        main_layout.addLayout(word_layout)
        main_layout.addLayout(toggle_layout)
        main_layout.addLayout(story_layout)
        main_layout.addLayout(note_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.next_btn, alignment=Qt.AlignRight)
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)

        self.load_random_word()

    def load_random_word(self):
        result = get_random_word()
        word, story, note, image = result
        while "QUANT" in story:
            print("Found QUANT word in story, fetching another random word...")
            result = get_random_word()
            word, story, note, image = result
        if result:
            self.word_display.setText(word)
            self.story_display.setText(story)
            self.note_display.setText(note if note else "")
            self.toggle_btn.setChecked(False)
            self.story_label.hide()
            self.story_display.hide()
            self.note_label.hide()
            self.note_display.hide()
            if image:
                pixmap = QPixmap()
                pixmap.loadFromData(image)
                self.image_label.setPixmap(pixmap.scaledToWidth(200, Qt.SmoothTransformation))
            else:
                self.image_label.clear()
        else:
            self.word_display.setText("No words found in database.")
            self.story_display.setText("")
            self.note_display.setText("")
            self.toggle_btn.setChecked(False)
            self.story_label.hide()
            self.story_display.hide()
            self.note_label.hide()
            self.note_display.hide()
            self.image_label.clear()

    def toggle_details(self, checked):
        if checked:
            self.toggle_btn.setText("Hide Story & Note")
            self.story_label.show()
            self.story_display.show()
            self.note_label.show()
            self.note_display.show()
        else:
            self.toggle_btn.setText("Show Story & Note")
            self.story_label.hide()
            self.story_display.hide()
            self.note_label.hide()
            self.note_display.hide()
            
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
    # Add note column if it doesn't exist
    cursor.execute("PRAGMA table_info(mnemonic_words)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'note' not in columns:
        cursor.execute("ALTER TABLE mnemonic_words ADD COLUMN note TEXT")
    if 'image' not in columns:
        cursor.execute("ALTER TABLE mnemonic_words ADD COLUMN image BLOB")
    conn.commit()
    conn.close()
    
def save_mnemonic(word, story, note, image_data=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO mnemonic_words (word, story, note, image) VALUES (?, ?, ?, ?)",
            (word, story, note, image_data)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"The word '{word}' already exists.")
    finally:
        conn.close()

def get_mnemonic_story(word):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT story, note FROM mnemonic_words WHERE word = ?', (word,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row  # (story, note)
    return None

class InsertTab(QWidget):
    def __init__(self):
        super().__init__()

        self.word_label = QLabel("Word:")
        self.word_input = QLineEdit()

        self.story_label = QLabel("Mnemonic Story:")
        self.story_input = QTextEdit()

        self.note_label = QLabel("Note:")
        self.note_input = QTextEdit()

        self.image_label = QLabel("No image selected")
        self.image_btn = QPushButton("Upload Image")
        self.image_btn.clicked.connect(self.show_image_menu)
        self.image_data = None

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.submit_form)

        layout = QVBoxLayout()
        layout.addWidget(self.word_label)
        layout.addWidget(self.word_input)
        layout.addWidget(self.story_label)
        layout.addWidget(self.story_input)
        layout.addWidget(self.note_label)
        layout.addWidget(self.note_input)
        layout.addWidget(self.image_btn)
        layout.addWidget(self.image_label)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)
        
    def show_image_menu(self):
        menu = QMenu()
        upload_action = menu.addAction("Upload from File")
        clipboard_action = menu.addAction("Paste from Clipboard")
        action = menu.exec_(self.image_btn.mapToGlobal(self.image_btn.rect().bottomLeft()))
        if action == upload_action:
            self.upload_image()
        elif action == clipboard_action:
            self.paste_image_from_clipboard()

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            with open(file_path, "rb") as f:
                self.image_data = f.read()
            self.image_label.setText(f"Selected: {file_path.split('/')[-1]}")
        else:
            self.image_data = None
            self.image_label.setText("No image selected")
    
    def paste_image_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasImage():
            image = clipboard.image()
            pixmap = QPixmap.fromImage(image)
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QBuffer.WriteOnly)
            pixmap.save(buffer, "PNG")
            self.image_data = ba.data()
            self.image_label.setText("Image pasted from clipboard")
        else:
            self.image_data = None
            self.image_label.setText("No image in clipboard")

    def submit_form(self):
        word = self.word_input.text().strip()
        story = self.story_input.toPlainText().strip()
        note = self.note_input.toPlainText().strip()
        image = self.image_data
        if not word or not story:
            QMessageBox.warning(self, "Input Error", "Please enter both word and story.")
            return
        try:
            save_mnemonic(word, story, note, image)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        
        QMessageBox.information(self, "Success", f"Mnemonic for '{word}' saved!")
        self.word_input.clear()
        self.story_input.clear()
        self.note_input.clear()
        self.image_data = None
        self.image_label.setText("No image selected")
        
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
        
        result = get_mnemonic_story(word)
        if result:
            story, note = result
            text = f"Mnemonic for '{word}':\n\n{story}"
            if note:
                text += f"\n\nNote:\n{note}"
            self.result_label.setText(text)
        else:
            self.result_label.setText(f"No mnemonic story found for '{word}'.")

class MnemonicApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GRE Mnemonic Stories")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.insert_tab = InsertTab()
        self.search_tab = SearchTab()
        self.random_tab = RandomWordTab()

        self.tabs.addTab(self.insert_tab, "Add Mnemonic")
        self.tabs.addTab(self.search_tab, "Search Mnemonic")
        self.tabs.addTab(self.random_tab, "Random Word")

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
