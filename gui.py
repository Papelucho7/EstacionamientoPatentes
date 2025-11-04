
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from detectar_video import procesar_video
from detectar_camara import procesar_camara
import configparser

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reconocimiento de Patentes")
        self.geometry("500x250")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Pestaña para procesar video
        self.video_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.video_tab, text="Procesar Video")
        self.create_video_tab()

        # Pestaña para procesar cámara
        self.camera_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.camera_tab, text="Procesar Cámara")
        self.create_camera_tab()

    def create_video_tab(self):
        # Etiqueta y entrada para la ruta del video
        self.video_path_label = ttk.Label(self.video_tab, text="Ruta del video:")
        self.video_path_label.pack(pady=5)

        self.video_path_entry = ttk.Entry(self.video_tab, width=50)
        self.video_path_entry.pack(pady=5)

        self.browse_button = ttk.Button(self.video_tab, text="Examinar", command=self.browse_video)
        self.browse_button.pack(pady=5)

        # Botón para iniciar el procesamiento
        self.process_video_button = ttk.Button(self.video_tab, text="Procesar Video", command=self.process_video)
        self.process_video_button.pack(pady=10)

    def create_camera_tab(self):
        # Etiqueta y entrada para la URL de la cámara
        self.camera_url_label = ttk.Label(self.camera_tab, text="URL de la cámara IP:")
        self.camera_url_label.pack(pady=5)

        self.camera_url_entry = ttk.Entry(self.camera_tab, width=50)
        self.camera_url_entry.pack(pady=5)

        # Cargar la URL desde el archivo de configuración
        config = configparser.ConfigParser()
        config.read('config.ini')
        camera_url = config['camera']['url']
        self.camera_url_entry.insert(0, camera_url)

        # Botón para iniciar el procesamiento
        self.process_camera_button = ttk.Button(self.camera_tab, text="Procesar Cámara", command=self.process_camera)
        self.process_camera_button.pack(pady=10)

    def browse_video(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.video_path_entry.delete(0, tk.END)
            self.video_path_entry.insert(0, filepath)

    def process_video(self):
        video_path = self.video_path_entry.get()
        if video_path:
            # Ejecutar el procesamiento de video en un hilo separado para no bloquear la GUI
            thread = threading.Thread(target=procesar_video, args=(video_path,))
            thread.start()

    def process_camera(self):
        camera_url = self.camera_url_entry.get()
        if camera_url:
            # Ejecutar el procesamiento de la cámara en un hilo separado
            thread = threading.Thread(target=procesar_camara, args=(camera_url,))
            thread.start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
