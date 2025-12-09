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
        self.current_intruders = set()

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
        if len(self.current_points) > 0:
            pts = np.array(self.current_points, dtype=np.int32)
            cv2.polylines(frame, [pts], False, (0, 255, 0), 2)
            for p in self.current_points:
                cv2.circle(frame, p, 5, (0, 255, 0), -1)

    def finish_polygon(self):
        if len(self.current_points) >= 3:
            self.zones.append({"points": self.current_points.copy()})
            print(
                f"✅ Zone #{len(self.zones)} added with {len(self.current_points)} points")
            self.current_points = []
        elif len(self.current_points) > 0:
            print(
                f"⚠️  Need at least 3 points (current: {len(self.current_points)})")
            self.current_points = []
        else:
            print("⚠️  No points to finish")

    def check_intrusion(self, bounding_boxes):
        intrusion_detected = False

        for box in bounding_boxes:
            x1, y1, x2, y2 = box

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            bottom_center_x = center_x
            bottom_center_y = int(y2)

            for zone in self.zones:
                pts = np.array(zone["points"], dtype=np.int32)

                if (cv2.pointPolygonTest(pts, (center_x, center_y), False) >= 0 or
                        cv2.pointPolygonTest(pts, (bottom_center_x, bottom_center_y), False) >= 0):
                    intrusion_detected = True
                    break

            if intrusion_detected:
                break

        return intrusion_detected

    def update_alarm(self, intrusion_detected, person_boxes_with_ids):
        current_time = time.time()
        active_intruders = set()

        if intrusion_detected and len(person_boxes_with_ids) > 0:
            for box in person_boxes_with_ids:
                x1, y1, x2, y2, track_id = box
                if track_id is None:
                    continue

                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                bottom_center_x = center_x
                bottom_center_y = int(y2)

                for zone in self.zones:
                    pts = np.array(zone["points"], dtype=np.int32)
                    if (cv2.pointPolygonTest(pts, (center_x, center_y), False) >= 0 or
                            cv2.pointPolygonTest(pts, (bottom_center_x, bottom_center_y), False) >= 0):
                        active_intruders.add(track_id)
                        if track_id not in self.intruders:
                            print(
                                f"🚨 ALARM! Person ID:{track_id} entered restricted zone!")
                        self.intruders[track_id] = current_time
                        break

            self.last_intrusion_time = current_time
            if not self.alarm_active:
                self.alarm_active = True

        expired_intruders = []
        for track_id, last_seen in list(self.intruders.items()):
            if current_time - last_seen >= self.alarm_delay:
                expired_intruders.append(track_id)
                print(f"✅ Person ID:{track_id} cleared (3 seconds passed)")

        for track_id in expired_intruders:
            del self.intruders[track_id]

        if not self.intruders and self.alarm_active:
            self.alarm_active = False
            print("✅ All clear - Alarm deactivated")

        return active_intruders
