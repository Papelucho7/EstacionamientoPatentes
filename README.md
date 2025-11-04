# Reconocimiento de Patentes

Este proyecto implementa un sistema de reconocimiento de patentes vehiculares chilenas utilizando visión por computadora y aprendizaje automático. El sistema es capaz de detectar y leer patentes tanto de transmisiones de cámaras IP en tiempo real como de archivos de video, almacenando las patentes reconocidas en una base de datos SQL Server.

## Características

- Detección de patentes vehiculares mediante el modelo YOLO (You Only Look Once).
- Reconocimiento óptico de caracteres (OCR) de las patentes detectadas utilizando EasyOCR.
- Validación del formato de patentes chilenas (BBBB11 y BB1111).
- Lógica de confirmación de patentes para reducir falsos positivos.
- Almacenamiento de patentes confirmadas en una base de datos SQL Server.
- Interfaz gráfica de usuario (GUI) para facilitar la interacción con el sistema.

## Tecnologías Utilizadas

- Python
- OpenCV (`cv2`)
- Ultralytics YOLO
- EasyOCR
- `pyodbc` para conexión a SQL Server
- `numpy`
- `tkinter` para la interfaz gráfica
- `configparser` para la gestión de configuración

## Estructura del Proyecto

```
. (Raíz del proyecto)
├── db_config.py            # Configuración y conexión a la base de datos SQL Server
├── detectar_camara.py      # Script para procesar video de una cámara IP
├── detectar_video.py       # Script para procesar un archivo de video
├── core.py                 # Funciones comunes de detección, OCR y validación de patentes
├── gui.py                  # Interfaz gráfica de usuario (GUI) para la aplicación
├── config.ini              # Archivo de configuración para la base de datos y la cámara IP
├── requirements.txt        # Lista de dependencias del proyecto
├── model/
│   └── best.pt             # Modelo YOLO entrenado para detección de patentes
├── img/
│   └── VideoFuncional.mp4  # Video de ejemplo para pruebas
└── venv/                   # Entorno virtual de Python
```

## Configuración

1.  **Base de Datos SQL Server:**
    Asegúrate de tener una instancia de SQL Server accesible. El script `db_config.py` está configurado para usar `Trusted_Connection=yes`. Si tu configuración es diferente, ajusta la cadena de conexión en `db_config.py` o en `config.ini`.

    La base de datos debe contener una tabla `RegistrosPatentes` con al menos las columnas `Patente` (VARCHAR) y `FechaRegistro` (DATETIME).

2.  **Archivo `config.ini`:**
    Edita el archivo `config.ini` para configurar los parámetros de tu base de datos y la URL de tu cámara IP:

    ```ini
    [database]
    server = TU_SERVIDOR_SQL\TU_INSTANCIA
    database = TU_BASE_DE_DATOS

    [camera]
    url = TU_URL_CAMARA_IP
    ```
    Reemplaza `TU_SERVIDOR_SQL\TU_INSTANCIA`, `TU_BASE_DE_DATOS` y `TU_URL_CAMARA_IP` con tus propios valores.

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd patentesbruh
    ```

2.  **Crear y activar un entorno virtual (recomendado):**

    ```bash
    python -m venv venv
    # En Windows
    .\venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Descargar modelos de EasyOCR:**
    La primera vez que ejecutes EasyOCR, descargará automáticamente los modelos de idioma necesarios. Asegúrate de tener conexión a internet.

## Uso

Para iniciar la aplicación con la interfaz gráfica, ejecuta:

```bash
python gui.py
```

Desde la GUI, puedes:

-   **Procesar Video:** Seleccionar un archivo de video local para que el sistema detecte y registre las patentes.
-   **Procesar Cámara:** Introducir la URL de una cámara IP para realizar el reconocimiento de patentes en tiempo real.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un *issue* o envía un *pull request*.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
