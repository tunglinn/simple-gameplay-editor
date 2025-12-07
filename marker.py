from PyQt6.QtWidgets import QListWidgetItem
from enum import Enum

class Marker(QListWidgetItem):
    class MarkerType(str, Enum):
        SERVE = "Serve"
        NO_PT = "No point"
        HOME_PT = "Home point"
        AWAY_PT = "Away point"
    def __init__(self, name:str, timestamp: float):
        super().__init__(f"{round(timestamp/1000, 2)} - {name.value}")
        self.marker_type = name
        self.timestamp = int(timestamp)
    def __str__(self):
        return f"{round(self.timestamp/1000, 2)} - {self.marker_type.value}"
    def __lt__(self, other):
        # First compare timestamps
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp

        # If timestamps are equal, compare MarkerType values
        return self.marker_type.value < other.marker_type.value
