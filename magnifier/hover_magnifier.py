import cv2
import sys
import numpy as np
import pyautogui
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings.settings import SettingsManager

class ScreenMagnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.scale_factor = self.settings.get("default_zoom")
        self.zoom_increment = self.settings.get("zoom_step")
        self.running = True

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        self.label = QLabel(self)
        self.label.setFixedSize(300, 200)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30)

        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Start a thread to listen for zoom commands from stdin
        threading.Thread(target=self.listen_commands, daemon=True).start()

    def create_context_menu(self):
        self.tray_menu = QMenu(self)
        self.zoom_in_action = QAction("Zoom In (Ctrl+Up)", self)
        self.zoom_out_action = QAction("Zoom Out (Ctrl+Down)", self)
        self.hide_action = QAction("Hide (Esc)", self)
        self.unhide_action = QAction("Unhide", self)
        self.exit_action = QAction("Exit", self)

        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.hide_action.triggered.connect(self.hide)
        self.unhide_action.triggered.connect(self.show)
        self.exit_action.triggered.connect(self.emit_exit)

        self.tray_menu.addAction(self.zoom_in_action)
        self.tray_menu.addAction(self.zoom_out_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.hide_action)
        self.tray_menu.addAction(self.unhide_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)

    def listen_commands(self):
        """Listen to stdin commands to zoom dynamically"""
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
        screen = pyautogui.screenshot()
        frame = np.array(screen)

        target_w, target_h = 300, 200
        half_w = int(target_w / (2 * self.scale_factor))
        half_h = int(target_h / (2 * self.scale_factor))

        x1, y1 = max(0, mx - half_w), max(0, my - half_h)
        x2, y2 = min(frame.shape[1], mx + half_w), min(frame.shape[0], my + half_h)

        magnified_frame = frame[y1:y2, x1:x2]
        
        # Apply inversion if toggled
        if self.settings.get("invert_magnifier"):
            magnified_frame = cv2.bitwise_not(magnified_frame)

        if magnified_frame.shape[0] > 0 and magnified_frame.shape[1] > 0:
            magnified_frame = cv2.resize(magnified_frame, (target_w, target_h))

            height, width, channel = magnified_frame.shape
            bytesPerLine = 3 * width
            qImg = QImage(magnified_frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg)
            self.label.setPixmap(pixmap)
            
        # Offset sufficiently to avoid infinite mirror capture
        offset_x, offset_y = 160, 110
        if mx + offset_x + target_w > pyautogui.size().width:
            offset_x = -target_w - 20
        if my + offset_y + target_h > pyautogui.size().height:
            offset_y = -target_h - 20
        self.move(int(mx + offset_x), int(my + offset_y))

    def zoom_in(self):
        self.scale_factor = min(self.scale_factor + self.zoom_increment, 10.0)
        self.update()

    def zoom_out(self):
        self.scale_factor = max(2.5, self.scale_factor - self.zoom_increment)
        self.update()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Up:
                self.zoom_in()
            elif event.key() == Qt.Key_Down:
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
