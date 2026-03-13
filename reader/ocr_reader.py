import sys
import os
import asyncio
import threading
import edge_tts
import pygame
import tempfile
import os
import mss
import numpy as np
import pytesseract
import cv2
import re
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen
import pyautogui
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings.settings import SettingsManager

pygame.mixer.init()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class OCROverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        # Cover the entire virtual screen (all monitors)
        screen_geometry = QApplication.desktop().geometry()
        self.setGeometry(screen_geometry)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_drawing = False

        # Dim the screen
        self.dim_color = QColor(0, 0, 0, 100)
        self.selection_color = QColor(255, 50, 50, 150)
        
        # TTS Engine Loop
        self.speech_id = 0
        self.tts_loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_event_loop, args=(self.tts_loop,), daemon=True).start()

    def _run_event_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Dim whole screen
        painter.fillRect(self.rect(), self.dim_color)
        
        # Draw selection rectangle
        if not self.begin.isNull() and not self.end.isNull():
            rect = QRect(self.begin, self.end).normalized()
            # Clear the dimming inside the box
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # Draw a border around it
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(self.selection_color, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = event.pos()
            self.is_drawing = True
            self.update()
        elif event.button() == Qt.RightButton:
            # Cancel on right click
            self.close()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end = event.pos()
            self.is_drawing = False
            self.update()
            self.process_selected_area()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def process_selected_area(self):
        rect = QRect(self.begin, self.end).normalized()
        if rect.width() < 10 or rect.height() < 10:
            self.close()
            return

        region = {
            "top": rect.top(),
            "left": rect.left(),
            "width": rect.width(),
            "height": rect.height()
        }

        # Hide overlay so it doesn't get caught in the screenshot
        self.hide()
        QApplication.processEvents()
        
        # Give DWM a moment to clear the translucent window from the screen buffer
        import time
        time.sleep(0.15)
        
        with mss.mss() as sct:
            img = np.array(sct.grab(region))
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            # Thresholding for better OCR
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # Read text line-by-line block structure
            lang = self.settings.get("ocr_language")
            text = pytesseract.image_to_string(gray, lang=lang, config="--oem 1 --psm 6").strip()

            filtered_text = " ".join(text.split())
            
            if self.valid_text(filtered_text):
                print(f"Reading: {filtered_text}")
                self.speech_id += 1
                asyncio.run_coroutine_threadsafe(
                    self._speak(filtered_text, self.speech_id),
                    self.tts_loop
                )
            else:
                self.close()

    def valid_text(self, text: str) -> bool:
        if len(text) < 2: return False
        blocked = ["traceback", "keyboardinterrupt"]
        if any(b in text.lower() for b in blocked): return False
        return True

    async def _speak(self, text, sid):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name

        try:
            await edge_tts.Communicate(text=text, voice="en-US-GuyNeural", rate="+0%").save(path)
            
            if sid != self.speech_id:
                os.remove(path)
                return

            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"Audio error: {e}")
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
            
            # Since we set QuitOnLastWindowClosed to False, we must manually kill the process
            os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = OCROverlay()
    overlay.show()
    sys.exit(app.exec_())
