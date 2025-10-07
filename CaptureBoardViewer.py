import ast
import asyncio
import multiprocessing
import sys
import threading
import platform
import cv2
import pyaudio
from PySide6.QtCore import Qt, QSize
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


def _audio_loader():
    while True:
        try:
            play.write(stream.read(128))
        except SystemExit:
            break

def _audio():
    with multiprocessing.Pool(3) as _pool:
        _pool.apply(_audio_loader)

def _return_data(data):
    return data


def _video():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)
    cap.set(cv2.CAP_PROP_FPS, 60)
    while True:
        try:
            ret, frame = cap.read()
            if ret:
                h, w, ch = frame.shape
                bytesPerLine = ch * w
                data = {"data": frame,
                        "w": w,
                        "h": h,
                        "bytesPerLine": bytesPerLine}
                yield QImage(data["data"], data["w"], data["h"], data["bytesPerLine"], QImage.Format.Format_BGR888)
        except SystemExit:
            break
    cap.release()

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
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self.p)


class Window(QMainWindow):
    video_size = QSize(1280, 700)
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.process = threading.Thread(target=_audio, daemon=True)
        self.thread = threading.Thread(target=self._video, daemon=True)
        asyncio.run(self._load())

    async def _load(self):
        await asyncio.gather(asyncio.to_thread(self._load2), self._load1())

    async def _load1(self):
        self.process.start()

    def _load2(self):
        self.thread.start()

    def _video(self):
        [self.img_label1.setPixmap(QPixmap.fromImage(image, Qt.ImageConversionFlag.NoOpaqueDetection)) for image in _video()]

    def closeEvent(self, _):
        try:
            self.process.join(0)
            self.thread.join(0)
        except:
            pass
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
            try:
                self.process.join(0)
                self.thread.join(0)
            except:
                pass
            sys.exit(0)
        if e.key() == Qt.Key.Key_Escape:
            try:
                self.process.join(0)
                self.thread.join(0)
            except:
                pass
            sys.exit(0)


def main():
    app = QApplication([])
    ex = Window()
    ex.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    if platform.system() == 'Linux':
        multiprocessing.set_start_method('fork')
    else:
        multiprocessing.set_start_method('spawn')
    main()