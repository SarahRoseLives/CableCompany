# ui/video_player.py
import sys
import vlc
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QSlider, QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


class VideoPlayer(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.is_recording = False
        self.current_channel_name = ""

        # --- VLC Initialization ---
        # FIXED: Added flags to disable hardware decoding and Xlib integration
        # --avcodec-hw=none: Prevents the VAAPI crash you saw
        # --no-xlib: Essential for PyQt/Linux compatibility to prevent thread conflicts
        self.instance = vlc.Instance("--avcodec-hw=none --no-xlib")
        self.mediaplayer = self.instance.media_player_new()

        self.setup_ui()

    def setup_ui(self):
        # --- Video Frame ---
        self.video_frame = QFrame()
        self.video_frame.setObjectName("VideoFrame")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_frame.setStyleSheet("background-color: black;")

        # OSD (On Screen Display)
        self.osd = QLabel(self.video_frame)
        self.osd.setStyleSheet("background-color: rgba(0,0,0,180); color: white; padding: 10px; border-radius: 4px;")
        self.osd.hide()

        # --- Controls ---
        controls = QWidget()
        controls.setObjectName("ControlsBar")
        controls.setFixedHeight(65)
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(20, 0, 20, 0)

        # Play/Pause
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setStyleSheet("border-radius: 20px; background-color: rgba(255,255,255,0.1); border: none;")
        self.play_btn.clicked.connect(self.toggle_play)

        # Volume
        vol_icon = QLabel()
        vol_icon.setPixmap(self.style().standardPixmap(QStyle.SP_MediaVolume))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #4a5568; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #4299e1; border-radius: 2px; }
            QSlider::handle:horizontal { background: white; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)

        # Record Button
        self.rec_btn = QPushButton("Record")
        self.rec_btn.setObjectName("RecordBtn")
        self.rec_btn.setCheckable(True)
        self.rec_btn.clicked.connect(self.toggle_record)

        # Fullscreen Icon
        fs_btn = QPushButton()
        fs_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        fs_btn.setStyleSheet("background: transparent; border: none;")

        # Assemble Layout
        c_layout.addWidget(self.play_btn)
        c_layout.addSpacing(15)
        c_layout.addWidget(vol_icon)
        c_layout.addWidget(self.volume_slider)
        c_layout.addStretch()
        c_layout.addWidget(self.rec_btn)
        c_layout.addSpacing(10)
        c_layout.addWidget(fs_btn)

        self.layout.addWidget(self.video_frame)
        self.layout.addWidget(controls)

    def play_stream(self, name, ip):
        self.current_channel_name = name

        if self.mediaplayer.is_playing():
            self.mediaplayer.stop()

        # UDP Multicast URL
        url = f"udp://@{ip}:1234"

        self.status_message.emit(f"Buffering: {name}...")

        media = self.instance.media_new(url)
        # Network optimization flags
        media.add_option(":network-caching=300")
        media.add_option(":clock-jitter=0")
        media.add_option(":clock-synchro=0")

        self.mediaplayer.set_media(media)

        # Embed VLC
        if sys.platform.startswith("linux"):
            self.mediaplayer.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.mediaplayer.set_nsobject(int(self.video_frame.winId()))

        self.mediaplayer.play()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        self.show_osd(name, ip)
        QTimer.singleShot(1500, lambda: self.status_message.emit(f"Playing: {name} (Live UDP)"))

    def toggle_play(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.status_message.emit("Paused")
        else:
            self.mediaplayer.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.status_message.emit(f"Playing: {self.current_channel_name}")

    def set_volume(self, volume):
        self.mediaplayer.audio_set_volume(volume)

    def show_osd(self, name, ip):
        self.osd.setText(f"<b>{name}</b><br><span style='font-size:10px; color:#ccc'>UDP Multicast | {ip}</span>")
        self.osd.adjustSize()
        self.osd.move(self.video_frame.width() - self.osd.width() - 20, 20)
        self.osd.show()
        self.osd.raise_()
        QTimer.singleShot(4000, self.osd.hide)

    def toggle_record(self):
        if self.rec_btn.isChecked():
            self.is_recording = True
            self.rec_btn.setText(" Recording")
            self.status_message.emit("Recording started (UI Simulation)...")
        else:
            self.is_recording = False
            self.rec_btn.setText(" Record")
            self.status_message.emit("Recording Saved.")