import cv2

class VideoReader:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {path}")

    def frames(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            # Encode to JPEG
            _, jpeg = cv2.imencode('.jpg', frame)
            yield jpeg.tobytes()
        self.cap.release()