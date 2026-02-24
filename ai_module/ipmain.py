import cv2
from ultralytics import YOLO

# =========================
# CONFIGURATION
# =========================
#VIDEO_PATH = 0  # Use 0 for webcam OR mobile IP link
VIDEO_PATH = "http://192.168.0.206:8080/video"

MODEL_PATH = "yolov8n.pt"

CONFIDENCE = 0.45
PERSON_CLASS_ID = 0  # Person class in COCO

ENTRY_X1, ENTRY_Y1 = 400, 400
ENTRY_X2, ENTRY_Y2 = 800, 520

# =========================
# LOAD MODEL
# =========================
model = YOLO(MODEL_PATH)

# =========================
# VIDEO
# =========================
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

# =========================
# COUNTING STATE
# =========================
entry_count = 0
counted_entry_ids = set()

total_ids = set()
track_states = {}

# =========================
# MAIN LOOP
# =========================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (960, 720))

    results = model.track(
        frame,
        tracker="bytetrack.yaml",
        persist=True,
        conf=CONFIDENCE,
        classes=[PERSON_CLASS_ID],
        imgsz=960,
        verbose=False
    )

    # ENTRY ZONE
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

            # TOTAL UNIQUE HUMANS
            total_ids.add(track_id)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            inside = ENTRY_X1 < cx < ENTRY_X2 and ENTRY_Y1 < cy < ENTRY_Y2

            if track_id not in track_states:
                track_states[track_id] = inside

            # ENTRY COUNT (outside → inside)
            if not track_states[track_id] and inside:
                if track_id not in counted_entry_ids:
                    entry_count += 1
                    counted_entry_ids.add(track_id)

            track_states[track_id] = inside

            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {track_id}",
                        (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

    # DISPLAY COUNTS
    cv2.putText(frame, f"Entry Count (Simulated Cows): {entry_count}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

    cv2.putText(frame, f"Total Detected: {len(total_ids)}",
                (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

    cv2.imshow("Livestock Monitoring - Human Simulation", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
