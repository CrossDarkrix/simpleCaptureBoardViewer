import ast
import sys
import cv2
import time
import threading
import pyaudio
from PySide6.QtCore import Qt, Signal, Slot, QThread, QSize
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication
from PySide6.QtGui import QImage, QPixmap

class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    playing = True
    audio = pyaudio.PyAudio()

    def __init__(self):
        super().__init__()
        self.stream = self.audio.open(format=pyaudio.paFloat32,
                            rate=96000,
                            channels=1,
                            input_device_index=self.check_device(),
                            input=True,
                            frames_per_buffer=1024)
        self.play = self.audio.open(format=pyaudio.paFloat32,
                          rate=96000, channels=1,
                          output_device_index=self.audio.get_default_output_device_info()['index'],
                          output=True,
                          frames_per_buffer=1024
                          )
    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
        cap.set(cv2.CAP_PROP_FPS, 120)
        while self.playing:
            ret, frame = cap.read()
            if ret:
                h, w, ch = frame.shape
                bytesPerLine = ch * w
                self.play.write(self.stream.read(3024))
                self.change_pixmap_signal.emit(QImage(frame.data, w, h, bytesPerLine, QImage.Format.Format_BGR888).scaled(QSize(1280, 768), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).convertToFormat(QImage.Format.Format_RGBA32FPx4_Premultiplied, Qt.ImageConversionFlag.NoOpaqueDetection))
            time.sleep(0.01)
        cap.release()

    def stop(self):

        self.playing = False
        self.wait()

    def audio_stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def check_device(self):
        audio = pyaudio.PyAudio()
        for i in range(audio.get_device_count()):
            data = ast.literal_eval('{}'.format(audio.get_device_info_by_index(i)).encode("utf-8", errors='ignore').decode("utf-8", errors='ignore'))
            if data["hostApi"] == 2 and "USB3.0 Capture" in data["name"]:
                return data["index"]


class Window(QMainWindow):
    video_size = QSize(1280, 768)
    def __init__(self):
        super().__init__()    
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def closeEvent(self, _):
        self.thread.stop()

    def initUI(self):
        self.setFixedSize(self.video_size)
        self.img_label1 = QLabel()
        self.setCentralWidget(self.img_label1)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Q:
            self.thread.stop()
            sys.exit()
        if e.key() == Qt.Key.Key_Escape:
            self.thread.stop()
            sys.exit()

    @Slot(QImage)
    def update_image(self, image):
        self.img_label1.setPixmap(QPixmap.fromImage(image, Qt.ImageConversionFlag.NoOpaqueDetection).scaled(self.video_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication([])
    ex = Window()
    ex.show()
    sys.exit(app.exec())