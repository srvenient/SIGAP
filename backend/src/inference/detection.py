from loguru import logger
from ultralytics import YOLO

from processing.preprocess_crop import process_crop


class Detection:
    def __init__(self, model: YOLO) -> None:
        self.model = model

    def detect(self, frame):
        results = self.model.predict(
            frame,
            verbose=False
        )
        result = results[0]  # Get the first result

        boxes = [box for box in result.boxes if float(box.conf[0]) > 0.20]

        if not boxes:
            logger.warning("No boxes detected with confidence > 0.20.")
            return None

        boxes.sort(key=lambda box: box.conf[0], reverse=True)  # Sort by ID in descending order

        best_box = boxes[0]

        x1, y1, x2, y2 = map(int, best_box.xyxy[0])
        bbox_w, bbox_h = x2 - x1, y2 - y1

        x1c, x2c = max(0, x1 + int(bbox_w * 0.02)), min(frame.shape[1], x2 - int(bbox_w * 0.02))
        y1c, y2c = max(0, y1 + int(bbox_h * 0.02)), min(frame.shape[0], y2 - int(bbox_h * 0.02))

        # Ensure the cropped coordinates are valid
        if not (y1c < y2c and x1c < x2c):
            logger.warning("Invalid crop coordinates after adjustment.")
            return None

        # Crop the detected plate from the frame
        plate_crop = frame[y1c:y2c, x1c:x2c]
        # Process the cropped plate image
        processed_plate = process_crop(plate_crop)

        return processed_plate
