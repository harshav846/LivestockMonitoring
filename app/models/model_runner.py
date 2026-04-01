import cv2
from ultralytics import YOLO
import os

# =========================
# CONFIG
# =========================
MODEL_PATH = "yolov8n.pt"
CONFIDENCE = 0.45
COW_CLASS_ID = 19

ENTRY_X1, ENTRY_Y1 = 400, 400
ENTRY_X2, ENTRY_Y2 = 800, 520

# =========================
# LOAD MODEL ONCE (IMPORTANT)
# =========================
model = YOLO(MODEL_PATH)


def run_model(input_path, output_path):

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return None, None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    entry_count = 0
    counted_entry_ids = set()
    total_ids = set()
    track_states = {}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            frame,
            tracker="bytetrack.yaml",
            persist=True,
            conf=CONFIDENCE,
            classes=[COW_CLASS_ID],
            imgsz=960,
            verbose=False
        )

        # Draw Entry Zone
        cv2.rectangle(frame, (ENTRY_X1, ENTRY_Y1),
                      (ENTRY_X2, ENTRY_Y2), (0, 0, 255), 2)
        cv2.putText(frame, "ENTRY ZONE",
                    (ENTRY_X1, ENTRY_Y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu()
            ids = results[0].boxes.id.cpu()

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                track_id = int(track_id)

                total_ids.add(track_id)

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                inside = ENTRY_X1 < cx < ENTRY_X2 and ENTRY_Y1 < cy < ENTRY_Y2

                if track_id not in track_states:
                    track_states[track_id] = inside

                if not track_states[track_id] and inside:
                    if track_id not in counted_entry_ids:
                        entry_count += 1
                        counted_entry_ids.add(track_id)

                track_states[track_id] = inside

                # Draw
                cv2.rectangle(frame, (x1, y1),
                              (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID {track_id}",
                            (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 0), 2)
                cv2.circle(frame, (cx, cy),
                           4, (0, 255, 255), -1)

        # Display counts
        cv2.putText(frame, f"Entry Count: {entry_count}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (0, 255, 255), 2)

        cv2.putText(frame, f"Total Cows: {len(total_ids)}",
                    (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 0), 2)

        out.write(frame)

    cap.release()
    out.release()

    return entry_count, len(total_ids)