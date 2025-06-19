# ai_fitness_coach/src/capture/camera.py
import cv2


class CameraManager:
    """
    Unified camera manager that can handle both live camera and video files.
    """
    
    def __init__(self, source=0, width=640, height=480, fps=30):
        """
        Args:
            source: int for camera ID (0, 1, etc.) or str for video file path
            width, height: desired resolution (ignored for video files)
            fps: desired FPS (ignored for video files - uses video's native FPS)
        """
        self.source = source
        self.is_video_file = isinstance(source, str)
        self.cap = None
        self.video_fps = fps
        self.frame_count = 0
        self.total_frames = 0
        
        self._initialize_capture(width, height, fps)
    
    def _initialize_capture(self, width, height, fps):
        """Initialize the video capture based on source type."""
        if self.is_video_file:
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open video file: {self.source}")
            
            # Get video properties
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            print(f"Video loaded: {self.total_frames} frames at {self.video_fps:.1f} FPS")
            
        else:
            # Live camera setup
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open camera: {self.source}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    
    def get_frame(self):
        """Returns a BGR numpy.ndarray or None on read failure."""
        if not self.cap:
            return None
            
        if self.is_video_file:
            ok, frame = self.cap.read()
            if ok:
                self.frame_count += 1
            else:
                # End of video - optionally loop
                self.restart_video()
                ok, frame = self.cap.read()
                if ok:
                    self.frame_count = 1
        else:
            # Live camera - grab latest frame
            self.cap.grab()
            ok, frame = self.cap.retrieve()
        
        return frame if ok else None
    
    def restart_video(self):
        """Restart video from beginning (for looping)."""
        if self.is_video_file and self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.frame_count = 0
    
    def seek_to_frame(self, frame_number):
        """Seek to specific frame (video files only)."""
        if self.is_video_file and self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.frame_count = frame_number
    
    def get_progress(self):
        """Get video progress as percentage (0-100)."""
        if self.is_video_file and self.total_frames > 0:
            return (self.frame_count / self.total_frames) * 100
        return 0
    
    def get_time_info(self):
        """Get current time and duration info."""
        if self.is_video_file:
            current_time = self.frame_count / self.video_fps if self.video_fps > 0 else 0
            total_time = self.total_frames / self.video_fps if self.video_fps > 0 else 0
            return current_time, total_time
        return 0, 0
    
    def release(self):
        """Release the video capture."""
        if self.cap:
            self.cap.release()
            self.cap = None