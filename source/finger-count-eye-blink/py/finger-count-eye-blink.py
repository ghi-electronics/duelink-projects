# In this project:
# Detect how many fingers are shown and blink the eyes that many times.
# Requires Python 3.14.
import cv2
import mediapipe as mp
import time

from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions
from DUELink.DUELinkController import DUELinkController

availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)


# -------------------- Camera setup --------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# -------------------- MediaPipe Tasks setup --------------------
options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="hand_landmarker.task"
    ),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)


# -------------------- Finger counting function --------------------
def count_fingers(hand, handedness):
    fingers = 0

    # ---- Thumb ----
    if handedness == "Right":
        if hand[4].x > hand[3].x:
            fingers += 1
    else:  # Left hand
        if hand[4].x < hand[3].x:
            fingers += 1

    # ---- Other four fingers ----
    if hand[8].y < hand[6].y:    # Index
        fingers += 1
    if hand[12].y < hand[10].y:  # Middle
        fingers += 1
    if hand[16].y < hand[14].y:  # Ring
        fingers += 1
    if hand[20].y < hand[18].y:  # Pinky
        fingers += 1

    return fingers


# -------------------- Main loop --------------------
last_count = None
duelink.Engine.ExecuteCommand(f"REye(255,255,255)")
duelink.Engine.ExecuteCommand(f"LEye(255,255,255)")
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

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        handedness = result.handedness[0][0].category_name

        finger_count = count_fingers(hand, handedness)

        # Print only when the count changes
        if finger_count != last_count:
            print(finger_count)
            if (finger_count == 0):
                duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
                duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
                
            for i in range (finger_count*2):
                if (i % 2) == 1:
                    duelink.Engine.ExecuteCommand(f"REye(255,255,255)")
                    duelink.Engine.ExecuteCommand(f"LEye(255,255,255)")
                else:
                    duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
                    duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
                time.sleep(0.05)     



            last_count = finger_count
    else:
        last_count = None

    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()
