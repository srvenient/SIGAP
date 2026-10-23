import cv2
import numpy as np


def correct_skew(image):
    """
    Calcula el ángulo de inclinación del contenido en la imagen y lo endereza
    solo si se encuentra dentro de un rango físico razonable (-15 a 15 grados).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))

    if len(coords) < 50:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Protección: Si el ángulo calculado supera los 15°, suele ser ruido del marco de la placa
    if abs(angle) > 15 or abs(angle) < 0.5:
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def process_crop(yolo_crop):
    """
    Reescala recortes pequeños, endereza la perspectiva, convierte a grises y aplica CLAHE.
    """
    h, w = yolo_crop.shape[:2]

    # Si la placa está lejos (altura menor a 65px), duplicamos su tamaño para ayudar a EasyOCR
    if h < 65:
        scale = 65.0 / max(1, h)
        yolo_crop = cv2.resize(yolo_crop, None, fx=scale, fy=scale, interpolation=cv2.interp_cubic if hasattr(cv2, 'interp_cubic') else cv2.INTER_CUBIC)

    aligned_img = correct_skew(yolo_crop)
    gray_img = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_img = clahe.apply(gray_img)

    return enhanced_img