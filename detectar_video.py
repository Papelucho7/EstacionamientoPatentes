import cv2
import collections
from core import model, ocr, es_patente_valida, preprocesar_para_ocr, guardar_en_sql, son_patentes_similares

# --- Función Principal de Procesamiento (Lógica de Colab) ---
def procesar_video(ruta_video, frame_skip=4):
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        print(f"Error al abrir el video: '{ruta_video}'")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video cargado: {total_frames} frames a {fps} FPS. Se procesará 1 de cada {frame_skip} frames.")

    # --- Variables para la lógica de confirmación ---
    patente_buffer = collections.deque(maxlen=30) # Almacena las últimas N lecturas válidas
    patentes_confirmadas = set() # Almacena las patentes ya guardadas en esta sesión
    CONFIRMATION_THRESHOLD = 3 # Número de veces que una patente debe ser leída para confirmarse
    frame_actual = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_actual % frame_skip == 0:
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

        cv2.imshow("Detección en Video - Lógica Avanzada", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC para salir
            break
        
        frame_actual += 1

    cap.release()
    cv2.destroyAllWindows()
    print("\n--- Proceso de video finalizado. ---")
    print(f"Se confirmaron {len(patentes_confirmadas)} patentes únicas en esta sesión: {sorted(list(patentes_confirmadas))}")


if __name__ == "__main__":
    # Asegúrate de que la ruta al video sea la correcta
    procesar_video("img/VideoFuncional.mp4")