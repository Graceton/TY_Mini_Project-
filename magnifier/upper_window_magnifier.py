import sys
import numpy as np
import pyautogui
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QImage, QIcon
import cv2
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings.settings import SettingsManager

class UpperWindowMagnifier(QWidget):
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.scale_factor = self.settings.get("default_zoom")
        self.zoom_increment = self.settings.get("zoom_step")
        
        self.dragging = False
        self.offset = QPoint()
        self.running = True

        # Screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width, screen_height = screen_geometry.width(), screen_geometry.height()

        # Position: top-right, size: 1/4th of screen
        self.width_size = screen_width // 2
        self.height_size = screen_height // 2
        self.setGeometry(screen_width - self.width_size, 0, self.width_size, self.height_size)

        # Always on top, frameless
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Label to show magnified region
        self.label = QLabel(self)
        self.label.resize(self.width_size, self.height_size)

        # Timer to update magnifier
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(30)

        # Tray icon
        self.create_tray_icon()

        # Listen for commands from standard input
        threading.Thread(target=self.listen_commands, daemon=True).start()

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
                    self.exit_magnifier()
            except Exception:
                break

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        self.tray_menu = QMenu()

        zoom_in_action = QAction("Zoom In", self)
        zoom_out_action = QAction("Zoom Out", self)
        exit_action = QAction("Exit", self)

        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_out_action.triggered.connect(self.zoom_out)
        exit_action.triggered.connect(self.exit_magnifier)

        self.tray_menu.addAction(zoom_in_action)
        self.tray_menu.addAction(zoom_out_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def update_magnifier(self):
        mx, my = pyautogui.position()
        screen = pyautogui.screenshot()
        frame = np.array(screen)

        # Calculate region around mouse with correct aspect ratio
        half_w = int(self.width_size / (2 * self.scale_factor))
        half_h = int(self.height_size / (2 * self.scale_factor))
        x1, y1 = max(0, mx - half_w), max(0, my - half_h)
        x2, y2 = min(frame.shape[1], mx + half_w), min(frame.shape[0], my + half_h)

        magnified = frame[y1:y2, x1:x2]

        # Resize to overlay window size
        magnified = cv2.resize(magnified, (self.width_size, self.height_size))

        # Apply inversion if toggled
        if self.settings.get("invert_magnifier"):
            magnified = cv2.bitwise_not(magnified)
            
        h, w, _ = magnified.shape
        image = QImage(magnified.data, w, h, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)

    def zoom_in(self):
        self.scale_factor = min(self.scale_factor + self.zoom_increment, 10.0)

    def zoom_out(self):
        self.scale_factor = max(1.0, self.scale_factor - self.zoom_increment)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Up:
                self.zoom_in()
            elif event.key() == Qt.Key_Down:
                self.zoom_out()
        elif event.key() == Qt.Key_Escape:
            self.exit_magnifier()

    # ----------------- Draggable Overlay -----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= 30:  # Top draggable bar
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def exit_magnifier(self):
        self.running = False
        self.close()
        self.exit_signal.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    magnifier = UpperWindowMagnifier()
    magnifier.show()
    magnifier.exit_signal.connect(app.quit)
    sys.exit(app.exec_())
