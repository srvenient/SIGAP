from loguru import logger
from ultralytics import YOLO
import torch

from src.processing.preprocess_crop import process_crop

class Detection:
    def __init__(self, model: YOLO) -> None:
        self.model = model
        self.use_half = torch.cuda.is_available()

    def detect(self, frame):
        q_mode = 'fp16' if self.use_half else 'fp32'
        results = self.model.predict(
            frame,
            device=0 if self.use_half else 'cpu',
            quantize=q_mode,
            verbose=False
        )
        result = results[0]

        boxes = [box for box in result.boxes if float(box.conf[0]) > 0.20]

        if not boxes:
            # logger.warning("No boxes detected with confidence > 0.20.")
            return None, None # <-- Ahora devolvemos una tupla

        boxes.sort(key=lambda box: box.conf[0], reverse=True)
        best_box = boxes[0]

        x1, y1, x2, y2 = map(int, best_box.xyxy[0])
        bbox_w, bbox_h = x2 - x1, y2 - y1

        x1c, x2c = max(0, x1 + int(bbox_w * 0.02)), min(frame.shape[1], x2 - int(bbox_w * 0.02))
        y1c, y2c = max(0, y1 + int(bbox_h * 0.02)), min(frame.shape[0], y2 - int(bbox_h * 0.02))

        if not (y1c < y2c and x1c < x2c):
            # logger.warning("Invalid crop coordinates after adjustment.")
            return None, None  # <-- Ahora devolvemos una tupla

        plate_crop = frame[y1c:y2c, x1c:x2c]
        processed_plate = process_crop(plate_crop)

        return processed_plate, (x1, y1, x2, y2)