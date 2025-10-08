import ast
import sys
import cv2
import pyaudio
from PySide6.QtCore import Qt, QSize, QEvent, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy, QMenu


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

class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    playing = True

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)
        cap.set(cv2.CAP_PROP_FPS, 120)
        while self.playing:
            ret, frame = cap.read()
            if ret:
                h, w, ch = frame.shape
                bytesPerLine = ch * w
                self.change_pixmap_signal.emit(QImage(frame, w, h, bytesPerLine, QImage.Format.Format_BGR888).convertToFormat(QImage.Format.Format_RGBA8888, Qt.ImageConversionFlag.NoOpaqueDetection))
        cap.release()

    def stop(self):
        self.playing = False
        self.wait()


class AudioThread(QThread):
    change_audio_signal = Signal(bytes)
    playing = True

    def __init__(self):
        super().__init__(None)
        self.stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                    rate=96000,
                                    channels=1,
                                    input_device_index=self.check_device(),
                                    input=True)  # input WebCam mic.

    def run(self):
        while self.playing:
            self.change_audio_signal.emit(self.stream.read(128))

    def check_device(self):  # check index from "USB Capture Board"
        audio = pyaudio.PyAudio()
        for i in range(audio.get_device_count()):
            data = ast.literal_eval('{}'.format(audio.get_device_info_by_index(i)).encode("utf-8", errors='ignore').decode("utf-8", errors='ignore'))
            if data["hostApi"] == 2 and "USB3.0 Capture" in data["name"]:
                return data["index"]

    def stop(self):
        self.playing = False
        self.wait()


class Window(QMainWindow):
    video_size = QSize(1200, 700)
    play = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                  rate=96000,
                                  channels=1,
                                  output_device_index=pyaudio.PyAudio().get_default_output_device_info()['index'],
                                  output=True)  # output to Speaker
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.thread1 = VideoThread()
        self.thread1.change_pixmap_signal.connect(self._video)
        self.thread2 = AudioThread()
        self.thread2.change_audio_signal.connect(self._audio)
        self.thread1.start()
        self.thread2.start()

    @Slot(QImage)
    def _video(self, image):
        self.img_label1.setPixmap(QPixmap.fromImage(image, Qt.ImageConversionFlag.NoOpaqueDetection))

    @Slot(bytes)
    def _audio(self, microphone):
        self.play.write(microphone)

    def _kill(self):
        self.thread1.stop()
        self.thread2.stop()

    def closeEvent(self, _):
        self._kill()
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
            self._kill()
            sys.exit(0)
        if e.key() == Qt.Key.Key_Escape:
            self._kill()
            sys.exit(0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and event.type() == QEvent.Type.MouseButtonPress:
            menu = QMenu()
            menu.addAction("close Window", self._close_window)
            menu.addAction("set View ON/OFF", self._setVisble_label)
            menu.exec(self.mapToGlobal(event.position().toPoint()))

    def _close_window(self):
        self._kill()
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
    main()