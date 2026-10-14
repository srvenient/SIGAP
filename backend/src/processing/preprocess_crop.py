import cv2
import numpy as np


def correct_skew(image):
    """
    Calcula el ángulo de inclinación del contenido en la imagen y lo endereza.
    """
    # Convertir a escala de grises temporalmente para encontrar bordes
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Invertir colores y aplicar thresholding (binarización)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Obtener todas las coordenadas de los píxeles que forman el objeto/texto
    coords = np.column_stack(np.where(thresh > 0))

    # Si no hay suficientes píxeles, devolver la imagen original
    if len(coords) == 0:
        return image

    # Calcular el rectángulo delimitador mínimo que envuelve los puntos y su ángulo
    angle = cv2.minAreaRect(coords)[-1]

    # Ajustar el ángulo para las diferentes versiones de OpenCV
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotar la imagen
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Aplicar la rotación
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated


def process_crop(yolo_crop):
    """
    Función principal: Endereza, pasa a grises y mejora el contraste.
    :param yolo_crop: Imagen recortada en formato array de NumPy (OpenCV).
    """
    # 1. Enderezar la perspectiva (Rotación)
    aligned_img = correct_skew(yolo_crop)

    # 2. Pasar a escala de grises
    gray_img = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)

    # 3. Mejorar el contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # CLAHE es mucho mejor que la ecualización estándar porque lo hace por regiones (tiles)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_img = clahe.apply(gray_img)

    return enhanced_img