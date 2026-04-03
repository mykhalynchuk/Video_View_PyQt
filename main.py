import sys
import cv2

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtGui import QImage, QPixmap

class VideoThread(QThread):
    changePixmap = pyqtSignal(object)

    def __init__(self, cameraIndex):
        super().__init__()
        self.running = True
        self.cameraIndex = cameraIndex # store camera index to open correct device

    def run(self):
        cap = cv2.VideoCapture(self.cameraIndex)

        # Continuous frame capture loop
        while self.running:
            ret, frame = cap.read()

            # Only emit frame if successfully captured
            if ret:
                self.changePixmap.emit(frame)

        # Important: release camera resource when thread stops
        cap.release()

    def stop(self):
        # Stop loop safely from main thread
        self.running = False


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.thread = None  # will hold reference to video thread

        self.layout = QVBoxLayout()

        self.label = QLabel("Video")
        self.label.setFixedSize(640, 480)  # fixed size prevents UI resizing flicker

        self.buttonStart = QPushButton("Start")
        self.buttonStart.clicked.connect(self.startVideoThread)

        self.buttonStop = QPushButton("Stop")
        self.buttonStop.clicked.connect(self.stopVideoThread)

        self.combo = QComboBox()

        # Mapping human-readable names to actual camera indices
        self.cameras = {
            "Camera" : 0,
            "Laptop" : 1
        }
        for name in self.cameras:
            self.combo.addItem(name)

        self.combo.currentIndexChanged.connect(self.onChange)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.buttonStart)
        self.layout.addWidget(self.buttonStop)
        self.layout.addWidget(self.combo)

        self.setLayout(self.layout)

    def startVideoThread(self):
        # Prevent starting multiple threads at the same time
        if self.thread and self.thread.isRunning():
            return

        # Get selected camera index from mapping
        name = self.combo.currentText()
        cameraIndex = self.cameras[name]

        self.thread = VideoThread(cameraIndex)
        self.thread.changePixmap.connect(self.updateLabel)
        self.thread.start()

        self.label.clear()

    def stopVideoThread(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()  # wait until thread fully stops

    def onChange(self, index):
        # If thread is not started yet, do nothing
        if not self.thread:
            return

        # Stop current video stream before switching camera
        self.thread.stop()
        self.thread.wait()

        # Get new camera index from mapping
        name = self.combo.currentText()
        cameraIndex = self.cameras[name]

        # Start new thread with selected camera
        self.thread = VideoThread(cameraIndex=index)
        self.thread.changePixmap.connect(self.updateLabel)
        self.thread.start()


    def updateLabel(self, frame):
        # Convert OpenCV BGR image to RGB
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgbImage.shape
        bytes_per_line = ch * w

        # Create Qt image from raw data
        qtImage = QImage(
            rgbImage.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888)

        # Scale image to fit QLabel while keeping aspect ratio
        self.label.setPixmap(QPixmap.fromImage(qtImage).scaled(
            self.label.width(),
            self.label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

app = QApplication(sys.argv)

window = App()
window.show()

app.exec()