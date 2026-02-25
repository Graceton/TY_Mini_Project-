# hover_reader.py
import sys
import cv2
import pytesseract
import pyttsx3
import pyautogui
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
import time

# Path to Tesseract (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class HoverReaderThread(QThread):
    update_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.engine = pyttsx3.init()
        self.last_text = ""
        self.interval = 1.5  # seconds between reads

    def run(self):
        while self.running:
            x, y = pyautogui.position()
            # Capture a small region around cursor
            region = (x - 100, y - 50, 200, 100)
            screenshot = pyautogui.screenshot(region=region)
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # OCR to extract text
            text = pytesseract.image_to_string(frame, lang="eng").strip()

            if text and text != self.last_text:
                self.last_text = text
                self.update_text.emit(text)
                self.engine.say(text)
                self.engine.runAndWait()

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.engine.stop()

class HoverReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optivox - Hover to Read")
        self.setGeometry(100, 100, 420, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #1a1a1a; color: white; font-size: 16px; border-radius: 10px;")

        layout = QVBoxLayout()
        self.label = QLabel("🖱️ Hover over text to hear it aloud", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Start background reader
        self.thread = HoverReaderThread()
        self.thread.update_text.connect(self.showText)
        self.thread.start()

    def showText(self, text):
        self.label.setText(f"🔊 {text}")

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = HoverReader()
    reader.show()
    sys.exit(app.exec_())
