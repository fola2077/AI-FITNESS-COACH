# ai_fitness_coach/src/capture/camera.py
import cv2

class CameraManager:
    """
    Unified camera manager that can handle both live camera and video files.
    """
    def __init__(self, source=0):
        self.source = source
        self.is_video_file = isinstance(source, str)
        self.cap = cv2.VideoCapture(source)
    
    def get_frame(self):
        """Returns a BGR numpy.ndarray or None on read failure."""
        if not self.isOpened():
            return None
        
        ok, frame = self.cap.read()
        if not ok:
            return None
            
        return frame

    def isOpened(self):
        """Check if the camera or video file is opened."""
        return self.cap is not None and self.cap.isOpened()

    def get_property(self, prop_id):
        """Generic method to get a video capture property."""
        if self.cap:
            return self.cap.get(prop_id)
        return 0

    def release(self):
        """Release the video capture."""
        if self.cap:
            self.cap.release()
            self.cap = None