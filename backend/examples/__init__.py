import os
import time
import cv2
import re
import easyocr
from collections import Counter
from loguru import logger
from ultralytics import YOLO

# --- DICCIONARIOS DE CORRECCIÓN ---
NUMERO_A_LETRA = {'0': 'O', '1': 'I', '2': 'Z', '4': 'A', '5': 'S', '6': 'G', '8': 'B'}
LETRA_A_NUMERO = {'O': '0', 'I': '1', 'Z': '2', 'A': '4', 'S': '5', 'G': '6', 'B': '8', 'Q': '0'}


def corregir_y_clasificar_placa(texto_ocr):
    """
    Solución a corto plazo: Corrige posiciones 0-4 y deja que el OCR decida la posición 5.
    El tipo de vehículo se define basado en la lectura cruda de la última posición.
    """
    placa = re.sub(r'[^A-Z0-9]', '', texto_ocr.upper())

    if len(placa) != 6:
        return placa, "Descartada (Longitud inválida)"

    placa_corregida = list(placa)

    # Forzar Letras (Índices 0, 1, 2)
    for i in range(3):
        if placa_corregida[i] in NUMERO_A_LETRA:
            placa_corregida[i] = NUMERO_A_LETRA[placa_corregida[i]]

    # Forzar Números (Índices 3, 4)
    for i in range(3, 5):
        if placa_corregida[i] in LETRA_A_NUMERO:
            placa_corregida[i] = LETRA_A_NUMERO[placa_corregida[i]]

    # El Índice 5 NO se fuerza. Se confía en la estadística del buffer.
    placa_final = "".join(placa_corregida)

    # Clasificar según lo que leyó el OCR en la última posición
    if placa_final[5].isalpha():
        tipo_vehiculo = "Moto"
    elif placa_final[5].isdigit():
        tipo_vehiculo = "Carro"
    else:
        tipo_vehiculo = "Desconocido"

    return placa_final, tipo_vehiculo


# --- CREACIÓN DE DIRECTORIO DE DEBUG ---
CARPETA_ERRORES = "errores_ocr"
if not os.path.exists(CARPETA_ERRORES):
    os.makedirs(CARPETA_ERRORES)
    logger.info(f"Carpeta creada para guardar errores: {CARPETA_ERRORES}/")

# --- INICIALIZACIÓN DE MODELOS Y VARIABLES ---
logger.info("Cargando modelo YOLO...")
modelo = YOLO("../models/YOLO/SIGAP_model_small_v1.pt")

logger.info("Cargando modelo EasyOCR...")
reader = easyocr.Reader(['es', 'en'], gpu=True)

buffer_placas = []
FRAMES_A_ANALIZAR = 15
VOTOS_MINIMOS = 8

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    logger.error("No se pudo abrir la cámara.")
    exit()

logger.info("Sistema listo. Presiona 'q' para salir.")

# --- BUCLE PRINCIPAL ---
terminar_programa = False
placa_final_detectada = ""

# Preparamos el ecualizador CLAHE para mejorar contraste sin quemar la imagen
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

while True:
    ret, frame = cap.read()
    if not ret:
        logger.error("No se pudo leer el frame.")
        break

    resultados = modelo(frame, stream=True, verbose=False)

    for resultado in resultados:
        for caja in resultado.boxes:
            confianza = float(caja.conf[0])

            if confianza > 0.50:
                x1, y1, x2, y2 = map(int, caja.xyxy[0])

                h = y2 - y1
                w = x2 - x1

                # Recorte Inteligente de Márgenes
                x1_crop = x1 + int(w * 0.05)
                x2_crop = x2 - int(w * 0.05)
                y1_crop = y1
                y2_crop = y2 - int(h * 0.20)

                if y1_crop < y2_crop and x1_crop < x2_crop:
                    recorte_placa = frame[y1_crop:y2_crop, x1_crop:x2_crop]

                    if recorte_placa.size > 0:
                        # 1. Ampliación (Upscaling 2x) para definir mejor los bordes
                        recorte_ampliado = cv2.resize(recorte_placa, None, fx=2.0, fy=2.0,
                                                      interpolation=cv2.INTER_CUBIC)

                        # 2. Convertir a escala de grises
                        gris = cv2.cvtColor(recorte_ampliado, cv2.COLOR_BGR2GRAY)

                        # 3. Suavizado Gaussiano (vital para limpiar el ruido antes de Otsu)
                        gris_suavizado = cv2.GaussianBlur(gris, (5, 5), 0)

                        # 4. Thresholding de Otsu (Binarización Blanco y Negro puro)
                        # El '0' inicial es un valor de relleno porque Otsu calcula el umbral real automáticamente
                        _, binarizada = cv2.threshold(gris_suavizado, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                        detecciones = reader.readtext(
                            binarizada,
                            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                        )

                        texto_detectado = ""
                        if detecciones:
                            deteccion_principal = max(detecciones, key=lambda d: d[0][2][1] - d[0][0][1])
                            texto_detectado = deteccion_principal[1]

                        if texto_detectado:
                            placa_final, tipo_vehiculo = corregir_y_clasificar_placa(texto_detectado)

                            if "Descartada" not in tipo_vehiculo:
                                buffer_placas.append(placa_final)

                                etiqueta = f"Analizando: {len(buffer_placas)}/{FRAMES_A_ANALIZAR}"
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                                cv2.putText(frame, etiqueta, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

                                if len(buffer_placas) >= FRAMES_A_ANALIZAR:
                                    conteo = Counter(buffer_placas)
                                    placa_ganadora, votos = conteo.most_common(1)[0]

                                    if votos >= VOTOS_MINIMOS:
                                        # Recalculamos el tipo basado en la placa estadísticamente ganadora
                                        tipo_ganador = "Moto" if placa_ganadora[5].isalpha() else "Carro"

                                        logger.success(
                                            f"¡PLACA CONFIRMADA! -> {placa_ganadora} ({votos} votos) | Tipo: {tipo_ganador}")

                                        placa_final_detectada = f"{placa_ganadora} - {tipo_ganador}"
                                        terminar_programa = True
                                        break
                                    else:
                                        # GUARDADO DE IMAGEN EN CASO DE LECTURA INESTABLE
                                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                                        nombre_archivo = f"{CARPETA_ERRORES}/falla_{placa_ganadora}_{votos}votos_{timestamp}.jpg"
                                        cv2.imwrite(nombre_archivo, recorte_placa)

                                        logger.warning(
                                            f"Lectura inestable ({votos} votos). Recorte guardado en: {nombre_archivo}")

                                    buffer_placas.clear()

        if terminar_programa:
            break

    if not terminar_programa:
        cv2.imshow("SIGAP - ALPR en Vivo", frame)

    if terminar_programa or (cv2.waitKey(1) & 0xFF == ord('q')):
        break

cap.release()
cv2.destroyAllWindows()

if placa_final_detectada:
    logger.info("=" * 40)
    logger.info(f"PROCESO FINALIZADO. PLACA DETECTADA: {placa_final_detectada}")
    logger.info("=" * 40)