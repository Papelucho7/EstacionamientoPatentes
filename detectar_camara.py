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

# --- Función Principal de Procesamiento para Cámara IP ---
def procesar_camara(url_camara):
    cap = cv2.VideoCapture(url_camara)
    if not cap.isOpened():
        print(f"Error: No se pudo conectar a la cámara IP en '{url_camara}'.")
        print("Asegúrate de que la aplicación de cámara IP esté funcionando en tu celular y que la URL sea correcta.")
        return

    print(f"Cámara IP conectada en '{url_camara}'. Presiona 'q' para salir.")

    # --- Variables para la lógica de confirmación ---
    patente_buffer = collections.deque(maxlen=30) # Almacena las últimas N lecturas válidas
    patentes_confirmadas = set() # Almacena las patentes ya guardadas en esta sesión
    CONFIRMATION_THRESHOLD = 3 # Número de veces que una patente debe ser leída para confirmarse

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el fotograma de la cámara. Posiblemente la conexión se perdió.")
            break

        # No usamos frame_skip para una experiencia más en tiempo real
        results = model.predict(frame, conf=0.6, verbose=False) # Usamos conf=0.6
        
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id].lower()

                if 'patente' in class_name or 'license_plate' in class_name:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    patente_recortada = frame[y1:y2, x1:x2]

                    # 1. Pre-procesar la imagen para mejorar la lectura
                    imagen_mejorada = preprocesar_para_ocr(patente_recortada)
                    
                    # 2. Leer texto con OCR
                    ocr_result = ocr.readtext(imagen_mejorada, detail=0, paragraph=True)

                    if ocr_result:
                        texto_sucio = " ".join(ocr_result)
                        texto_limpio = "".join(filter(str.isalnum, texto_sucio)).upper()

                        # 3. Validar formato de la patente
                        if es_patente_valida(texto_limpio):
                            
                            # 4. Lógica de confirmación por buffer
                            es_similar_a_confirmada = any(son_patentes_similares(texto_limpio, p_confirmada) for p_confirmada in patentes_confirmadas)
                            
                            if not es_similar_a_confirmada:
                                patente_buffer.append(texto_limpio)
                                count = patente_buffer.count(texto_limpio)

                                if count >= CONFIRMATION_THRESHOLD and texto_limpio not in patentes_confirmadas:
                                    print(f"⭐ Patente CONFIRMADA: {texto_limpio}")
                                    guardar_en_sql(texto_limpio)
                                    patentes_confirmadas.add(texto_limpio)
                            
                            # Dibujar texto en el frame
                            color = (0, 255, 0) if texto_limpio in patentes_confirmadas else (255, 255, 0)
                            cv2.putText(frame, texto_limpio, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("Detección en Cámara IP", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): # Q para salir
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n--- Proceso de cámara IP finalizado. ---")
    print(f"Se confirmaron {len(patentes_confirmadas)} patentes únicas en esta sesión: {sorted(list(patentes_confirmadas))}")


if __name__ == "__main__":
    # Asegúrate de que la URL de tu cámara IP sea correcta
    # Si tu app de cámara IP usa un sufijo diferente (ej. /stream), cámbialo aquí.
    IP_CAMERA_URL = "http://10.38.142.109:8080/video"
    procesar_camara(IP_CAMERA_URL)
