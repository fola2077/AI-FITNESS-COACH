"""
Benchmark three pose-estimation back-ends on a folder of videos
Usage: python pose_backends.py --videos data/test_clips --gt data/gt.json
"""

import argparse, time, json, cv2, numpy as np
from pathlib import Path
from collections import defaultdict

# ---------- 1.  NORMALISE LANDMARK FORMAT TO (x,y,score) * 17  ---------- #

def to_17_kpts(kpts, mapping):
    """Pick & re-order keypoints so every backend returns 17 joints."""
    out = []
    for src_idx in mapping:
        if src_idx is None:          # joint missing in that backend
            out.append([np.nan, np.nan, 0.0])
        else:
            out.append(kpts[src_idx])
    return np.asarray(out)           # shape (17,3)

# ---------- 2.  BACKEND WRAPPERS  --------------------------------------- #

class MediaPipeRunner:
    import mediapipe as mp
    _mp_pose = mp.solutions.pose.Pose(static_image_mode=False,
                                      model_complexity=1,
                                      enable_segmentation=False,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)
    _map = [0,11,12,13,14,15,16,23,24,25,26,27,28,None,None,31,32,   # → COCO-17
            ]  # fill with Nones where MP doesn’t map cleanly

    def infer(self, frame):
        res = self._mp_pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not res.pose_landmarks: return None
        kpts = [[l.x, l.y, l.visibility] for l in res.pose_landmarks.landmark]
        return to_17_kpts(kpts, self._map)

class MoveNetRunner:
    import tensorflow as tf, tensorflow_hub as hub
    model = hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4")
    _input_size, _map = 192, list(range(17))  # MoveNet already is COCO-17

    def infer(self, frame):
        img = cv2.resize(frame, (self._input_size, self._input_size))
        t = self.tf.convert_to_tensor(img[np.newaxis])
        outputs = self.model.signatures['serving_default'](t)
        kpts = outputs['output_0'].numpy()[0,0,:,:]  # (17,3)
        return kpts

# class OpenPoseRunner:
#     # Requires compiled OpenPose + pyopenpose wrapper in PYTHONPATH
#     import pyopenpose as op
#     _op_params = dict(model_folder="models/", model_pose="BODY_25",
#                       disable_blending=True)
#     opWrapper = op.WrapperPython(); opWrapper.configure(_op_params); opWrapper.start()
#     _map_body25_to_coco17 = [0,2,5,3,6,4,7,9,12,10,13,11,14,24,21,19,22]

#     def infer(self, frame):
#         datum = self.op.Datum(); datum.cvInputData = frame; self.opWrapper.emplaceAndPop([datum])
#         if datum.poseKeypoints is None: return None
#         kpts = datum.poseKeypoints[0]   # first person
#         return to_17_kpts(kpts, self._map_body25_to_coco17)

BACKENDS = {"mediapipe": MediaPipeRunner(),
            "movenet":   MoveNetRunner(),
            # "openpose":  OpenPoseRunner()
            }

# ---------- 3.  SIMPLE METRIC:  PCK @ 0.05  ----------------------------- #

def pck(gt, pred, thr=0.05):
    if gt is None or pred is None: return np.nan
    h, w = 1.0, 1.0  # assuming coords already normalised 0-1
    norm = np.sqrt(h**2 + w**2)
    dist = np.linalg.norm(gt[:,:2] - pred[:,:2], axis=1) / norm
    return np.nanmean((dist < thr).astype(float))

# ---------- 4.  BENCHMARK LOOP  ----------------------------------------- #

def run_benchmark(videos_dir, gt_json):
    gt_data = json.loads(Path(gt_json).read_text())  # {video: {frame:17x3}}
    results = defaultdict(list)

    for vid in Path(videos_dir).glob("*.mp4"):
        cap = cv2.VideoCapture(str(vid))
        frame_idx = 0
        while True:
            ok, frame = cap.read();  frame_idx += 1
            if not ok: break
            for name, runner in BACKENDS.items():
                t0 = time.time()
                kp = runner.infer(frame)
                dt = time.time() - t0
                acc = pck(np.asarray(gt_data[vid.name][str(frame_idx)]),
                          kp)
                results[name].append({"fps": 1/dt, "pck": acc})
        cap.release()

    # Aggregate
    for name, rows in results.items():
        fps = np.mean([r["fps"] for r in rows])
        pck_avg = np.nanmean([r["pck"] for r in rows])
        print(f"{name:10s}  FPS: {fps:5.1f}   PCK@0.05: {pck_avg:0.3f}")

# ---------- 5.  CLI ----------------------------------------------------- #

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True)
    ap.add_argument("--gt", required=True, help="Ground-truth landmarks JSON")
    args = ap.parse_args()
    run_benchmark(args.videos, args.gt)
