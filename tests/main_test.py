import pytest
from unittest.mock import patch
from timeline import TimelineWidget
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from main import VideoApp

@pytest.fixture
def video_app(qtbot):
    window = VideoApp()          # initialize the app
    qtbot.addWidget(window)      # register with qtbot
    window.show()                # show the window
    qtbot.waitExposed(window)    # wait until fully visible

    yield window                 # provide the app to the test

    window.close()               # close after test finishes

@patch("PyQt6.QtWidgets.QMessageBox.question",
           return_value=QMessageBox.StandardButton.Yes)
def test_app_loads(video_app, qtbot):
    """Ensure the app window loads and closes cleanly."""
    assert video_app.isVisible()  # confirm it actually appeared
    # Wait for window to be exposed
    qtbot.waitExposed(video_app)
    assert video_app.isVisible()