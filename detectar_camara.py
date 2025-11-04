import cv2
import collections
from core import model, ocr, es_patente_valida, preprocesar_para_ocr, guardar_en_sql, son_patentes_similares


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

    frame_skip = 5 # Procesar 1 de cada X fotogramas para estabilidad
    frame_actual = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el fotograma de la cámara. Posiblemente la conexión se perdió.")
            break

        if frame_actual % frame_skip == 0: # Solo procesar si es un fotograma seleccionado
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
        
        frame_actual += 1 # Incrementar el contador de fotogramas

    cap.release()
    cv2.destroyAllWindows()
    print("\n--- Proceso de cámara IP finalizado. ---")
    print(f"Se confirmaron {len(patentes_confirmadas)} patentes únicas en esta sesión: {sorted(list(patentes_confirmadas))}")


import configparser

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    IP_CAMERA_URL = config['camera']['url']
    procesar_camara(IP_CAMERA_URL)
