import cv2
import json
import numpy as np
import os
import time


class ZoneManager:
    def __init__(self, json_path="data/restricted_zones.json"):
        self.json_path = json_path

        self.zones = []
        self.current_points = []

        self.load_zones()
        self.edit_enabled = False
        self.redraw_callback = None

        self.alarm_active = False
        self.last_intrusion_time = None
        self.alarm_delay = 3.0
        self.intruders = {}

    def load_zones(self):
        with open(self.json_path, "r") as f:
            data = json.load(f)
            self.zones = data["zones"]

    def save_zones(self):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)

        data = {"zones": self.zones}
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"💾 Zones saved to {self.json_path} ({len(self.zones)} zones)")

    def mouse_callback(self, event, x, y, flags, param):
        if not self.edit_enabled:
            if event == cv2.EVENT_LBUTTONDOWN:
                print("⚠️  Edit mode is OFF. Press 'E' to enable (video must be paused)")
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_points.append((x, y))
            print(
                f"✏️  Point added: ({x}, {y}) - Total points: {len(self.current_points)}")
            if self.redraw_callback:
                self.redraw_callback()

        if event == cv2.EVENT_RBUTTONDOWN:
            if self.current_points:
                self.current_points.pop()
                print(
                    f"↩️  Point removed - Total points: {len(self.current_points)}")
                if self.redraw_callback:
                    self.redraw_callback()

    def draw_zones(self, frame):
        for zone in self.zones:
            pts = np.array(zone["points"], dtype=np.int32)
            cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
        return frame

    def draw_current_polygon(self, frame):
        if not self.current_points:
            return

        pts = np.array(self.current_points, dtype=np.int32)
        cv2.polylines(frame, [pts], False, (0, 255, 0), 2)
        for p in self.current_points:
            cv2.circle(frame, p, 5, (0, 255, 0), -1)

    def finish_polygon(self):
        if not self.current_points:
            print("⚠️  No points to finish")
            return

        if len(self.current_points) < 3:
            print(
                f"⚠️  Need at least 3 points (current: {len(self.current_points)})")
            self.current_points = []
            return

        self.zones.append({"points": self.current_points.copy()})
        print(
            f"✅ Zone #{len(self.zones)} added with {len(self.current_points)} points")
        self.current_points = []

    def _is_point_in_any_zone(self, x: int, y: int) -> bool:
        point = (x, y)
        for zone in self.zones:
            pts = np.array(zone["points"], dtype=np.int32)
            if cv2.pointPolygonTest(pts, point, False) >= 0:
                return True
        return False

    def _is_box_in_zone(self, box) -> bool:
        x1, y1, x2, y2 = box[:4]
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        bottom_y = int(y2)
        return (self._is_point_in_any_zone(center_x, center_y) or
                self._is_point_in_any_zone(center_x, bottom_y))

    def check_intrusion(self, bounding_boxes):
        return any(self._is_box_in_zone(box) for box in bounding_boxes)

    def _find_active_intruders(self, person_boxes_with_ids, current_time):
        active = set()
        for box in person_boxes_with_ids:
            track_id = box[4]
            if track_id is None:
                continue

            if self._is_box_in_zone(box):
                active.add(track_id)
                if track_id not in self.intruders:
                    print(
                        f"🚨 ALARM! Person ID:{track_id} entered restricted zone!")
                self.intruders[track_id] = current_time
        return active

    def _cleanup_expired_intruders(self, current_time):
        expired = [tid for tid, last_seen in self.intruders.items()
                   if current_time - last_seen >= self.alarm_delay]
        for track_id in expired:
            del self.intruders[track_id]
            print(f"✅ Person ID:{track_id} cleared (3 seconds passed)")

    def update_alarm(self, intrusion_detected, person_boxes_with_ids):
        current_time = time.time()
        active_intruders = set()

        if intrusion_detected and person_boxes_with_ids:
            active_intruders = self._find_active_intruders(
                person_boxes_with_ids, current_time)
            self.last_intrusion_time = current_time
            if not self.alarm_active:
                self.alarm_active = True

        self._cleanup_expired_intruders(current_time)

        if not self.intruders and self.alarm_active:
            self.alarm_active = False
            print("✅ All clear - Alarm deactivated")

        return active_intruders
