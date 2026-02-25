import sys
import ctypes
from ctypes import c_float, c_int
import threading
import time

from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QIcon

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# Windows API setup for Magnification
mag = ctypes.windll.Magnification
user32 = ctypes.windll.user32

class FullWindowMagnifier(QWidget):
    """
    A full screen magnifier that uses the native Windows Magnification API.
    It provides 60FPS fluid zooming on the whole desktop natively.
    """
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scale_factor = 1.0
        self.zoom_increment = 0.5
        self.running = True

        # Initialize the native Windows magnifier engine
        if not mag.MagInitialize():
            print("Failed to initialize Magnification API")
            sys.exit(1)

        mag.MagSetFullscreenTransform.argtypes = [c_float, c_int, c_int]

        # Get total screen dimensions from Windows API
        self.screen_w = user32.GetSystemMetrics(0)
        self.screen_h = user32.GetSystemMetrics(1)

        # Make the PyQt window invisible but able to intercept global hotkeys if focused
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)

        # Timer loops to update the viewport based on mouse position
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        # Update every 16ms for ~60 fps
        self.timer.start(16)

        self.create_context_menu()
        self.tray_icon = QSystemTrayIcon(self)
        
        # Load the tray icon
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Listen for std input commands in the background
        threading.Thread(target=self.listen_commands, daemon=True).start()

    def create_context_menu(self):
        """Builds the system tray menu actions."""
        self.tray_menu = QMenu(self)
        self.zoom_in_action = QAction("Zoom In (Ctrl+Up / Ctrl++)", self)
        self.zoom_out_action = QAction("Zoom Out (Ctrl+Down / Ctrl+-)", self)
        self.reset_action = QAction("Reset View (Esc)", self)
        self.exit_action = QAction("Exit", self)

        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.reset_action.triggered.connect(self.reset_zoom)
        self.exit_action.triggered.connect(self.emit_exit)

        self.tray_menu.addAction(self.zoom_in_action)
        self.tray_menu.addAction(self.zoom_out_action)
        self.tray_menu.addAction(self.reset_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)

    def listen_commands(self):
        """Listens for standard input commands from external processes."""
        while self.running:
            try:
                command = sys.stdin.readline().strip()
                if command == "zoom_in":
                    self.zoom_in()
                elif command == "zoom_out":
                    self.zoom_out()
                elif command == "exit":
                    self.emit_exit()
                elif command == "reset":
                    self.reset_zoom()
            except Exception:
                break

    def get_mouse_pos(self):
        """Retrieve actual mouse coordinates quickly via ctypes."""
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def update_magnifier(self):
        """Updates the system-wide magnification viewport."""
        if self.scale_factor <= 1.0:
            # When zoom is default, ensure zero offset to eliminate visual glitches
            mag.MagSetFullscreenTransform(1.0, 0, 0)
            return

        mx, my = self.get_mouse_pos()

        # Determine how large the screen appears inside the scaled viewport
        view_w = self.screen_w / self.scale_factor
        view_h = self.screen_h / self.scale_factor

        # Map current mouse coordinates into a panning offset
        offset_x = 0
        if self.screen_w > view_w:
            offset_x = int((mx / self.screen_w) * (self.screen_w - view_w))

        offset_y = 0
        if self.screen_h > view_h:
            offset_y = int((my / self.screen_h) * (self.screen_h - view_h))

        # Apply the Windows OS hardware transform
        mag.MagSetFullscreenTransform(self.scale_factor, offset_x, offset_y)

    def zoom_in(self):
        """Increase the scale factor, cap at 5x."""
        self.scale_factor = min(self.scale_factor + self.zoom_increment, 5.0)

    def zoom_out(self):
        """Decrease the scale factor, lowest is 1.0x (normal screen)."""
        self.scale_factor = max(1.0, self.scale_factor - self.zoom_increment)

    def reset_zoom(self):
        """Restores the screen back to normal immediately."""
        self.scale_factor = 1.0
        self.update_magnifier()

    def keyPressEvent(self, event):
        """Handle PyQt window key events if it has focus."""
        if event.modifiers() == Qt.ControlModifier:
            # Keyboard shortcuts for zooming (Ctrl + Up, Ctrl + Plus)
            if event.key() in (Qt.Key_Up, Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()
            # Keyboard shortcuts for zooming out (Ctrl + Down, Ctrl + Minus)
            elif event.key() in (Qt.Key_Down, Qt.Key_Minus):
                self.zoom_out()
        elif event.key() == Qt.Key_Escape:
            self.reset_zoom()

    def uninitialize_mag(self):
        """Properly clean up the Magnification API context to stop zoom."""
        mag.MagSetFullscreenTransform(1.0, 0, 0)
        mag.MagUninitialize()

    def emit_exit(self):
        """Safely exit application and notify."""
        self.running = False
        self.uninitialize_mag()
        self.exit_signal.emit()
        self.close()

    def closeEvent(self, event):
        """Ensures magnification context closes neatly when PyQt exits."""
        self.uninitialize_mag()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    magnifier = FullWindowMagnifier()
    magnifier.show()
    magnifier.exit_signal.connect(app.quit)
    sys.exit(app.exec_())
