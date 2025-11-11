import cv2
from ultralytics import YOLO
import easyocr
import re
import collections
import numpy as np
from db_config import get_connection
import pyodbc # Added for specific exception handling and type hinting

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

def registrar_movimiento_patente(patente):
    """
    Registra el movimiento de una patente (entrada/salida) en la base de datos.
    Actualiza la tabla 'Vehiculos' y registra el movimiento en 'Movimientos'.
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("Error: No se pudo establecer conexión con la base de datos.")
            return

        cursor = conn.cursor()

        # 1. Verificar el estado actual de la patente en la tabla Vehiculos
        cursor.execute("SELECT Estado FROM Vehiculos WHERE Patente = ?", (patente,))
        resultado = cursor.fetchone()

        tipo_movimiento = ""
        mensaje = ""

        if resultado is None:
            # La patente no existe, es una ENTRADA
            tipo_movimiento = "Entrada"
            cursor.execute("INSERT INTO Vehiculos (Patente, Estado, UltimoMovimiento) VALUES (?, ?, GETDATE())",
                           (patente, "Dentro"))
            mensaje = f"✅ ENTRADA registrada para la patente: {patente}"
        elif resultado[0] == "Fuera":
            # La patente existe y está "Fuera", es una ENTRADA
            tipo_movimiento = "Entrada"
            cursor.execute("UPDATE Vehiculos SET Estado = ?, UltimoMovimiento = GETDATE() WHERE Patente = ?",
                           ("Dentro", patente))
            mensaje = f"✅ ENTRADA registrada para la patente: {patente}"
        elif resultado[0] == "Dentro":
            # La patente existe y está "Dentro", es una SALIDA
            tipo_movimiento = "Salida"
            cursor.execute("UPDATE Vehiculos SET Estado = ?, UltimoMovimiento = GETDATE() WHERE Patente = ?",
                           ("Fuera", patente))
            mensaje = f"✅ SALIDA registrada para la patente: {patente}"
        
        # 2. Registrar el movimiento en la tabla Movimientos
        if tipo_movimiento: # Solo si se determinó un tipo de movimiento
            cursor.execute("INSERT INTO Movimientos (Patente, TipoMovimiento, FechaHora) VALUES (?, ?, GETDATE())",
                           (patente, tipo_movimiento))
            conn.commit()
            print(mensaje)
        else:
            print(f"ℹ️ No se pudo determinar el movimiento para la patente: {patente}")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        if sqlstate == '23000': # Integrity constraint violation (e.g., duplicate primary key)
            print(f"❌ Error de integridad al registrar movimiento para {patente}: {ex}")
        else:
            print(f"❌ Error de base de datos al registrar movimiento para {patente}: {ex}")
        if conn:
            conn.rollback() # Revertir cualquier cambio si hay un error
    except Exception as e:
        print(f"❌ Error inesperado al registrar movimiento para {patente}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def obtener_ocupacion_estacionamiento():
    """
    Obtiene el número de vehículos actualmente "Dentro" del estacionamiento.
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("Error: No se pudo establecer conexión con la base de datos para obtener ocupación.")
            return 0

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Vehiculos WHERE Estado = 'Dentro'")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"❌ Error al obtener la ocupación del estacionamiento: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def obtener_patentes_dentro():
    """
    Obtiene una lista de las patentes de los vehículos actualmente "Dentro".
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("Error: No se pudo establecer conexión con la base de datos.")
            return []

        cursor = conn.cursor()
        cursor.execute("SELECT Patente FROM Vehiculos WHERE Estado = 'Dentro' ORDER BY UltimoMovimiento DESC")
        patentes = [row[0] for row in cursor.fetchall()]
        return patentes
    except Exception as e:
        print(f"❌ Error al obtener las patentes de vehículos dentro: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ultimos_movimientos(limit=50):
    """
    Obtiene una lista de los últimos movimientos registrados.
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("Error: No se pudo establecer conexión con la base de datos.")
            return []

        cursor = conn.cursor()
        # Usamos TOP para limitar los resultados directamente en la consulta SQL
        cursor.execute("""
            SELECT TOP (?) Patente, TipoMovimiento, FechaHora
            FROM Movimientos
            ORDER BY FechaHora DESC
        """, (limit,))
        
        # Formateamos la fecha para que sea más legible en la GUI
        movimientos = []
        for row in cursor.fetchall():
            patente, tipo, fecha = row
            fecha_formateada = fecha.strftime('%Y-%m-%d %H:%M:%S')
            movimientos.append((patente, tipo, fecha_formateada))
            
        return movimientos
    except Exception as e:
        print(f"❌ Error al obtener los últimos movimientos: {e}")
        return []
    finally:
        if conn:
            conn.close()