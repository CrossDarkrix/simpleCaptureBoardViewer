import ast
import multiprocessing
import platform
import sys
import pyaudio
from PySide6.QtCore import Qt, QSize, QEvent, Slot
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtMultimedia import QCamera, QCameraFormat, QMediaDevices, QVideoSink, QMediaCaptureSession, QVideoFrame
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy, QMenu


def check_device():  # check index from "USB Capture Board"
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        data = ast.literal_eval('{}'.format(audio.get_device_info_by_index(i)).encode("utf-8", errors='ignore').decode("utf-8", errors='ignore'))
        if data["hostApi"] == 2 and "USB3.0 Capture" in data["name"]:
            return data["index"]

stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                    rate=96000,
                                    channels=1,
                                    input_device_index=check_device(),
                                    input=True)  # input WebCam mic.

play = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                  rate=96000,
                                  channels=1,
                                  output_device_index=pyaudio.PyAudio().get_default_output_device_info()['index'],
                                  output=True)  # output to Speaker

def _audio():
    while True:
        try:
            yield stream.read(128)
        except SystemExit:
            break

def _process_audio():
    [play.write(microphone) for microphone in _audio()]

class _QLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = QPixmap()

    def setPixmap(self, p):
        self.p = p
        try:
            self.update()
        except:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering)
        painter.drawPixmap(self.rect(), self.p)

class Window(QMainWindow):
    video_size = QSize(1024, 800)
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        multiprocessing.Process(target=_process_audio, daemon=True).start()
        camera = QCamera(cameraDevice=QMediaDevices.defaultVideoInput())
        camera.setCameraFormat(QCameraFormat(resolution=self.video_size, maxFrameRate=60))
        self.cap = QMediaCaptureSession()
        self.cap.setCamera(camera)
        video_sink = QVideoSink(self)
        self.cap.setVideoSink(video_sink)
        self.cap.videoSink().videoFrameChanged.connect(self._setImage)
        self.cap.camera().start()

    @Slot(QVideoFrame)
    def _setImage(self, frame: QVideoFrame):
        self.img_label1.setPixmap(QPixmap.fromImage(frame.toImage()))

    @Slot(QImage)
    def _video(self, image):
        self.img_label1.clear()
        self.img_label1.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, _):
        sys.exit(0)

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
            sys.exit(0)
        if e.key() == Qt.Key.Key_Escape:
            sys.exit(0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and event.type() == QEvent.Type.MouseButtonPress:
            menu = QMenu()
            menu.addAction("close Window", self._close_window)
            menu.addAction("set View ON/OFF", self._setVisble_label)
            menu.exec(self.mapToGlobal(event.position().toPoint()))

    def _close_window(self):
        sys.exit(0)

    def _setVisble_label(self):
        if self.img_label1.isVisible():
            self.img_label1.setVisible(False)
        else:
            self.img_label1.setVisible(True)

    def _Exec(self):
        return self.app.exec()

def main():
    ex = Window(app=QApplication([]))
    ex.show()
    sys.exit(ex._Exec())

if __name__ == "__main__":
    if platform.system() == 'Darwin':
        multiprocessing.set_start_method('fork')
    else:
        multiprocessing.set_start_method('spawn')
    main()