import cv2
import sys
import numpy as np
import pyautogui
import mss
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
import threading
import os
import keyboard
import ctypes

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings.settings import SettingsManager


class ScreenMagnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.settings = SettingsManager()
        self.scale_factor = self.settings.get("default_zoom")
        self.zoom_increment = 0.5 # Fixed step
        self.running = True

        self.capture = mss.mss()

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.92)
        
        # Exclude this window from screen captures to prevent the "infinity mirror" effect
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011) # WDA_EXCLUDEFROMCAPTURE
        except Exception as e:
            print("Could not exclude window from capture:", e)

        self.label = QLabel(self)
        self.label.setFixedSize(300, 200)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(16)  # ~60 FPS smoother

        self.create_context_menu()

        self.tray_icon = QSystemTrayIcon(self)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "Images", "Dark themed Logo.jpeg")
        self.tray_icon.setIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon())
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        threading.Thread(target=self.listen_commands, daemon=True).start()
        
        # Global Hotkeys (Suppressed to prevent passing to underlying apps like Chrome)
        keyboard.add_hotkey('ctrl+plus', self.zoom_in, suppress=True)
        keyboard.add_hotkey('ctrl+=', self.zoom_in, suppress=True)
        keyboard.add_hotkey('ctrl+add', self.zoom_in, suppress=True)
        keyboard.add_hotkey('ctrl+-', self.zoom_out, suppress=True)
        keyboard.add_hotkey('ctrl+subtract', self.zoom_out, suppress=True)

    def create_context_menu(self):
        self.tray_menu = QMenu(self)

        zoom_in = QAction("Zoom In (Ctrl+Up / Ctrl++)", self)
        zoom_out = QAction("Zoom Out (Ctrl+Down / Ctrl+-)", self)
        hide = QAction("Hide (Esc)", self)
        unhide = QAction("Unhide", self)
        exit_app = QAction("Exit", self)

        zoom_in.triggered.connect(self.zoom_in)
        zoom_out.triggered.connect(self.zoom_out)
        hide.triggered.connect(self.hide)
        unhide.triggered.connect(self.show)
        exit_app.triggered.connect(self.emit_exit)

        self.tray_menu.addAction(zoom_in)
        self.tray_menu.addAction(zoom_out)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(hide)
        self.tray_menu.addAction(unhide)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_app)

    def listen_commands(self):
        while self.running:
            try:
                command = sys.stdin.readline().strip()

                if command == "zoom_in":
                    self.zoom_in()

                elif command == "zoom_out":
                    self.zoom_out()

                elif command == "exit":
                    self.running = False
                    self.close()

            except Exception:
                break

    def update_magnifier(self):

        mx, my = pyautogui.position()

        target_w = 300
        target_h = 200

        capture_w = int(target_w / self.scale_factor)
        capture_h = int(target_h / self.scale_factor)

        # Capture region centered on cursor
        left = mx - capture_w // 2
        top = my - capture_h // 2

        screen_w, screen_h = pyautogui.size()

        left = max(0, min(left, screen_w - capture_w))
        top = max(0, min(top, screen_h - capture_h))

        monitor = {
            "left": left,
            "top": top,
            "width": capture_w,
            "height": capture_h
        }

        frame = np.array(self.capture.grab(monitor))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        if self.settings.get("invert_magnifier"):
            frame = cv2.bitwise_not(frame)

        magnified = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        cv2.rectangle(magnified, (0, 0), (target_w - 1, target_h - 1), (0, 255, 0), 2)
        magnified = cv2.cvtColor(magnified, cv2.COLOR_BGR2RGB)

        height, width, channel = magnified.shape
        bytesPerLine = 3 * width

        qImg = QImage(magnified.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qImg))

        # Window position centered on cursor
        self.move(mx - target_w // 2, my - target_h // 2)

    def zoom_in(self):
        self.scale_factor = min(self.scale_factor + self.zoom_increment, 10)
        self.update()

    def zoom_out(self):
        self.scale_factor = max(2.0, self.scale_factor - self.zoom_increment)
        self.update()

    def keyPressEvent(self, event):

        if event.modifiers() == Qt.ControlModifier:

            if event.key() in (Qt.Key_Up, Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()

            elif event.key() in (Qt.Key_Down, Qt.Key_Minus):
                self.zoom_out()

        elif event.key() == Qt.Key_Escape:
            self.hide()

    def emit_exit(self):
        self.running = False
        self.exit_signal.emit()
        self.close()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    magnifier = ScreenMagnifier()
    magnifier.show()

    magnifier.exit_signal.connect(app.quit)

    sys.exit(app.exec_())