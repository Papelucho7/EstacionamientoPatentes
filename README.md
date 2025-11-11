
## Configuración

1.  **Base de Datos SQL Server:**
    Asegúrate de tener una instancia de SQL Server accesible. El script `db_config.py` está configurado para usar `Trusted_Connection=yes`. Si tu configuración es diferente, ajusta la cadena de conexión en `db_config.py` o en `config.ini`.

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

4.  **Ejecutar script para crear tablas en base de datos:**
    En el directorio del proyecto hay un script EstacionamientoPatentes.sql, ejecutarlo en sql server para crear las tablas


## Uso

Para iniciar la aplicación con la interfaz gráfica, ejecuta:

```bash
python gui.py
```

Desde la GUI, puedes:

-   **Procesar Video:** Seleccionar un archivo de video local para que el sistema detecte y registre las patentes. El video esta en img/VideoFuncional.mp4
-   **Procesar Cámara:** Introducir la URL de una cámara IP para realizar el reconocimiento de patentes en tiempo real.
