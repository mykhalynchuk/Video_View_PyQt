import sys
import cv2

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtGui import QImage, QPixmap

class VideoThread(QThread):
    change_pixmap = pyqtSignal(object)

    def __init__(self, camera_index):
        super().__init__()
        self.running = True
        self.camera_index = camera_index

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)

        while self.running:
            ret, frame = cap.read()
            if ret:
                self.change_pixmap.emit(frame)

        cap.release()

    def stop(self):
        self.running = False


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.thread = None

        self.layout = QVBoxLayout()

        self.label = QLabel("Video")
        self.label.setFixedSize(640, 480)

        self.button_start = QPushButton("Start")
        self.button_start.clicked.connect(self.start_video_thread)

        self.button_stop = QPushButton("Stop")
        self.button_stop.clicked.connect(self.stop_video_thread)

        self.combo = QComboBox()
        self.combo.addItems(["Camera 0 (Laptop)", "Camera 1 (USB)"])
        self.combo.currentIndexChanged.connect(self.on_change)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button_start)
        self.layout.addWidget(self.button_stop)
        self.layout.addWidget(self.combo)

        self.setLayout(self.layout)

    def start_video_thread(self):
        if self.thread and self.thread.isRunning():
            return

        camera_index = self.combo.currentIndex()

        self.thread = VideoThread(camera_index)
        self.thread.change_pixmap.connect(self.update_label)
        self.thread.start()
        self.label.clear()

    def stop_video_thread(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()

    def on_change(self, index):
        self.thread.stop()
        self.thread.wait()

        self.thread = VideoThread(camera_index=index)
        self.thread.change_pixmap.connect(self.update_label)
        self.thread.start()


    def update_label(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        self.label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.label.width(),
            self.label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
app = QApplication(sys.argv)
window = App()
window.show()
app.exec()