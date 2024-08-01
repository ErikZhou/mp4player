import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, 
                             QSlider, QLabel, QComboBox, QMainWindow, QAction, QStyle, QMessageBox)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTime
from PyQt5.QtGui import QKeyEvent, QIcon

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Player")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.init_ui()
        self.create_menu()

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        self.last_positions = self.load_positions()
        self.current_file = ""

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Video display area
        self.video_widget = QVideoWidget()
        main_layout.addWidget(self.video_widget)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self.set_position)
        main_layout.addWidget(self.progress_slider)

        # Time labels
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(0)

        self.current_time_label = QLabel("00:00:00")
        self.total_time_label = QLabel("00:00:00")

        label_style = """
            QLabel {
                font-size: 10px;
                min-height: 15px;
                max-height: 15px;
            }
        """
        self.current_time_label.setStyleSheet(label_style)
        self.total_time_label.setStyleSheet(label_style)

        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)

        time_container = QWidget()
        time_container.setLayout(time_layout)
        time_container.setFixedHeight(15)

        main_layout.addWidget(time_container)

        # Combined control layout
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Play controls
        play_control_layout = QHBoxLayout()
        play_control_layout.setSpacing(5)

        button_style = """
            QPushButton {
                min-height: 20px;
                max-height: 20px;
                padding: 0px 10px;
            }
        """

        self.backward_button = QPushButton('<<')
        self.backward_button.clicked.connect(self.backward)
        self.backward_button.setStyleSheet(button_style)

        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.play_pause_video)
        self.play_button.setStyleSheet(button_style)

        self.forward_button = QPushButton('>>')
        self.forward_button.clicked.connect(self.forward)
        self.forward_button.setStyleSheet(button_style)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_video)
        self.stop_button.setStyleSheet(button_style)

        play_control_layout.addWidget(self.backward_button)
        play_control_layout.addWidget(self.play_button)
        play_control_layout.addWidget(self.forward_button)
        play_control_layout.addWidget(self.stop_button)

        control_layout.addLayout(play_control_layout)

        # Volume control
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume_slider)
        control_layout.addLayout(volume_layout)

        # Playback speed control
        speed_layout = QHBoxLayout()
        self.speed_combo = QComboBox()
        speeds = ["0.5x", "0.75x", "0.85x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"]
        self.speed_combo.addItems(speeds)
        self.speed_combo.setCurrentText("1.0x")  # Set default speed
        self.speed_combo.currentTextChanged.connect(self.set_playback_speed)
        speed_layout.addWidget(QLabel("Speed:"))
        speed_layout.addWidget(self.speed_combo)
        control_layout.addLayout(speed_layout)

        main_layout.addLayout(control_layout)

        self.central_widget.setLayout(main_layout)

    def create_menu(self):
        # Create menubar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')

        # Open action
        open_action = QAction(QIcon.fromTheme("document-open"), 'Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open movie')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Exit action
        exit_action = QAction(QIcon.fromTheme("application-exit"), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def load_positions(self):
        try:
            with open('last_positions.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_positions(self):
        with open('last_positions.json', 'w') as f:
            json.dump(self.last_positions, f)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Movie", "", "MP4 files (*.mp4)")
        if file_name:
            self.current_file = file_name
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_name)))
            self.play_button.setEnabled(True)
            
            # Check if there's a saved position for this file
            if file_name in self.last_positions:
                position = self.last_positions[file_name]
                reply = QMessageBox.question(self, 'Resume Playback', 
                                             'Do you want to resume from where you left off?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.media_player.setPosition(position)
            
            self.play_pause_video()

    def play_pause_video(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_video(self):
        self.media_player.stop()
        # Save the current position when stopping
        if self.current_file:
            self.last_positions[self.current_file] = self.media_player.position()
            self.save_positions()

    def closeEvent(self, event):
        # Save the current position when closing the application
        if self.current_file:
            self.last_positions[self.current_file] = self.media_player.position()
            self.save_positions()
        event.accept()

    def media_state_changed(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    def position_changed(self, position):
        self.progress_slider.setValue(position)
        self.update_current_time(position)

    def duration_changed(self, duration):
        self.progress_slider.setRange(0, duration)
        self.update_total_time(duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_volume(self, volume):
        self.media_player.setVolume(volume)

    def update_current_time(self, position):
        current_time = QTime(0, 0, 0).addMSecs(position)
        self.current_time_label.setText(current_time.toString("hh:mm:ss"))

    def update_total_time(self, duration):
        total_time = QTime(0, 0, 0).addMSecs(duration)
        self.total_time_label.setText(total_time.toString("hh:mm:ss"))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Left:
            self.backward()
        elif event.key() == Qt.Key_Right:
            self.forward()
        elif event.key() == Qt.Key_Space:
            self.play_pause_video()
        else:
            super().keyPressEvent(event)

    def backward(self):
        self.media_player.setPosition(max(0, self.media_player.position() - 1000))

    def forward(self):
        self.media_player.setPosition(min(self.media_player.duration(), self.media_player.position() + 1000))

    def set_playback_speed(self, speed_text):
        speed = float(speed_text[:-1])  # Remove 'x' and convert to float
        self.media_player.setPlaybackRate(speed)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())