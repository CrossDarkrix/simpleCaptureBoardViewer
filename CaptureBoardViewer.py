import os
import platform
import sys
from PySide6.QtCore import Qt, QSize, QEvent, Slot, QMicrophonePermission, QCameraPermission
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtMultimedia import QCamera, QCameraFormat, QMediaDevices, QVideoSink, QMediaCaptureSession, QVideoFrame, \
    QAudioSink, QAudioOutput, QAudioInput, QAudioSource
from PySide6.QtWidgets import QMainWindow, QLabel, QApplication, QSizePolicy, QMenu

if platform.system() == 'Windows':
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
    video_size = QSize(1200, 800) # Window and video size.
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.video_frame = [QVideoFrame]
        self.initUI()
        self.setWindowTitle("Capture Board Viewer")
        self.check_permission()
        self.init_Video_Audio()

    def check_permission(self): # set Permission.
        microphonePermission = QMicrophonePermission()
        micPermissionStatus = self.app.checkPermission(microphonePermission)
        if micPermissionStatus == Qt.PermissionStatus.Undetermined:
            self.app.requestPermission(microphonePermission, self.app, None)
        cameraPermission = QCameraPermission()
        camPermissionStatus = self.app.checkPermission(cameraPermission)
        if camPermissionStatus == Qt.PermissionStatus.Undetermined:
            self.app.requestPermission(cameraPermission, self.app, None)

    def init_Video_Audio(self):
        # camera and audio setting.
        self.cap = QMediaCaptureSession()
        self.audio_source = QAudioSource(QMediaDevices.defaultAudioInput(), format=QMediaDevices.defaultAudioInput().preferredFormat())
        self.audio_sink = QAudioSink(QMediaDevices.defaultAudioOutput(), format=QMediaDevices.defaultAudioInput().preferredFormat())
        # camera setting. set video size: 1200x800, max video frame rate: 75FPS.
        camera = QCamera(cameraDevice=QMediaDevices.defaultVideoInput(), cameraFormat=QCameraFormat(resolution=self.video_size, maxFrameRate=75))
        self.cap.setCamera(camera)
        # video setting.
        self.cap.setVideoSink(QVideoSink(self))
        self.cap.videoSink().videoFrameChanged.connect(self._setImage)
        self.cap.setAudioInput(QAudioInput(self.audio_source))
        self.cap.setAudioOutput(QAudioOutput(self.audio_sink))
        self.io_device_input = self.audio_source.start() # camera input audio.
        self.io_device_output = self.audio_sink.start() # output to speaker.
        self.io_device_input.readyRead.connect(self.set_audio) # set Audio input to Speaker.
        self.cap.camera().start()  # camera start.

    @Slot(QVideoFrame)
    def _setImage(self, frame: QVideoFrame): # Video frame set to QLabel and audio output to speaker.
        if self.io_device_input is None: # Stopped Audio to restart audio and video
            self.init_Video_Audio()
        if self.io_device_output is None: # Stopped Audio to restart audio and video
            self.init_Video_Audio()
        if self._is_StoppedVideo(frame): # Stopped Video to restart audio and video
            self.init_Video_Audio()
        try:
            self.img_label1.setPixmap(QPixmap.fromImage(frame.toImage())) # video frame set Pixelmap.
        except:
            pass

    def set_audio(self): # set audio to speaker.
        if self.io_device_input is None: # Stopped Audio to restart audio and video
            self.init_Video_Audio()
        if self.io_device_output is None: # Stopped Audio to restart audio and video
            self.init_Video_Audio()
        try:
            self.io_device_output.write(self.io_device_input.readAll()) # io input device output data to speaker device.
        except:
            pass

    def _is_StoppedVideo(self, frame):
        if self.video_frame[0] != frame:
            self.video_frame[0] = frame
            return False
        else:
            return True

    def closeEvent(self, _):
        sys.exit(0)

    def initUI(self):
        self.img_label1 = _QLabel()
        self.img_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(self.img_label1)
        self.setMinimumSize(QSize(480, 360)) # minimum size is 480x360.
        self.resize(self.video_size) # resize window to 1200x800

    def resizeEvent(self, event):
        self.img_label1.resize(event.size())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Q: # press Q key to exit Application.
            sys.exit(0)
        if e.key() == Qt.Key.Key_Escape: # press Esc key to exit application.
            sys.exit(0)

    def mousePressEvent(self, event): # Application Right click Menu.
        if event.button() == Qt.MouseButton.RightButton and event.type() == QEvent.Type.MouseButtonPress:
            menu = QMenu()
            menu.addAction("close Window", self._close_window) # this is application close.
            menu.addAction("restart Audio and Video", self._restart_Audio_and_video) # resetting video and audio.
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