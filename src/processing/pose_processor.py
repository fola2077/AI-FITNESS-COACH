import cv2
import numpy as np
import time
from src.pose.pose_detector import PoseDetector
from src.utils.math_utils import joint_angle

class PoseProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.phase = "START"
        self.phase_tracker = "START"
        self.start_time = time.time()
        self.frame_counter = 0
        self.fps = 0

    def process_frame(self, frame):
        self.frame_counter += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.start_time = time.time()
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.pose_detector.process_frame(frame_rgb)

        results = {'fps': self.fps}
        if self.pose_detector.results.pose_landmarks:
            right_hip = self.pose_detector.get_landmark_coords('RIGHT_HIP')
            right_knee = self.pose_detector.get_landmark_coords('RIGHT_KNEE')
            right_ankle = self.pose_detector.get_landmark_coords('RIGHT_ANKLE')

            # --- FIX: Check if all required landmarks are detected before processing ---
            if all([right_hip, right_knee, right_ankle]):
                knee_angle = joint_angle(
                    right_hip[0], right_hip[1],
                    right_knee[0], right_knee[1],
                    right_ankle[0], right_ankle[1]
                )

                if knee_angle > 160:
                    self.phase_tracker = "TOP"
                elif knee_angle < 90 and self.phase_tracker == "TOP":
                    self.phase_tracker = "BOTTOM"
                
                results['knee_angle'] = knee_angle
                results['phase'] = self.phase_tracker
            # -------------------------------------------------------------------------

        annotated_frame = self.draw_overlays(frame.copy(), results)
        return annotated_frame, results

    def draw_overlays(self, frame, results):
        self.pose_detector.draw_landmarks(frame)
        
        bar_height = 50
        text_color = (255, 255, 255)
        font_scale = max(0.5, frame.shape[0] / 1440)
        thickness = max(1, int(font_scale * 2))

        info_text = ""
        if 'fps' in results:
            info_text += f"FPS: {int(results['fps'])}   "
        if 'knee_angle' in results:
            info_text += f"Knee Angle: {int(results['knee_angle'])}   "
        if 'phase' in results:
            info_text += f"Phase: {results['phase']}"

        sub_img = frame[0:bar_height, 0:frame.shape[1]]
        black_rect = np.ones(sub_img.shape, dtype=np.uint8) * 0
        res = cv2.addWeighted(sub_img, 0.7, black_rect, 0.3, 1.0)
        frame[0:bar_height, 0:frame.shape[1]] = res

        (text_width, text_height), _ = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_y = (bar_height + text_height) // 2
        cv2.putText(frame, info_text, (15, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, cv2.LINE_AA)

        return frame