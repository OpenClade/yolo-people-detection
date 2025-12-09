import cv2
from services.video_service import VideoService
from managers.zone_manager import ZoneManager


class Application:
    def __init__(self, zones_path: str, model):
        self.zones_path = zones_path
        self.model = model

        self.video_service = None
        self.zone_service = ZoneManager(json_path=zones_path)

        self.window_name = "Video Zone Editor"

    def run(self, video_path: str):
        self.video_service = VideoService(video_path)

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(
            self.window_name, self.zone_service.mouse_callback)
        self.zone_service.redraw_callback = self._redraw_frame

        while True:
            frame = self.video_service.read_frame()
            if frame is None:
                print("End of video or cannot read frame.")
                break

            display_frame = self.zone_service.draw_zones(frame.copy())

            if self.zone_service.edit_enabled:
                self.zone_service.draw_current_polygon(display_frame)

            self._add_status_text(display_frame)

            cv2.imshow(self.window_name, display_frame)

            key = cv2.waitKey(30) & 0xFF
            if not self._handle_key(key):
                break

    def _handle_key(self, key: int) -> bool:
        if key == ord('q'):
            return False
        elif key == ord(' '):
            self.video_service.toggle_pause()
            print(
                f"{'⏸️  Paused' if self.video_service.is_paused() else '▶️  Playing'}")
        elif key == ord('e'):
            if self.video_service.is_paused():
                self.zone_service.edit_enabled = not self.zone_service.edit_enabled
                print(
                    f"Edit mode: {'ON ✏️' if self.zone_service.edit_enabled else 'OFF'}")
            else:
                print("⚠️  Pause the video first (SPACE)")
        elif key == ord('f'):
            self.zone_service.finish_polygon()
        elif key == ord('s'):
            self.zone_service.save_zones()
        elif key == ord('c'):
            self.zone_service.zones.clear()
            print("🗑️  All zones cleared")
        elif key == ord('d') and self.video_service.is_paused():
            self._run_detection()

        return True

    def _run_detection(self):
        if self.video_service.current_frame is None:
            print("⚠️  No frame available")
            return

        print("🔍 Running detection...")
        results = self.model(self.video_service.current_frame)

        annotated = results[0].plot()
        cv2.imshow("Detection Results", annotated)
        print(f"✅ Detected {len(results[0].boxes)} objects")

    def _add_status_text(self, frame):
        status = []
        if self.video_service.is_paused():
            status.append("PAUSED")
        if self.zone_service.edit_enabled:
            status.append("EDIT MODE")

        if status:
            text = " | ".join(status)
            cv2.putText(frame, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def _redraw_frame(self):
        if self.video_service and self.video_service.current_frame is not None:
            display_frame = self.video_service.current_frame.copy()
            display_frame = self.zone_service.draw_zones(display_frame)

            if self.zone_service.edit_enabled:
                self.zone_service.draw_current_polygon(display_frame)

            self._add_status_text(display_frame)
            cv2.imshow(self.window_name, display_frame)
