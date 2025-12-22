import cv2
import numpy as np
from ultralytics import YOLO  # type:ignore

model = YOLO("yolov8n.pt")

# --- Initialization ---
cap = cv2.VideoCapture(0)

# Window & UI settings
DISPLAY_SIZE = (500, 500)
TEXT_POS = (150, 250)

# Detection control
frame_counter = 0
last_people_count = 0
last_boxes = []  # store boxes from last detection
SKIP_FRAME = 10

# --- Main Loop ---
while True:

    # Prepare display frame
    display_frame = np.zeros((*DISPLAY_SIZE, 3), dtype=np.uint8)

    # Read camera frame
    ret, camera_frame = cap.read()
    if not ret:
        break

    # Flip for natural movement
    camera_frame = cv2.flip(camera_frame, flipCode=1)

    # Increment counter
    frame_counter += 1

    # --- Run YOLO only every 'SKIP_FRAME'---
    if frame_counter % SKIP_FRAME == 0:
        results = model(camera_frame)
        people_count = 0
        current_boxes = []

        for r in results[0].boxes:
            cls = int(r.cls[0])
            if cls == 0:  # class 0 = person
                people_count += 1
                x1, y1, x2, y2 = r.xyxy[0].int().tolist()
                current_boxes.append((x1, y1, x2, y2))

        # Save results
        last_people_count = people_count
        last_boxes = current_boxes

    else:
        # --- Use last detection results ---
        people_count = last_people_count

        for (x1, y1, x2, y2) in last_boxes:
            cv2.rectangle(camera_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)


    # --- Draw person count text ---
    color = (20, 255, 20) if people_count > 0 else (255, 20, 20)

    cv2.putText(display_frame,
                f"People Count = {people_count}",
                TEXT_POS,
                cv2.FONT_HERSHEY_COMPLEX,
                0.7,
                color,
                2)

    # --- Footer Info ---
    cv2.putText(display_frame,
                "Person Detector",
                (10, DISPLAY_SIZE[1] - 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2)

    cv2.putText(display_frame,
                "By Omar Ahmed and Omar Ashraf - Embedded Systems",
                (10, DISPLAY_SIZE[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1)

    # --- Show Windows ---
    cv2.imshow("Camera Feed", camera_frame)
    cv2.imshow("Counter Display", display_frame)

    # Exit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
