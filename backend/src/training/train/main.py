import os

from loguru import logger
from ultralytics import YOLO

MODEL_NAME = "yolo26s"  # Model name
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory

PRETRAINED_MODEL = os.path.join(CURRENT_DIR, "../pretrained_models", f"{MODEL_NAME}.pt")
DATA_CONFIG_PATH = os.path.join(CURRENT_DIR, "../../../dataset/data.yaml")
LOCAL_RUNS_DIR = os.path.join(CURRENT_DIR, "../../../reports/runs/YOLO/yolo26s_detect")  # Local runs directory


def train_detection_model():
    logger.info(f"Starting training for model: {MODEL_NAME}")

    model = YOLO(PRETRAINED_MODEL)  # Load the pretrained model and move it to GPU
    model.train(
        data=DATA_CONFIG_PATH,
        project=LOCAL_RUNS_DIR,
        name=f"{MODEL_NAME}_detect",
        epochs=300,
        patience=25,
        imgsz=640,
        batch=16,
        amp=True,
        workers=8,
        cache=True,
        device=0,
        optimizer='auto',
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.0,
        fliplr=0.5
    )

    logger.info("Training completed successfully")


if __name__ == "__main__":
    train_detection_model()
