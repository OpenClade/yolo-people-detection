import cv2


class VideoService:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        self.paused = False
        self.current_frame = None
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

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

    def seek_frame(self, offset):
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        new_pos = max(0, min(current_pos + offset, self.total_frames - 1))

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame.copy()
        return self.current_frame

    def get_frame_info(self):
        current_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return current_pos, self.total_frames

    def release(self):
        self.cap.release()
