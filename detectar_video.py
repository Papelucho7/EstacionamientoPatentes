import cv2
import collections
import time
from core import model, ocr, es_patente_valida, preprocesar_para_ocr, registrar_movimiento_patente, son_patentes_similares

# --- Función Principal de Procesamiento de Video (Refactorizada para GUI) ---
def procesar_video(ruta_video, frame_callback, stop_event, frame_skip=3):
    """
    Procesa un video para detectar patentes y llama a un callback en cada frame.
    :param ruta_video: Ruta del archivo de video.
    :param frame_callback: Función a la que se le pasa cada frame procesado.
    :param stop_event: threading.Event para detener el bucle de procesamiento.
    :param frame_skip: Número de frames a saltar para optimizar el rendimiento.
    """
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        print(f"Error al abrir el video: '{ruta_video}'")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"Video cargado. Procesando a aprox. {fps/frame_skip:.1f} FPS.")

    patente_buffer = collections.deque(maxlen=30)
    patentes_confirmadas = set()
    CONFIRMATION_THRESHOLD = 3
    frame_actual = 0

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Fin del video.")
            break

        if frame_actual % frame_skip == 0:
            results = model.predict(frame, conf=0.6, verbose=False)
            
            for r in results:
                for box in r.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id].lower()

                    if 'patente' in class_name or 'license_plate' in class_name:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        patente_recortada = frame[y1:y2, x1:x2]

                        try:
                            imagen_mejorada = preprocesar_para_ocr(patente_recortada)
                            ocr_result = ocr.readtext(imagen_mejorada, detail=0, paragraph=True)

                            if ocr_result:
                                texto_sucio = " ".join(ocr_result)
                                texto_limpio = "".join(filter(str.isalnum, texto_sucio)).upper()

                                if es_patente_valida(texto_limpio):
                                    es_similar_a_confirmada = any(son_patentes_similares(texto_limpio, p_confirmada) for p_confirmada in patentes_confirmadas)
                                    
                                    if not es_similar_a_confirmada:
                                        patente_buffer.append(texto_limpio)
                                        count = patente_buffer.count(texto_limpio)

                                        if count >= CONFIRMATION_THRESHOLD and texto_limpio not in patentes_confirmadas:
                                            print(f"⭐ Patente CONFIRMADA: {texto_limpio}")
                                            registrar_movimiento_patente(texto_limpio)
                                            patentes_confirmadas.add(texto_limpio)
                                    
                                    color = (0, 255, 0) if texto_limpio in patentes_confirmadas else (255, 255, 0)
                                    cv2.putText(frame, texto_limpio, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                        except Exception as e:
                            print(f"Error procesando recorte de patente: {e}")

        # Enviar el frame a la GUI a través del callback
        if frame_callback:
            frame_callback(frame)
        
        frame_actual += 1
        # Pequeña pausa para no saturar la GUI y controlar la velocidad de reproducción
        time.sleep(1 / (fps * 1.5))


    cap.release()
    print("\n--- Proceso de video finalizado. ---")
    # La GUI será notificada de la finalización porque el hilo terminará.

if __name__ == "__main__":
    # Ejemplo de cómo se podría usar ahora (sin GUI)
    # Para probar, necesitaríamos un callback simple y un evento de stop
    import threading

    def simple_frame_viewer(frame):
        cv2.imshow("Test Viewer", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # Esto no detendrá el bucle, solo es para el waitKey
            pass

    stop_event = threading.Event()
    
    # Simular la ejecución: presionar Ctrl+C en la terminal para detener
    try:
        print("Ejecutando prueba. Presiona Ctrl+C en la terminal para detener.")
        procesar_video("img/VideoFuncional.mp4", frame_callback=simple_frame_viewer, stop_event=stop_event)
    except KeyboardInterrupt:
        print("\nDeteniendo por el usuario.")
        stop_event.set()
    
    cv2.destroyAllWindows()