# hover_reader.py
import sys
import cv2
import pytesseract
import pyttsx3
import pyautogui
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pytesseract import Output
import time
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings.settings import SettingsManager

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class HoverReaderThread(QThread):
    update_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.running = True
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.settings.get("speech_rate"))
        self.engine.setProperty('volume', self.settings.get("speech_volume"))
        self.last_text = ""
        self.interval = 0.5  # Faster scanning since we only read one word

    def run(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        while self.running:
            mx, my = pyautogui.position()
            
            # Widen the capture area slightly so tesseract has context
            w, h = 400, 100
            left, top = mx - w // 2, my - h // 2
            
            region = (left, top, w, h)
            try:
                screenshot = pyautogui.screenshot(region=region)
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Get bounding boxes of every word in the image
                lang = self.settings.get("ocr_language")
                data = pytesseract.image_to_data(frame, output_type=Output.DICT, lang=lang)

                hovered_word = None

                # Image coords vs Screen coords mapping
                for i in range(len(data['text'])):
                    word = data['text'][i].strip()
                    if not word:
                        continue

                    # Bounding box of the word relative to the 400x100 screenshot
                    wx = data['left'][i]
                    wy = data['top'][i]
                    ww = data['width'][i]
                    wh = data['height'][i]

                    # Convert screenshot coords back to absolute screen coords
                    abs_x = left + wx
                    abs_y = top + wy

                    # Check if the physical mouse (mx, my) is inside this absolute bounding box
                    if abs_x <= mx <= abs_x + ww and abs_y <= my <= abs_y + wh:
                        hovered_word = word
                        break

                if hovered_word and hovered_word != self.last_text:
                    self.last_text = hovered_word
                    self.update_text.emit(hovered_word)
                    self.engine.say(hovered_word)
                    self.engine.runAndWait()

            except Exception:
                pass

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.engine.stop()

class HoverReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optivox - Hover to Read")
        self.setGeometry(100, 100, 420, 140)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #1a1a1a; color: white; font-size: 20px; border-radius: 10px; font-weight: bold;")

        layout = QVBoxLayout()
        self.label = QLabel("🖱️ Point at a word to read it", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        from PyQt5.QtWidgets import QPushButton
        self.close_btn = QPushButton("❌ Close Reader")
        self.close_btn.setStyleSheet("background-color: #c0392b; font-size: 14px; padding: 5px; border-radius: 5px;")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)

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
