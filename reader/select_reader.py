import sys
import pyttsx3
import keyboard
import pyperclip
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class ReaderThread(QThread):
    speak_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.running = True
        self.last_text = ""
        self.is_reading = False

    def run(self):
        while self.running:
            # When user presses Ctrl+C, read the copied text
            try:
                if keyboard.is_pressed("ctrl+c"):
                    import time
                    time.sleep(0.2)  # Small delay to ensure clipboard is updated
                    text = pyperclip.paste()
                    if text and text != self.last_text:
                        self.last_text = text
                        self.is_reading = True
                        self.engine.say(text)
                        self.engine.runAndWait()
                        self.is_reading = False
            except Exception as e:
                print(f"Reader error: {e}")
            
            import time
            time.sleep(0.1)  # Prevent CPU overuse

    def stop(self):
        self.running = False
        if self.is_reading:
            self.engine.stop()

class SelectReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optivox - Select to Read")
        self.setGeometry(100, 100, 450, 120)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout()
        
        # Title label
        self.label = QLabel("📋 Select text & press Ctrl+C to read aloud", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 16px; padding: 10px;")
        layout.addWidget(self.label)

        # Button layout
        button_layout = QHBoxLayout()
        
        # Stop button
        self.stop_btn = QPushButton("🔇 Stop Reading", self)
        self.stop_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_reading)
        button_layout.addWidget(self.stop_btn)

        # Close button
        self.close_btn = QPushButton("❌ Close", self)
        self.close_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.thread = ReaderThread()
        self.thread.start()

    def stop_reading(self):
        """Stop current reading"""
        if self.thread.is_reading:
            self.thread.engine.stop()

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = SelectReader()
    reader.show()
    sys.exit(app.exec_())