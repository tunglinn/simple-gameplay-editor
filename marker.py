from PyQt6.QtWidgets import QListWidgetItem
from enum import Enum

class Marker(QListWidgetItem):
    class MarkerType(str, Enum):
        SERVE = "Serve"
        NO_PT = "No point"
        HOME_PT = "Home point"
        AWAY_PT = "Away point"
    def __init__(self, name:str, timestamp: float):
        super().__init__(f"{name.value} at {round(timestamp/1000, 2)}")
        self.marker_type = name
        self.timestamp = timestamp
