# full_reader.py
import sys
import cv2
import pytesseract
import pyttsx3
import pyautogui
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import time

# Configure Tesseract path (update if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class FullReaderThread(QThread):
    update_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.engine = pyttsx3.init()

    def run(self):
        while self.running:
            # Capture full screen
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # OCR text extraction
            text = pytesseract.image_to_string(frame, lang="eng").strip()

            if text:
                self.update_text.emit("Reading detected text...")
                self.engine.say(text)
                self.engine.runAndWait()

            time.sleep(5)  # Pause before next scan

    def start_reading(self):
        self.running = True
        self.start()

    def stop_reading(self):
        self.running = False
        self.engine.stop()

class FullReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optivox - Full Screen Reader")
        self.setGeometry(100, 100, 500, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #101010;
            color: white;
            font-size: 16px;
            border-radius: 15px;
        """)

        layout = QVBoxLayout()
        self.label = QLabel("📖 Full-Screen Reader Ready", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("▶️ Start Reading")
        self.stop_btn = QPushButton("⏹️ Stop Reading")
        self.start_btn.clicked.connect(self.start_reading)
        self.stop_btn.clicked.connect(self.stop_reading)

        for btn in [self.start_btn, self.stop_btn]:
            btn.setStyleSheet("background-color: #303030; color: white; border-radius: 10px; padding: 8px;")

        layout.addWidget(self.label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        self.setLayout(layout)

        self.reader_thread = FullReaderThread()
        self.reader_thread.update_text.connect(self.show_status)

    def start_reading(self):
        self.label.setText("🔊 Reading text from screen...")
        self.reader_thread.start_reading()

    def stop_reading(self):
        self.label.setText("⏸️ Reading stopped")
        self.reader_thread.stop_reading()

    def show_status(self, message):
        self.label.setText(message)

    def closeEvent(self, event):
        self.reader_thread.stop_reading()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = FullReader()
    reader.show()
    sys.exit(app.exec_())
