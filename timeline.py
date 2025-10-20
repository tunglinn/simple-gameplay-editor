from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt

MARKER_TYPES = {
    "Serve": "yellow",
    "No point": "grey",
    "Home point": "green",
    "Away point": "red"
}
class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = 0      # Current playback position in ms
        self.duration = 1      # Video duration in ms
        self.markers = {}      # List of marker times in ms

        self.setMinimumHeight(30)  # Visible height for timeline

    def set_position(self, pos):
        self.position = pos
        self.update()

    def set_duration(self, dur):
        self.duration = max(dur, 1)
        self.update()

    def set_markers(self, markers):
        self.markers = markers
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))

        # Draw current position line
        x_pos = int((self.position / self.duration) * self.width())
        x_pos = min(max(x_pos, 0), self.width())

        painter.setPen(QColor(200, 200, 255))
        painter.drawLine(x_pos, 0, x_pos, h)

        # Draw markers
        for t, name in self.markers.items():
            painter.setBrush(QColor(MARKER_TYPES[name]))
            x = int((t / self.duration) * w)
            painter.drawRect(x-1, 0, 2, h)
    def mousePressEvent(self, event):
        x = event.position().x()
        pos_ratio = x / self.width()
        new_time = int(pos_ratio * self.duration)
        self.parent().player.set_time(new_time)