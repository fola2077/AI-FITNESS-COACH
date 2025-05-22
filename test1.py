import cv2
import time
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(model_complexity=0)   # 0 = lightning-fast, 2 = highest accuracy
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)                 # 0 → default webcam
prev = time.time()

while cap.isOpened():
    ok, frame = cap.read()
    if not ok:
        break

    # Convert to RGB *once*; MediaPipe expects RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    # Draw landmarks
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(thickness=2, circle_radius=3)
        )

    # FPS counter
    curr = time.time()
    fps = 1 / (curr - prev)
    prev = curr
    cv2.putText(frame, f'FPS: {fps:0.1f}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('AI Fitness Coach – webcam test', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
