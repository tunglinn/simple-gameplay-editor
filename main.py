import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QListWidget, QMenuBar, QFileDialog, QMessageBox, QLabel, QLCDNumber, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
import vlc
import timeline
import json
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip
from marker import Marker
from preview_popup import PreviewPopup

DEFAULT_IMPORT="test.mkv"
DEFAULT_SCOREBOARD="scoreboard_base.png"

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Embedded Player")
        self.setGeometry(100, 100, 800, 600)

        # TODO: create option to select scoreboard image
        self.scoreboard_path = DEFAULT_SCOREBOARD
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

        # Creat markers
        self.markers = {}
        self.marker_list = QListWidget()
        self.marker_list.itemClicked.connect(self.select_marker)

        # create back button
        self.back_btn = QPushButton("<<")
        self.back_btn.clicked.connect(self.back)

        # create play button
        self.play_btn = QPushButton("Play/Pause")
        self.play_btn.clicked.connect(self.toggle_play)

        # create marker buttons
        self.marker_buttons = []
        for marker in Marker.MarkerType:
            button = QPushButton(marker.value)
            button.clicked.connect(lambda checked=False, n=marker: self.add_marker(n))
            self.marker_buttons.append(button)
        
        # create delete marker button
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_markers)

        # create preview button
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.show_preview)

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
        self.home = QLineEdit("Home", alignment=Qt.AlignmentFlag.AlignRight)
        self.home.setFixedWidth(100)
        score_label_layout.addWidget(QLabel("(Home)", alignment=Qt.AlignmentFlag.AlignRight))
        score_label_layout.addWidget(self.home)
        self.away = QLineEdit("Away")
        self.away.setFixedWidth(100)
        score_label_layout.addWidget(self.away)
        score_label_layout.addWidget(QLabel("(Away)"))

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
        button_layout.addWidget(self.delete_btn)
        main_layout.addLayout(button_layout)

        # below: slider
        main_layout.addWidget(self.timeline)

        # bottom: marker list
        main_layout.addWidget(self.marker_list, stretch=1)

        main_layout.addWidget(self.preview_btn)
        main_layout.addWidget(self.export_btn)
        
        # Timer to update slider
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # every 100 ms
        self.timer.timeout.connect(self.update_timeline)
        self.timer.start()

        if DEFAULT_IMPORT:
            self.auto_load()
    
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
    
    def auto_load(self):
        self.video_path=DEFAULT_IMPORT
        media = self.instance.media_new(self.video_path)
        self.player.set_media(media)
        self.set_timeline_and_fps()
        self.toggle_play()

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()
    def marker_hook(self, obj):
        for k, v in obj.items():
            if isinstance(v, str) and v in Marker.MarkerType._value2member_map_:
                obj[k] = Marker.MarkerType(v)
        return obj
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
            loaded = json.load(f, object_hook=self.marker_hook)
            self.markers = {int(k): v for k, v in loaded.items()}
        print(f"Loaded {len(self.markers)} items from {file_path}")
        self.timeline.set_markers(self.markers)
        self.marker_list.clear()
        for t, name in self.markers.items():
            self.marker_list.addItem(Marker(name, t))
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

    def make_scoreboard_composite(self, video_clip, duration, position=("center", 20)):
        w, h = video_clip.size
        overlay = ImageClip(self.scoreboard_path).with_duration(duration).resized(height=h/8).with_position(position)
        final = CompositeVideoClip([video_clip, overlay])
        return final

    def export(self):
        clip_ranges = []
        current_start = None
        for t, name in sorted(self.markers.items()):
            t = round(t/1000, 1)
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
            score_text = TextClip(text=f"{self.home.text()}: {home}  {self.away.text()}: {away}", 
                                  font_size=40, color='white', 
                                  duration=clip.duration,
                                  margin=(10,10), bg_color="black")
            score_text = score_text.with_position(("center", "top"))
            # Combine the video and text
            annotated_clip = CompositeVideoClip([clip, score_text])
            subclips.append(annotated_clip)
        final = concatenate_videoclips(subclips)
        final.write_videofile("output.mp4", fps=24, codec='libx264', threads=4)
        video.close()

    def show_preview(self):
        start = self.player.get_time()/1000
        video_clip = VideoFileClip(self.video_path).subclipped(start, start+10)
        popup = PreviewPopup(self.make_scoreboard_composite(video_clip, 10))
        popup.exec()

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
                if name == Marker.MarkerType.HOME_PT:
                    home += 1
                elif name == Marker.MarkerType.AWAY_PT:
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
        self.marker_list.addItem(Marker(name, t))

        self.timeline.set_markers(self.markers)
    def select_marker(self, marker):
        print(f"Move to marker: {marker.text()}")
        self.player.set_time(marker.timestamp)
    
    def delete_selected_markers(self):
        selected_markers = self.marker_list.selectedItems()

        if not selected_markers:
            print("No markers selected to delete.")
            return

        for marker in selected_markers:
            row = self.marker_list.row(marker)
            self.marker_list.takeItem(row)
            del marker

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec())
