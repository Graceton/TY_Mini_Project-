import sys
import subprocess
import runpy

if len(sys.argv) > 1 and sys.argv[1] == "--run-module":
    module_name = sys.argv[2]
    # Remove the argument from sys.argv so the target script doesn't see it
    sys.argv = [sys.argv[0]] + sys.argv[3:]
    runpy.run_module(module_name, run_name="__main__")
    sys.exit(0)

# Force PyInstaller to bundle auxiliary modules
if getattr(sys, 'frozen', False):
    import magnifier.upper_window_magnifier
    import magnifier.full_window_magnifier
    import magnifier.hover_magnifier
    import reader.select_reader
    import reader.hover_reader
    import reader.full_reader
    import reader.ocr_reader
    import voice_assistant.ui_assistant

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QEvent, QPoint
from settings.settings import SettingsManager, SettingsWindow


class AccessibilityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.magnifier_process = None
        self.reader_process = None
        self.voice_process = None  # now handled as separate process
        self.settings_manager = SettingsManager()
        self.settings_window = None
        self.initUI()

    def createButton(self, emoji, tooltip, color, size=60):
        btn = QPushButton(emoji)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("Arial", 22, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                border: 2px solid black;
            }}
        """)
        btn.setFixedHeight(size)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.installEventFilter(self)
        return btn

    def initUI(self):
        self.setWindowTitle("OPTIVOX")
        self.setGeometry(200, 200, 400, 50)
        self.layout = QVBoxLayout()

        self.hover_label = QLabel(self)
        self.hover_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.hover_label.setFont(QFont("Arial", 10))
        self.hover_label.setAlignment(Qt.AlignCenter)
        self.hover_label.setVisible(False)

        # Main buttons
        self.zoom_btn = self.createButton("🔍", "Zoom Options", "#3498db")
        self.reader_btn = self.createButton("🔊", "Reader Options (Tab+R)", "#2ecc71")
        self.voice_btn = self.createButton("🎙️", "Voice Assistant", "#e74c3c")
        self.settings_btn = self.createButton("⚙️", "Settings", "#7c37cd", 50)
        self.exit_btn = self.createButton("❌", "Exit / Minimize", "#2c3e50", 50)

        # Sub-menus
        self.zoom_options = self.createZoomOptions()
        self.reader_options = self.createReaderOptions()
        self.voice_options = self.createVoiceOptions()
        self.exit_options = self.createExitOptions()

        # Connect buttons
        self.zoom_btn.clicked.connect(self.expandZoomButtons)
        self.reader_btn.clicked.connect(lambda: self.toggleMenu(self.reader_options))
        self.voice_btn.clicked.connect(lambda: self.toggleMenu(self.voice_options))
        self.settings_btn.clicked.connect(self.open_settings)
        self.exit_btn.clicked.connect(lambda: self.toggleMenu(self.exit_options))

        # Layout
        self.layout.addWidget(self.zoom_btn)
        self.layout.addLayout(self.zoom_options)
        self.layout.addWidget(self.reader_btn)
        self.layout.addLayout(self.reader_options)
        self.layout.addWidget(self.voice_btn)
        self.layout.addLayout(self.voice_options)
        self.layout.addWidget(self.settings_btn)
        self.layout.addWidget(self.exit_btn)
        self.layout.addLayout(self.exit_options)

        self.setLayout(self.layout)

    # ==========================
    # Magnifier Handling
    # ==========================

    def expandZoomButtons(self):
        self.layout.removeWidget(self.zoom_btn)
        self.zoom_btn.setVisible(False)

        zoom_inline_layout = QHBoxLayout()
        plus_btn = self.createButton("+", "Zoom In", "#3498db", 50)
        reset_btn = self.createButton("🔄", "Reset Zoom", "#3498db", 50)
        minus_btn = self.createButton("-", "Zoom Out", "#3498db", 50)

        for btn in [plus_btn, reset_btn, minus_btn]:
            zoom_inline_layout.addWidget(btn)

        self.current_zoom_inline_layout = zoom_inline_layout
        self.layout.insertLayout(0, zoom_inline_layout)

        for i in range(self.zoom_options.count()):
            self.zoom_options.itemAt(i).widget().setVisible(True)

        reset_btn.clicked.connect(self.restoreZoomButton)
        plus_btn.clicked.connect(lambda: self.send_zoom_command("zoom_in"))
        minus_btn.clicked.connect(lambda: self.send_zoom_command("zoom_out"))

        upper_btn = self.zoom_options.itemAt(0).widget()
        full_btn = self.zoom_options.itemAt(1).widget()
        hover_btn = self.zoom_options.itemAt(2).widget()

        upper_btn.clicked.connect(lambda: self.launch_magnifier("magnifier/upper_window_magnifier.py"))
        full_btn.clicked.connect(lambda: self.launch_magnifier("magnifier/full_window_magnifier.py"))
        hover_btn.clicked.connect(lambda: self.launch_magnifier("magnifier/hover_magnifier.py"))

    def restoreZoomButton(self):
        if self.magnifier_process and self.magnifier_process.poll() is None:
            try:
                if self.magnifier_process.stdin:
                    self.magnifier_process.stdin.write("exit\n")
                    self.magnifier_process.stdin.flush()
                self.magnifier_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.magnifier_process.terminate()
            except Exception:
                pass
            self.magnifier_process = None

        if hasattr(self, "current_zoom_inline_layout"):
            for i in range(self.current_zoom_inline_layout.count()):
                w = self.current_zoom_inline_layout.itemAt(i).widget()
                if w:
                    w.setVisible(False)

        self.zoom_btn.setVisible(True)
        self.layout.insertWidget(0, self.zoom_btn)

        for i in range(self.zoom_options.count()):
            self.zoom_options.itemAt(i).widget().setVisible(False)

    def launch_magnifier(self, script_path):
        if self.magnifier_process and self.magnifier_process.poll() is None:
            try:
                if self.magnifier_process.stdin:
                    self.magnifier_process.stdin.write("exit\n")
                    self.magnifier_process.stdin.flush()
                self.magnifier_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.magnifier_process.terminate()
            except Exception:
                pass

        if getattr(sys, 'frozen', False):
            module_name = script_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            cmd = [sys.executable, "--run-module", module_name]
        else:
            cmd = [sys.executable, script_path]

        self.magnifier_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            text=True
        )

    def send_zoom_command(self, command):
        if self.magnifier_process and self.magnifier_process.poll() is None:
            try:
                self.magnifier_process.stdin.write(command + "\n")
                self.magnifier_process.stdin.flush()
            except Exception as e:
                print(f"Error sending zoom command: {e}")

    # ==========================
    # Reader Handling
    # ==========================

    def launch_reader(self, script_path):
        if self.reader_process and self.reader_process.poll() is None:
            self.reader_process.terminate()
            
        if getattr(sys, 'frozen', False):
            module_name = script_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            cmd = [sys.executable, "--run-module", module_name]
        else:
            cmd = [sys.executable, script_path]
            
        self.reader_process = subprocess.Popen(cmd)
        self.showMinimized()

    # ==========================
    # Voice Assistant Handling
    # ==========================

    def start_voice_assistant(self):
        if self.voice_process is None or self.voice_process.poll() is not None:
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--run-module", "voice_assistant.ui_assistant"]
            else:
                cmd = [sys.executable, "voice_assistant/ui_assistant.py"]
            self.voice_process = subprocess.Popen(cmd)

    def stop_voice_assistant(self):
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()
            self.voice_process = None

    # ==========================
    # UI Helpers
    # ==========================

    def toggleMenu(self, menu_layout):
        if menu_layout.count() > 0:
            is_visible = menu_layout.itemAt(0).widget().isVisible()
            for i in range(menu_layout.count()):
                widget = menu_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(not is_visible)
            self.hover_label.setVisible(False)

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Enter:
                self.hover_label.setText(obj.toolTip())
                self.hover_label.adjustSize()
                button_pos = obj.mapToGlobal(QPoint(0, 0))
                label_x = button_pos.x() + (obj.width() - self.hover_label.width()) // 2
                label_y = button_pos.y() - self.hover_label.height() - 5
                self.hover_label.move(self.mapFromGlobal(QPoint(label_x, label_y)))
                self.hover_label.setVisible(True)
                self.hover_label.raise_()
            elif event.type() == QEvent.Leave:
                self.hover_label.setVisible(False)
        return super().eventFilter(obj, event)

    def createZoomOptions(self):
        layout = QHBoxLayout()
        upper = self.createButton("🪟", " Magnifier Window", "#3498db", 50)
        full = self.createButton("⛶", "Full Window Magnifier", "#3498db", 50)
        hover = self.createButton("🖱️", "Hover Magnifier", "#3498db", 50)
        for btn in [upper, full, hover]:
            btn.setVisible(False)
            layout.addWidget(btn)
        return layout

    def createReaderOptions(self):
        layout = QHBoxLayout()
        hover = self.createButton("🖱️", "Hover to Read", "#27ae60", 50)
        para = self.createButton("�", "Paragraph Selection", "#27ae60", 50)
        line = self.createButton("📏", "Line-wise Reader", "#27ae60", 50)
        ocr = self.createButton("📷", "OCR Overlay", "#27ae60", 50)
        
        hover.clicked.connect(lambda: self.launch_reader("reader/hover_reader.py"))
        para.clicked.connect(lambda: self.launch_reader("reader/select_reader.py"))
        line.clicked.connect(lambda: self.launch_reader("reader/full_reader.py"))
        ocr.clicked.connect(lambda: self.launch_reader("reader/ocr_reader.py"))
        
        for btn in [hover, para, line, ocr]:
            btn.setVisible(False)
            layout.addWidget(btn)
        return layout

    def createVoiceOptions(self):
        layout = QHBoxLayout()
        start = self.createButton("🎙️", "Start Voice Assistant", "#c0392b", 50)
        stop = self.createButton("🔇", "Stop Voice Assistant", "#c0392b", 50)
        start.clicked.connect(self.start_voice_assistant)
        stop.clicked.connect(self.stop_voice_assistant)
        for btn in [start, stop]:
            btn.setVisible(False)
            layout.addWidget(btn)
        return layout

    def open_settings(self):
        if not self.settings_window or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow(self.settings_manager)
            self.settings_window.show()

    def createExitOptions(self):
        layout = QHBoxLayout()
        minimize = self.createButton("➖", "Minimize App", "#34495e", 50)
        quit_app = self.createButton("❌", "Quit App", "#34495e", 50)
        minimize.clicked.connect(self.showMinimized)
        quit_app.clicked.connect(self.close)
        for btn in [minimize, quit_app]:
            btn.setVisible(False)
            layout.addWidget(btn)
        return layout

    def closeEvent(self, event):
        if self.magnifier_process and self.magnifier_process.poll() is None:
            try:
                if self.magnifier_process.stdin:
                    self.magnifier_process.stdin.write("exit\n")
                    self.magnifier_process.stdin.flush()
                self.magnifier_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.magnifier_process.terminate()
            except Exception:
                pass
        if self.reader_process and self.reader_process.poll() is None:
            self.reader_process.terminate()
        if self.voice_process and self.voice_process.poll() is None:
            self.voice_process.terminate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccessibilityApp()
    window.show()
    sys.exit(app.exec_())