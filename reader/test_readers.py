import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QMouseEvent, Qt
from reader.ocr_reader import OCROverlay
import sys

@pytest.fixture(scope="module")
def app():
    app_instance = QApplication(sys.argv)
    yield app_instance
    app_instance.quit()

@pytest.fixture
def ocr_overlay(app):
    overlay = OCROverlay()
    yield overlay
    overlay.close()

def test_ocr_rectangle_drawing(ocr_overlay):
    """Test that mouse drag events properly define a rectangle."""
    # Simulate Mouse Press at (100, 100)
    press_event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPoint(100, 100),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier
    )
    ocr_overlay.mousePressEvent(press_event)
    
    assert ocr_overlay.is_drawing is True
    assert ocr_overlay.begin == QPoint(100, 100)
    assert ocr_overlay.end == QPoint(100, 100)

    # Simulate Mouse Move to (300, 250)
    move_event = QMouseEvent(
        QMouseEvent.MouseMove,
        QPoint(300, 250),
        Qt.NoButton,
        Qt.NoButton,
        Qt.NoModifier
    )
    ocr_overlay.mouseMoveEvent(move_event)
    assert ocr_overlay.end == QPoint(300, 250)

def test_valid_text_logic(ocr_overlay):
    """Test the anti-gibberish and python block filters."""
    assert ocr_overlay.valid_text("Hello world this is a test") is True
    assert ocr_overlay.valid_text("a") is False  # Too short
    assert ocr_overlay.valid_text("Traceback most recent call:") is False # Python trace
    assert ocr_overlay.valid_text("if (a == 1) { return 0; }") is False # Code
