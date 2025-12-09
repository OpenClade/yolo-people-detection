import cv2
import json
import numpy as np
import os


class ZoneManager:
    def __init__(self, json_path="data/restricted_zones.json"):
        self.json_path = json_path

        self.zones = []
        self.current_points = []

        self.load_zones()
        self.edit_enabled = False
        self.redraw_callback = None

    def load_zones(self):
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
                self.zones = data["zones"]
                print(f"Loaded {len(self.zones)} zones.")
        except:
            print("No zones found. Starting fresh.")

    def save_zones(self):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        data = {"zones": self.zones}
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved zones → {self.json_path}")

    def mouse_callback(self, event, x, y, flags, param):
        if not self.edit_enabled:
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_points.append((x, y))
            if self.redraw_callback:
                self.redraw_callback()

        if event == cv2.EVENT_RBUTTONDOWN:
            if self.current_points:
                self.current_points.pop()
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
            print("Zone added.")
        else:
            print("Need at least 3 points.")
        self.current_points = []
