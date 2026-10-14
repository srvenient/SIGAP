import os

from loguru import logger
from ultralytics import YOLO

from inference.detection import Detection
from inference.plate_reader import PlateReader

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def save_detected_image(frame, output_dir):
    """
    Saves the detected image with bounding boxes drawn on it.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, "detected_image.jpg")
    cv2.imwrite(output_path, frame)
    logger.info(f"Detected image saved to {output_path}")


model_path = os.path.join(BASE_DIR, "models", "YOLO", "SIGAP_model_small_v1.pt")

model = YOLO(model_path)
detection = Detection(model)
plate_reader = PlateReader(use_gpu=True)  # Set to True to use GPU if available

if __name__ == "__main__":
    import cv2

    # Test the detection with a sample image
    image_path = os.path.join(BASE_DIR, "examples", "images", "3.jpeg")
    image = cv2.imread(image_path)

    if image is not None:
        frame = image.copy()
        frame = detection.detect(frame)
        result = plate_reader.read_text(frame)

        if result:
            print(f"Sanitized Plate: {result.license_plate}, Vehicle Type: {result.vehicle_type}")

        save_detected_image(frame, "output")
    else:
        print(f"Failed to load image from {image_path}")
