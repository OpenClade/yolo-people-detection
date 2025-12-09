import cv2


class VideoService:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        self.paused = False
        self.current_frame = None

    def read_frame(self):
        if not self.paused:
            ret, frame = self.cap.read()
            if not ret:
                return None
            self.current_frame = frame.copy()
        return self.current_frame

    def toggle_pause(self):
        self.paused = not self.paused

    def is_paused(self):
        return self.paused

    def release(self):
        self.cap.release()
