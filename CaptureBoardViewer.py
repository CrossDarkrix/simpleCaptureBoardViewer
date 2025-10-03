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
        while self.playing:
            ret, frame = cap.read()
            if ret:
                h, w, ch = frame.shape
                bytesPerLine = ch * w
                self.change_pixmap_signal.emit(QImage(frame, w, h, bytesPerLine, QImage.Format.Format_BGR888).scaled(QSize(1920, 1080), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
        self.img_label1.setPixmap(QPixmap.fromImage(image).scaled(self.video_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication([])
    ex = Window()
    ex.show()
    sys.exit(app.exec())