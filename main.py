import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QListWidget, QMenuBar, QFileDialog, QMessageBox, QLabel, QLCDNumber
from PyQt6.QtCore import Qt
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import vlc
import timeline
import json
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Embedded Player")
        self.setGeometry(100, 100, 800, 600)

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")

        # Platform-specific handle embedding
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(int(self.video_frame.winId()))

        self.timeline = timeline.TimelineWidget()

        # Create and add menu bar manually
        menubar = QMenuBar()
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Media", self)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

        load_action = QAction("Load Markers", self)
        load_action.triggered.connect(self.load_markers)
        file_menu.addAction(load_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        self.markers = {}
        self.marker_list = QListWidget()

        # create back button
        self.back_btn = QPushButton("<<")
        self.back_btn.clicked.connect(self.back)

        # create play button
        self.play_btn = QPushButton("Play/Pause")
        self.play_btn.clicked.connect(self.toggle_play)

        # create marker buttons
        self.marker_buttons = []
        for marker in timeline.MARKER_TYPES.keys():
            button = QPushButton(marker)
            button.clicked.connect(lambda checked=False, n=marker: self.add_marker(n))
            self.marker_buttons.append(button)

        # create export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export)

        # create score tracker
        self.home_score = QLabel("0")
        self.home_score.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.away_score = QLabel("0")

         # --- Layout setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setMenuBar(menubar)

        score_label_layout = QHBoxLayout()
        home = QLabel("Home")
        home.setAlignment(Qt.AlignmentFlag.AlignRight)
        score_label_layout.addWidget(home)
        score_label_layout.addWidget(QLabel("Away"))

        score_layout = QHBoxLayout()
        score_layout.addWidget(self.home_score)
        score_layout.addWidget(self.away_score)

        main_layout.addLayout(score_label_layout)
        main_layout.addLayout(score_layout)

        # top: video display
        main_layout.addWidget(self.video_frame, stretch=3)

        # middle: play button + add marker
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.back_btn)
        button_layout.addWidget(self.play_btn)
        for button in self.marker_buttons:
            button_layout.addWidget(button)
        main_layout.addLayout(button_layout)

        # below: slider
        main_layout.addWidget(self.timeline)

        # bottom: marker list
        main_layout.addWidget(self.marker_list, stretch=1)

        main_layout.addWidget(self.export_btn)
        
        # Timer to update slider
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # every 100 ms
        self.timer.timeout.connect(self.update_timeline)
        self.timer.start()
        QTimer.singleShot(100, self.open_file_dialog)
    
    def open_file_dialog(self):
        # Open file picker dialog
        self.video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",  # initial directory
            "All Files (*);;Text Files (*.txt);;Video Files (*.mp4 *.avi)"
        )
        if self.video_path:
            print("Selected file:", self.video_path)
        
        media = self.instance.media_new(self.video_path)
        self.player.set_media(media)
        self.set_timeline_and_fps()
        self.toggle_play()
    

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()
    def load_markers(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            self.markers = {int(k): v for k, v in loaded.items()}
            print(f"markers: {self.markers}")
        print(f"Loaded {len(self.markers)} items from {file_path}")
        self.timeline.set_markers(self.markers)
        self.marker_list.clear()
        for t, name in self.markers.items():
            self.marker_list.addItem(f"{name} at {t/1000:.2f}s")
    def save(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.markers, f, indent=2)
        print(f"Saved {len(self.markers)} items to {file_path}")
        
    def back(self):
        current_time = self.player.get_time()  # milliseconds
        seek_time = max(0, current_time - 5000)
        self.player.set_time(seek_time)
    
    def export(self):
        clip_ranges = []
        current_start = None
        for t, name in sorted(self.markers.items()):
            t = round(t/1000, 1)
            print(f"timestamp: {t} name: {name}")
            if name == "Serve":
                current_start = t
            else:
                if current_start: 
                    clip_ranges.append((current_start, t, name))
                    current_start = None
                else:
                    print(f"{name} at timestamp {t} doesn't have start serve.")
                    return

        
        video = VideoFileClip(self.video_path)
        print(f'subclips: {clip_ranges}')
        subclips = []
        home = 0
        away = 0
        for start, end, name in clip_ranges:
            clip = video.subclipped(start, end)
            if "Home" in name:
                home += 1
            elif "Away" in name:
                away += 1
            # Create text overlay
            score_text = TextClip(text=f"Home: {home}  Away: {away}", 
                                  font_size=40, color='white', 
                                  duration=clip.duration,
                                  margin=(10,10), bg_color="black")
            score_text = score_text.with_position(("center", "top"))
            # Combine the video and text
            annotated_clip = CompositeVideoClip([clip, score_text])
            subclips.append(annotated_clip)
        final = concatenate_videoclips(subclips)
        final.write_videofile("output.mp4")
        video.close()
    
    def set_timeline_and_fps(self):
        
        self.timeline.set_duration(1)  # default to avoid div by zero
        self.duration_timer = QTimer(self)
        self.duration_timer.setInterval(100)  # check every 100ms
        self.duration_timer.timeout.connect(self.check_duration)
        self.duration_timer.start()

    def check_duration(self):
        dur = self.player.get_length()
        if dur > 0:
            self.timeline.set_duration(dur)
            self.fps = self.player.get_fps()
            self.duration_timer.stop()  # stop polling

    def init_duration(self):
        self.timeline.duration = self.player.get_length()
    def update_timeline(self):
        pos = self.player.get_time()         # Current time in ms
        self.timeline.set_position(pos)
        self.update_score()
    def update_score(self):
        pos = self.player.get_time()
        home = 0
        away = 0
        for t, name in self.markers.items():
            if t < pos:
                if name == "Home point":
                    home += 1
                elif name == "Away point":
                    away += 1
        self.home_score.setText(str(home))
        self.away_score.setText(str(away))

    def set_position(self, value):
        """Jump to a position in the video when slider is moved."""
        try:
            self.player.set_position(value / 1000.0)
        except Exception as e:
            print("Error setting position:", e)
    def add_marker(self, name):
        t = self.player.get_time()
        self.markers[t] = name
        self.marker_list.addItem(f"{name} at {t/1000:.2f}s")

        self.timeline.set_markers(self.markers)
    def closeEvent(self, event):
        # Show a confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()  # Close the window
        else:
            event.ignore()  # Ignore the close request


app = QApplication(sys.argv)
window = VideoApp()
window.show()
sys.exit(app.exec())
