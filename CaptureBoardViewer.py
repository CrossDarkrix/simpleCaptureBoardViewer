import ast
import threading
import sys

import cv2
import pyaudio
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy


def check_device(): # check index from "USB Capture Board"
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        data = ast.literal_eval('{}'.format(audio.get_device_info_by_index(i)).encode("utf-8", errors='ignore').decode("utf-8", errors='ignore'))
        if data["hostApi"] == 2 and "USB3.0 Capture" in data["name"]:
            return data["index"]


stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                     rate=96000,
                                     channels=1,
                                     input_device_index=check_device(),
                                     input=True) # WebCam mic input.
play = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                   rate=96000, channels=1,
                                   output_device_index=pyaudio.PyAudio().get_default_output_device_info()['index'],
                                   output=True) # output to Speaker

def _audio():
    while True:
        play.write(stream.read(128))

class _QLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = QPixmap()

    def setPixmap(self, p):
        self.p = p
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self.p)


class Window(QMainWindow):
    video_size = QSize(1280, 700)
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.threads = threading.Thread(target=_audio, daemon=True)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)
        self.cap.set(cv2.CAP_PROP_FPS, 120)
        self._audio_video_timer = QTimer(self)
        self._audio_video_timer.singleShot(0, self._audio)
        self._audio_video_timer.timeout.connect(self._video)
        self._audio_video_timer.start()

    def _video(self):
        ret, frame = self.cap.read()
        if ret:
            h, w, ch = frame.shape
            bytesPerLine = ch * w
            self.img_label1.setPixmap(QPixmap.fromImage(QImage(frame, w, h, bytesPerLine, QImage.Format.Format_BGR888), Qt.ImageConversionFlag.NoOpaqueDetection))

    def closeEvent(self, _):
        self.threads.join(0)
        self._audio_video_timer.stop()
        self.cap.release()

    def initUI(self):
        self.img_label1 = _QLabel()
        self.img_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(self.img_label1)
        self.setMinimumSize(QSize(480, 360))
        self.resize(self.video_size)

    def resizeEvent(self, event):
        self.img_label1.resize(event.size())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Q:
            self.threads.join(0)
            self._audio_video_timer.stop()
            self.cap.release()
            sys.exit(0)
        if e.key() == Qt.Key.Key_Escape:
            self.threads.join(0)
            self._audio_video_timer.stop()
            self.cap.release()
            sys.exit(0)

    def _audio(self):
        self.threads.start()

    def _start(self):
        return self.app.exec()

def main():
    app = QApplication([])
    ex = Window(app=app)
    ex.show()
    sys.exit(ex._start())

if __name__ == "__main__":
    main()