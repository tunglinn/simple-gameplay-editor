from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6. QtCore import Qt

class PreviewPopup(QDialog):
    def __init__(self, composite_clip, t=1.0):
        super().__init__()
        self.setWindowTitle("Preview")
        self.resize(800,450)

        frame = composite_clip.get_frame(t)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        label = QLabel()
        label.setFixedSize(800,450)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


