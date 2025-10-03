import sys
import cv2
from PySide6.QtCore import Qt, Signal, Slot, QThread, QSize
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication
from PySide6.QtGui import QImage, QPixmap

class VideoThread(QThread):
    change_pixmap_signal = Signal(QImage)
    playing = True

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
                self.change_pixmap_signal.emit(QImage(frame.data, w, h, bytesPerLine, QImage.Format.Format_BGR888).scaled(QSize(1280, 768), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).convertToFormat(QImage.Format.Format_RGBA32FPx4_Premultiplied, Qt.ImageConversionFlag.NoOpaqueDetection))
        cap.release()

    def stop(self):
        self.playing = False
        self.wait()

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

    @Slot(QImage)
    def update_image(self, image):
        self.img_label1.setPixmap(QPixmap.fromImage(image, Qt.ImageConversionFlag.NoOpaqueDetection).scaled(self.video_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication([])
    ex = Window()
    ex.show()
    sys.exit(app.exec())