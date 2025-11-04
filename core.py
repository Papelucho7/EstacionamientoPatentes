
import cv2
from ultralytics import YOLO
import easyocr
import re
import collections
import numpy as np
from db_config import get_connection

# --- Cargar modelo YOLO entrenado y OCR ---
model = YOLO('model/best.pt')
ocr = easyocr.Reader(['es'], gpu=False)

# --- Funciones de Ayuda ---

def levenshtein_distance(s1, s2):
    """Calcula la distancia de Levenshtein entre dos strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def son_patentes_similares(p1, p2, umbral=1):
    """Verifica si dos patentes son similares según el umbral de Levenshtein."""
    return levenshtein_distance(p1, p2) <= umbral

def es_patente_valida(texto):
    """Verifica si el texto coincide con los formatos de patente chilena."""
    if not texto or len(texto) < 6 or len(texto) > 7:
        return False
    patron1 = re.compile(r'^[A-Z]{4}[0-9]{2}$') # Formato más nuevo: BBBB11
    patron2 = re.compile(r'^[A-Z]{2}[0-9]{4}$') # Formato antiguo: BB1111
    return bool(patron1.match(texto) or patron2.match(texto))

def preprocesar_para_ocr(imagen_recortada):
    """Aplica técnicas para mejorar la legibilidad de la imagen antes de pasarla al OCR."""
    gray = cv2.cvtColor(imagen_recortada, cv2.COLOR_BGR2GRAY)
    
    # Agrandar la imagen (Interpolación) - Ayuda mucho al OCR
    h, w = gray.shape
    scale_factor = 3
    gray_resized = cv2.resize(gray, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_CUBIC)

    # Aplicar un filtro de enfoque (Sharpening) para realzar los bordes
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray_resized, -1, kernel)

    # Convertir a blanco y negro puro (Binarización con método de Otsu)
    _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh

def guardar_en_sql(patente):
    """Guarda la patente confirmada en la base de datos."""
    try:
        conn = get_connection()
        if not conn:
            print("Error: No se pudo establecer conexión con la base de datos.")
            return
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RegistrosPatentes (Patente, FechaRegistro)
            VALUES (?, GETDATE())
        """, (patente,))
        conn.commit()
        conn.close()
        print(f"✅ Base de Datos: Patente ''{patente}'' guardada.")
    except Exception as e:
        print(f"❌ Error al guardar en SQL Server: {e}")
