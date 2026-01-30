# In this project:
# When a smile is detected, blink the eyes and mouth.
# Requires python 3.14
import cv2
import mediapipe as mp
import time

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
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=False
)

landmarker = FaceLandmarker.create_from_options(options)


# -------------------- Main loop --------------------
last_state = None
counter = 0
duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
duelink.Engine.ExecuteCommand(f"statled(0,1,0)")         
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

    if result.face_blendshapes:
        blendshapes = result.face_blendshapes[0]

        smile_left = 0.0
        smile_right = 0.0

        for shape in blendshapes:
            if shape.category_name == "mouthSmileLeft":
                smile_left = shape.score
            elif shape.category_name == "mouthSmileRight":
                smile_right = shape.score

        smile_score = (smile_left + smile_right) / 2.0

        # Threshold for real smile (tune if needed)
        is_smile = smile_score > 0.35

        state = "smile" if is_smile else "not smile"

        if state != last_state:
            print(state)
            last_state = state

    cv2.imshow("SmileDetector", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    counter = counter + 1
    if last_state == "smile":
        if (counter % 2 == 0):
            duelink.Engine.ExecuteCommand(f"LEye(255,255,255)")
            duelink.Engine.ExecuteCommand(f"REye(255,255,255)")
            duelink.Engine.ExecuteCommand(f"statled(1,0,0)")
        else:
            duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
            duelink.Engine.ExecuteCommand(f"REye(0,0,0)")            
    else:
        duelink.Engine.ExecuteCommand(f"LEye(0,0,0)")
        duelink.Engine.ExecuteCommand(f"REye(0,0,0)")
        duelink.Engine.ExecuteCommand(f"statled(0,1,0)")


cap.release()
cv2.destroyAllWindows()
