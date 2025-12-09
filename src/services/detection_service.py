import cv2


class DetectionService:
    def __init__(self, model):
        self.model = model

    def detect_persons(self, frame):
        results = self.model.track(frame, verbose=False, persist=True)
        person_boxes = []

        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for box in boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    track_id = int(box.id[0]) if box.id is not None else None
                    person_boxes.append((x1, y1, x2, y2, track_id))

        return person_boxes

    def draw_detections(self, frame, person_boxes, intruders):
        for box in person_boxes:
            x1, y1, x2, y2, track_id = box

            is_intruder = track_id in intruders
            color = (0, 0, 255) if is_intruder else (255, 0, 0)
            thickness = 3 if is_intruder else 2

            cv2.rectangle(frame, (int(x1), int(y1)),
                         (int(x2), int(y2)), color, thickness)

            label = f"INTRUDER ID:{track_id}" if is_intruder else (
                f"Person ID:{track_id}" if track_id is not None else "Person")
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return frame
