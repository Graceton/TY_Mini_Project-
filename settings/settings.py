# settings/settings.py

import json
import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider,
    QPushButton, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt

# Use absolute paths to avoid PermissionError or CWD issues
SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "user_settings.json")


# -------------------------
# SETTINGS MANAGER
# -------------------------
class SettingsManager:

    DEFAULTS = {
        "speech_rate": 160,
        "speech_volume": 1.0,
        "voice_name": "default",
        "default_zoom": 2.0,
        "hover_width": 300,
        "hover_height": 200,
        "high_contrast": False,
        "large_ui": False,
        "invert_magnifier": False,
        "ocr_language": "eng"
    }

    def __init__(self):
        self.settings = {}
        self._last_mtime = 0
        self.load()

    def load(self):
        if not os.path.exists(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR)

        if not os.path.exists(SETTINGS_FILE):
            self.settings = self.DEFAULTS.copy()
            self.save()
        else:
            # Retry logic to handle race conditions where the file is momentarily empty/locked
            for attempt in range(5):
                try:
                    with open(SETTINGS_FILE, "r") as f:
                        content = f.read()
                        if not content:
                            raise ValueError("Empty settings file")
                        self.settings = json.loads(content)
                    self._last_mtime = os.path.getmtime(SETTINGS_FILE)
                    return
                except (json.JSONDecodeError, ValueError, IOError) as e:
                    if attempt == 4:
                        print(f"Failed to load settings after 5 attempts: {e}")
                        self.settings = self.DEFAULTS.copy()
                    else:
                        time.sleep(0.05) # Wait 50ms before retrying

    def save(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        self._last_mtime = os.path.getmtime(SETTINGS_FILE)

    def get(self, key):
        # Auto-refresh if file changed on disk
        if os.path.exists(SETTINGS_FILE):
            current_mtime = os.path.getmtime(SETTINGS_FILE)
            if current_mtime > self._last_mtime:
                self.load()
        return self.settings.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()


# -------------------------
# SETTINGS WINDOW GUI
# -------------------------
class SettingsWindow(QWidget):

    def __init__(self, manager: SettingsManager):
        super().__init__()
        self.manager = manager

        self.setWindowTitle("Optivox Settings")
        self.setGeometry(300, 300, 400, 500)

        layout = QVBoxLayout()

        # ---- SPEECH RATE ----
        layout.addWidget(QLabel("Speech Speed"))
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(80, 300)
        self.rate_slider.setValue(self.manager.get("speech_rate"))
        self.rate_slider.valueChanged.connect(
            lambda v: self.manager.set("speech_rate", v)
        )
        layout.addWidget(self.rate_slider)

        # ---- VOLUME ----
        layout.addWidget(QLabel("Speech Volume"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.manager.get("speech_volume") * 100))
        self.volume_slider.valueChanged.connect(
            lambda v: self.manager.set("speech_volume", v / 100)
        )
        layout.addWidget(self.volume_slider)

        # ---- DEFAULT ZOOM ----
        layout.addWidget(QLabel("Default Zoom Level"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(1, 10)
        self.zoom_slider.setValue(int(self.manager.get("default_zoom")))
        self.zoom_slider.valueChanged.connect(
            lambda v: self.manager.set("default_zoom", float(v))
        )
        layout.addWidget(self.zoom_slider)

        # ---- HIGH CONTRAST ----
        self.high_contrast = QCheckBox("Enable High Contrast Mode")
        self.high_contrast.setChecked(self.manager.get("high_contrast"))
        self.high_contrast.stateChanged.connect(
            lambda v: self.manager.set("high_contrast", bool(v))
        )
        layout.addWidget(self.high_contrast)

        # ---- LARGE UI ----
        self.large_ui = QCheckBox("Enlarge Interface")
        self.large_ui.setChecked(self.manager.get("large_ui"))
        self.large_ui.stateChanged.connect(
            lambda v: self.manager.set("large_ui", bool(v))
        )
        layout.addWidget(self.large_ui)

        # ---- INVERT MAGNIFIER ----
        self.invert = QCheckBox("Invert Magnifier Colors")
        self.invert.setChecked(self.manager.get("invert_magnifier"))
        self.invert.stateChanged.connect(
            lambda v: self.manager.set("invert_magnifier", bool(v))
        )
        layout.addWidget(self.invert)

        # ---- OCR LANGUAGE ----
        layout.addWidget(QLabel("OCR Language"))
        self.ocr_lang = QComboBox()
        self.ocr_lang.addItems(["eng", "hin", "fra", "spa"])
        self.ocr_lang.setCurrentText(self.manager.get("ocr_language"))
        self.ocr_lang.currentTextChanged.connect(
            lambda v: self.manager.set("ocr_language", v)
        )
        layout.addWidget(self.ocr_lang)

        # ---- CLOSE BUTTON ----
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)