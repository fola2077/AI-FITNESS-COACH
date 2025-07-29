import cv2, time, pathlib
from src.pose.pose_detector import PoseDetector
from src.preprocess.one_euro import OneEuroFilter
from src.utils.math_utils import joint_angle

def run_on_video(path, max_frames=None):
    cap = cv2.VideoCapture(str(path))
    det = PoseDetector(model_complexity=0)
    filters = {i: (OneEuroFilter(), OneEuroFilter()) for i in range(33)}
    knee_angles = []

    while True:
        ok, frame = cap.read()
        if not ok or (max_frames and len(knee_angles) >= max_frames):
            break

        out = det.detect(frame)
        if out:
            lms, _ = out
            t = time.perf_counter()
            for i, lm in enumerate(lms):
                fx, fy = filters[i]
                lm.x = fx.filter(lm.x, t)
                lm.y = fy.filter(lm.y, t)
            hip, knee, ankle = lms[24], lms[26], lms[28]
            ang = joint_angle(hip.x, hip.y, knee.x, knee.y, ankle.x, ankle.y)
            knee_angles.append(round(ang, 1))

    cap.release(); det.close()
    return knee_angles
