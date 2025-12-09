import cv2
from services.video_service import VideoService
from services.detection_service import DetectionService
from managers.zone_manager import ZoneManager


class Application:
    def __init__(self, zones_path: str, model):
        self.zones_path = zones_path
        self.model = model

        self.video_service = None
        self.detection_service = DetectionService(model)
        self.zone_service = ZoneManager(json_path=zones_path)

        self.window_name = "Video Zone Editor"
        self.monitoring_enabled = True

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

            display_frame = frame.copy()

            if self.monitoring_enabled and not self.zone_service.edit_enabled:
                person_boxes = self.detection_service.detect_persons(frame)

                bbox_only = [(x1, y1, x2, y2) for x1, y1, x2, y2, _ in person_boxes]
                intrusion = self.zone_service.check_intrusion(bbox_only)
                self.zone_service.update_alarm(intrusion, person_boxes)

                display_frame = self.detection_service.draw_detections(
                    display_frame, person_boxes, self.zone_service.intruders)

            display_frame = self.zone_service.draw_zones(display_frame)

            if self.zone_service.edit_enabled:
                self.zone_service.draw_current_polygon(display_frame)

            self._add_status_text(display_frame)

            if self.zone_service.alarm_active:
                self._draw_alarm(display_frame)

            cv2.imshow(self.window_name, display_frame)

            key = cv2.waitKey(30) & 0xFF
            if not self._handle_key(key):
                break

        self.video_service.release()
        cv2.destroyAllWindows()

    def _handle_key(self, key: int) -> bool:
        if key == ord('q'):
            return False
        elif key == ord(' '):
            self.video_service.toggle_pause()
            print(
                f"{'⏸️  Paused' if self.video_service.is_paused() else '▶️  Playing'}")
        elif key == ord('e') or key == ord('E'):
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
        elif key == ord('m') or key == ord('M'):
            self.monitoring_enabled = not self.monitoring_enabled
            print(
                f"{'📹 Monitoring enabled' if self.monitoring_enabled else '⏸️  Monitoring disabled'}")
        elif key == ord('d') and self.video_service.is_paused():
            self._run_detection()
        elif key == 83 and self.video_service.is_paused():
            self._seek_frames(1)
        elif key == 81 and self.video_service.is_paused():
            self._seek_frames(-1)
        elif key == 84 and self.video_service.is_paused():
            self._seek_frames(-30)
        elif key == 82 and self.video_service.is_paused():
            self._seek_frames(30)
        elif key == 27:
            return False

        return True

    def _seek_frames(self, offset):
        self.video_service.seek_frame(offset)
        current, total = self.video_service.get_frame_info()
        print(f"⏩ Frame {current}/{total}")

    def _draw_alarm(self, frame):
        h, w = frame.shape[:2]

        text = "ALARM!"
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 3
        thickness = 8

        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (w - text_size[0]) // 2
        text_y = (h + text_size[1]) // 2

        cv2.rectangle(frame,
                     (text_x - 20, text_y - text_size[1] - 20),
                     (text_x + text_size[0] + 20, text_y + 20),
                     (0, 0, 0), -1)

        cv2.putText(frame, text, (text_x, text_y),
                   font, font_scale, (0, 0, 255), thickness)

        if hasattr(self.zone_service, 'intruders') and self.zone_service.intruders:
            intruder_text = "Intruders: " + \
                ", ".join([f"ID:{id}" for id in self.zone_service.intruders.keys()])
            intruder_font_scale = 1
            intruder_thickness = 2
            intruder_size = cv2.getTextSize(
                intruder_text, font, intruder_font_scale, intruder_thickness)[0]
            intruder_x = (w - intruder_size[0]) // 2
            intruder_y = text_y + 60

            cv2.rectangle(frame,
                         (intruder_x - 10, intruder_y - intruder_size[1] - 10),
                         (intruder_x + intruder_size[0] + 10, intruder_y + 10),
                         (0, 0, 0), -1)

            cv2.putText(frame, intruder_text, (intruder_x, intruder_y),
                       font, intruder_font_scale, (255, 255, 255), intruder_thickness)

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
        if self.monitoring_enabled:
            status.append("MONITORING ON")

        current, total = self.video_service.get_frame_info()
        status.append(f"Frame: {current}/{total}")

        if status:
            text = " | ".join(status)
            color = (0, 0, 255) if self.zone_service.alarm_active else (
                0, 255, 0)
            cv2.putText(frame, text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    def _redraw_frame(self):
        if self.video_service and self.video_service.current_frame is not None:
            display_frame = self.video_service.current_frame.copy()
            display_frame = self.zone_service.draw_zones(display_frame)

            if self.zone_service.edit_enabled:
                self.zone_service.draw_current_polygon(display_frame)

            self._add_status_text(display_frame)
            cv2.imshow(self.window_name, display_frame)
