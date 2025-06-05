"""
Push-Up Tracker – Minimal Prototype
-----------------------------------
Tracks left-elbow angle in real time with MediaPipe Pose and counts push-ups.

Requirements:
    pip install opencv-python mediapipe numpy
Run:
    python pushup_tracker.py
Press <ESC> to quit.
"""

from collections import deque
import cv2
import mediapipe as mp
import numpy as np


# ---------- Geometry helper -------------------------------------------------- #
def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return the included angle ABC (at vertex b) in degrees."""
    ba, bc = a - b, c - b
    cos_val = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos_val, -1.0, 1.0)))


# ---------- Rep-counting state machine --------------------------------------- #
class PushUpCounter:
    """
    Counts reps using elbow-angle thresholds.
    A rep is completed when we move from 'down' (small angle)
    back to 'up' (large angle).
    """

    def __init__(self, down_thresh: float = 70.0, up_thresh: float = 160.0, smooth: int = 4):
        self.down_thresh, self.up_thresh = down_thresh, up_thresh
        self.buffer = deque(maxlen=smooth)
        self.state = "up"         # current posture
        self.count = 0

    def update(self, elbow_angle: float):
        self.buffer.append(elbow_angle)
        avg = np.mean(self.buffer)

        if avg < self.down_thresh and self.state == "up":
            self.state = "down"
        elif avg > self.up_thresh and self.state == "down":
            self.state = "up"
            self.count += 1
        return self.state, self.count


# ---------- Main loop -------------------------------------------------------- #
def main():
    mp_pose = mp.solutions.pose
    draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    with mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as pose:
        counter = PushUpCounter()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)            # mirror view
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                # Left arm landmarks
                shoulder = np.array([lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x * w,
                                     lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h])
                elbow    = np.array([lm[mp_pose.PoseLandmark.LEFT_ELBOW].x * w,
                                     lm[mp_pose.PoseLandmark.LEFT_ELBOW].y * h])
                wrist    = np.array([lm[mp_pose.PoseLandmark.LEFT_WRIST].x * w,
                                     lm[mp_pose.PoseLandmark.LEFT_WRIST].y * h])

                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                state, reps = counter.update(elbow_angle)

                # --- overlays -------------------------------------------------
                colour = (0, 255, 0) if state == "up" else (0, 0, 255)
                cv2.circle(frame, tuple(elbow.astype(int)), 8, colour, -1)
                cv2.putText(frame, f"Elbow: {elbow_angle:5.1f}°",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Reps: {reps}",
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

                draw.draw_landmarks(frame, res.pose_landmarks,
                                    mp_pose.POSE_CONNECTIONS,
                                    landmark_drawing_spec=draw.DrawingSpec(color=(0, 255, 255), thickness=2),
                                    connection_drawing_spec=draw.DrawingSpec(color=(255, 0, 255), thickness=2))

            cv2.imshow("Push-Up Tracker", frame)
            if cv2.waitKey(1) & 0xFF == 27:      # ESC
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
