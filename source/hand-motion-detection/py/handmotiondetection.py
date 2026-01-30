# In this project:
# Ghizzy's eyes will blink when hand movement is detected.
# Requires Python 3.14.
import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions

from DUELink.DUELinkController import DUELinkController

availablePort = DUELinkController.GetConnectionPort()
duelink = DUELinkController(availablePort)

# Drawing colors
draw_color = (255, 255, 255)
erase_color = (0, 0, 0)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
canvas = np.zeros((480, 640, 3), dtype=np.uint8)
prev_x, prev_y = 0, 0

def scale(value, in_min=0, in_max=640, out_min=0, out_max=255):
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def draw_line(canvas, start, end, color, thickness=2):
    cv2.line(canvas, start, end, color, thickness)


def erase_area(canvas, center, radius, color):
    cv2.circle(canvas, center, radius, color, -1)

# --- MediaPipe Tasks setup ---
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    num_hands=1
)

landmarker = HandLandmarker.create_from_options(options)

MOVE_THRESHOLD = 8  # pixels
duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
index_tip_x_prev = None
count = 0
while True:
    count = count+1
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_rgb
    )

    result = landmarker.detect(mp_image)

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        handedness = result.handedness[0][0].category_name

        # Index finger tip (landmark 8)
        index_tip_x = int(hand[8].x * frame.shape[1])
        index_tip_y = int(hand[8].y * frame.shape[0])

        if index_tip_x_prev is not None:
            dx = index_tip_x - index_tip_x_prev
            index_tip_x_scale = 255

            if dx > MOVE_THRESHOLD or dx < -MOVE_THRESHOLD:
      
                if count % 2 == 0:
                    duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
                    duelink.Engine.ExecuteCommand(f"LEye({index_tip_x_scale},{index_tip_x_scale},{index_tip_x_scale})")
                else:
                    duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
                    duelink.Engine.ExecuteCommand(f"REye({index_tip_x_scale},{index_tip_x_scale},{index_tip_x_scale})")


        index_tip_x_prev = index_tip_x

        # Wrist (landmark 0)
        palm_x = int(hand[0].x * frame.shape[1])
        palm_y = int(hand[0].y * frame.shape[0])

        if handedness == "Left" and hand[0].x < 0.5:
            erase_area(canvas, (palm_x, palm_y), 140, [100, 0, 100])
            prev_x, prev_y = 0, 0
        else:
            if prev_x != 0 and prev_y != 0:
                draw_line(
                    canvas,
                    (prev_x, prev_y),
                    (index_tip_x, index_tip_y),
                    draw_color
                )
            prev_x, prev_y = index_tip_x, index_tip_y
    else:
        duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
        duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")

    cv2.imshow("Frame", frame)
    cv2.imshow("Canvas", canvas)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
