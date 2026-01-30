# In this project:
# Detect mouth open/close.
# When the mouth is open, Ghizzy Jr.'s eyes and mouth are on.
# When the mouth is closed, they are off.
# Requires Python 3.14.

import cv2
import mediapipe as mp
import time
import math

from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions
from DUELink.DUELinkController import DUELinkController

availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)


# -------------------- Camera setup --------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# -------------------- MediaPipe Face Landmarker --------------------
options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="face_landmarker.task"
    ),
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False
)

landmarker = FaceLandmarker.create_from_options(options)


# -------------------- Helper function --------------------
def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


# -------------------- Main loop --------------------
last_state = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_rgb
    )

    timestamp_ms = int(time.time() * 1000)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    if result.face_landmarks:
        face = result.face_landmarks[0]

        # ---- Mouth landmarks (MediaPipe standard indices) ----
        upper_lip = face[13]
        lower_lip = face[14]

        left_mouth = face[61]
        right_mouth = face[291]

        mouth_open = distance(upper_lip, lower_lip)
        mouth_width = distance(left_mouth, right_mouth)

        # Normalize to face size (important!)
        ratio = mouth_open / mouth_width if mouth_width > 0 else 0

        # Threshold for open mouth (tune if needed)
        is_open = ratio > 0.25

        state = "mouth open" if is_open else "mouth closed"

        if state != last_state:
            print(state)
            last_state = state

    cv2.imshow("MouthDetector", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()
