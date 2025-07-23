# ai_fitness_coach/src/capture/camera.py
import cv2
import os

class CameraManager:
    """
    Unified camera manager that can handle both live camera and video files.
    """
    def __init__(self, source=0):
        self.source = source
        self.is_video_file = isinstance(source, str)
        
        # Additional validation for video files
        if self.is_video_file:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Video file not found: {source}")
            if not os.path.isfile(source):
                raise ValueError(f"Path is not a file: {source}")
        
        self.cap = cv2.VideoCapture(source)
        
        # Enhanced validation - only fail for video files
        if not self.cap.isOpened():
            if self.is_video_file:
                raise RuntimeError(f"Cannot open video file: {source}")
            # For webcam sources, we don't throw an error, just log
            print(f"⚠️  Warning: Cannot open camera {source} (camera may not be available)")
    
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
    
    def get_video_info(self):
        """Get video information for debugging."""
        if not self.cap:
            return None
        
        return {
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'is_video_file': self.is_video_file,
            'source': self.source
        }

    def release(self):
        """Release the video capture."""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
                print("🔄 Camera resources released")
        except Exception as e:
            print(f"Warning: Error releasing camera: {e}")
            
    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        self.release()