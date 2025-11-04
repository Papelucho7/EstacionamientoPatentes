import cv2
from ultralytics import YOLO
import easyocr
from db_config import get_connection

model = YOLO('model/best.pt')
ocr = easyocr.Reader(['es'], gpu=False)

def guardar_en_sql(patente):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RegistrosPatentes (Patente, FechaRegistro)
            VALUES (?, GETDATE())
        """, (patente,))
        conn.commit()
        conn.close()
        print(f"✅ Guardado en SQL Server: {patente}")
    except Exception as e:
        print(f"❌ Error SQL: {e}")

def procesar_camara():
    cap = cv2.VideoCapture(0)  # 0 = cámara predeterminada
    if not cap.isOpened():
        print("Error: no se detectó cámara.")
        return

    print("Cámara iniciada. Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=0.5, verbose=False)

        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id].lower()

                if 'patente' in class_name or 'license_plate' in class_name:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    recorte = frame[y1:y2, x1:x2]
                    gray = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
                    texto = ocr.readtext(gray, detail=0)
                    texto_limpio = "".join(filter(str.isalnum, " ".join(texto))).upper()

                    if len(texto_limpio) >= 5:
                        guardar_en_sql(texto_limpio)
                        cv2.putText(frame, texto_limpio, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        cv2.imshow("Detección en Cámara", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Q para salir
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    procesar_camara()
