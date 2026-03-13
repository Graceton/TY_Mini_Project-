import pytest
from magnifier.full_window_magnifier import FullWindowMagnifier
from PyQt5.QtWidgets import QApplication
import sys

# Ensure there's a Qt application context for the tests
@pytest.fixture(scope="module")
def app():
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def magnifier(app):
    """Fixture to create and clean up the magnifier instance."""
    mag = FullWindowMagnifier()
    yield mag
    mag.uninitialize_mag()

def test_initial_state(magnifier):
    """Ensure magnifier starts at a scale of 1.0."""
    assert magnifier.scale_factor == 1.0
    assert magnifier.running is True

def test_zoom_in(magnifier):
    """Test zoom incrementing."""
    initial_scale = magnifier.scale_factor
    magnifier.zoom_in()
    assert magnifier.scale_factor > initial_scale
    assert magnifier.scale_factor == 1.5

def test_zoom_out(magnifier):
    """Test zoom decrementing down to a minimum of 1.0."""
    magnifier.scale_factor = 2.0
    magnifier.zoom_out()
    assert magnifier.scale_factor == 1.5
    
    # Test capping at 1.0 limit
    magnifier.scale_factor = 1.0
    magnifier.zoom_out()
    assert magnifier.scale_factor == 1.0

def test_reset_zoom(magnifier):
    """Test resetting zoom back to 1.0 immediately."""
    magnifier.zoom_in()
    magnifier.zoom_in()
    assert magnifier.scale_factor == 2.0
    magnifier.reset_zoom()
    assert magnifier.scale_factor == 1.0
