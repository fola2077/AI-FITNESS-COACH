# ai_fitness_coach/src/capture/camera.py
import cv2


class CameraManager:
    """
    Tiny OpenCV wrapper.
    Keeps the first slice simple: no threads, no async,
    just grab-a-frame-whenever-asked.
    """

    def __init__(self, cam_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)  # CAP_DSHOW avoids long open delay on Windows
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")

        # best-effort property requests — many drivers ignore them, that’s OK
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

    def get_frame(self):
        """Returns a BGR `numpy.ndarray` or `None` on read failure."""
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        self.cap.release()
