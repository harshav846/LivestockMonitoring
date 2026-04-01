import cv2
from ultralytics import YOLO
from io import BytesIO

# =========================
# CONFIGURATION
# =========================
MODEL_PATH = "ai_module/models/yolov8n.pt"  # Update relative path
CONFIDENCE = 0.45
COW_CLASS_ID = 19

ENTRY_X1, ENTRY_Y1 = 300, 300
ENTRY_X2, ENTRY_Y2 = 600, 450

# Load YOLO model once
model = YOLO(MODEL_PATH)


def run_frame_processing(video_path):
    """
    Generator function that processes video frames one by one
    and yields them as JPEG bytes for live streaming (MJPEG).
    Also counts cows entering entry zone.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    entry_count = 0
    counted_entry_ids = set()
    total_ids = set()
    track_states = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))

        results = model.track(
            frame,
            tracker="bytetrack.yaml",
            persist=True,
            conf=CONFIDENCE,
            classes=[COW_CLASS_ID],
            imgsz=640,
            verbose=False
        )

        # Draw entry zone
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

                if inside and track_id not in counted_entry_ids:
                    entry_count += 1
                    counted_entry_ids.add(track_id)
                
                track_states[track_id] = inside

                # Draw box and ID
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID {track_id}",
                            (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

        # Display counts on frame
        cv2.putText(frame, f"Entry Count: {entry_count}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        cv2.putText(frame, f"Total Cows: {len(total_ids)}",
                    (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield frame_bytes, entry_count, len(total_ids)

    cap.release()