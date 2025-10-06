import ast
import asyncio
import sys
import cv2
import pyaudio
from PySide6.QtCore import Qt, Signal, Slot, QThread, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy

_Playing = [True]

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
    while _Playing[0]:
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


class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    playing = True
    _Playing[0] = True

    def run(self):
        async def _video():
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)
            cap.set(cv2.CAP_PROP_FPS, 120)
            while self.playing:
                ret, frame = cap.read()
                if ret:
                    h, w, ch = frame.shape
                    bytesPerLine = ch * w
                    self.change_pixmap_signal.emit(QImage(frame, w, h, bytesPerLine, QImage.Format.Format_BGR888))
            cap.release()

        async def _run():
            await asyncio.gather(asyncio.to_thread(_audio), _video())

        asyncio.run(_run())

    def stop(self):
        self.playing = False
        _Playing[0] = False
        self.wait()


class Window(QMainWindow):
    video_size = QSize(1280, 700)
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
        # self.setFixedSize(self.video_size)
        self.img_label1 = _QLabel()
        self.img_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(self.img_label1)
        self.setMinimumSize(QSize(480, 360))
        self.resize(self.video_size)

    def resizeEvent(self, event):
        self.img_label1.resize(event.size())

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

def main():
    app = QApplication([])
    ex = Window()
    ex.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()