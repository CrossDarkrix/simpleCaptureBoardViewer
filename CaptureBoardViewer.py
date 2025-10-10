import os
import sys
from PySide6.QtCore import Qt, QSize, QEvent, Slot, QMicrophonePermission, QCameraPermission
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtMultimedia import QCamera, QCameraFormat, QMediaDevices, QVideoSink, QMediaCaptureSession, QVideoFrame, \
    QAudioSink, QAudioOutput, QAudioInput, QAudioSource, QAudioFormat
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy, QMenu

os.environ["QT_MEDIA_BACKEND"] = "windows"
os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "directshow"


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
    video_size = QSize(1200, 800)
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.check_permission()
        self.init_Video_Audio()

    def check_permission(self):
        microphonePermission = QMicrophonePermission()
        micPermissionStatus = self.app.checkPermission(microphonePermission)
        if micPermissionStatus == Qt.PermissionStatus.Undetermined:
            self.app.requestPermission(microphonePermission, self.app, None)
        cameraPermission = QCameraPermission()
        camPermissionStatus = self.app.checkPermission(cameraPermission)
        if camPermissionStatus == Qt.PermissionStatus.Undetermined:
            self.app.requestPermission(cameraPermission, self.app, None)

    def init_Video_Audio(self):
        camera = QCamera(cameraDevice=QMediaDevices.defaultVideoInput())
        camera.setCameraFormat(QCameraFormat(resolution=self.video_size, maxFrameRate=75))
        self.cap = QMediaCaptureSession()
        audio_format = QAudioFormat()
        audio_format.setSampleRate(96000)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.audio_source = QAudioSource(QMediaDevices.defaultAudioInput(), format=audio_format)
        output_format = QAudioFormat()
        output_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        output_format.setSampleRate(96000)
        output_format.setChannelCount(1)
        self.audio_sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format=output_format)
        self.audio_source.setVolume(100)
        self.cap.setCamera(camera)
        video_sink = QVideoSink(self)
        self.cap.setVideoSink(video_sink)
        self.cap.videoSink().videoFrameChanged.connect(self._setImage)
        self.cap.camera().start()
        self.audio_sink.setVolume(100)
        self.cap.setAudioInput(QAudioInput(self.audio_source))
        self.cap.setAudioOutput(QAudioOutput(self.audio_sink))
        self.io_device_input = self.audio_source.start()
        self.io_device_output = self.audio_sink.start()

    @Slot(QVideoFrame)
    def _setImage(self, frame: QVideoFrame):
        self.io_device_output.write(self.io_device_input.readAll())
        self.img_label1.setPixmap(QPixmap.fromImage(frame.toImage()))

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
            menu.addAction("restart Audio and Video", self._restart_Audio_and_video)
            menu.exec(self.mapToGlobal(event.position().toPoint()))

    def _restart_Audio_and_video(self):
        self.init_Video_Audio()

    def _close_window(self):
        sys.exit(0)

    def _Exec(self):
        return self.app.exec()


def main():
    ex = Window(app=QApplication([]))
    ex.show()
    sys.exit(ex._Exec())

if __name__ == "__main__":
    main()