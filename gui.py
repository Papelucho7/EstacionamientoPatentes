import tkinter as tk
from tkinter import ttk, filedialog
import threading
import cv2
from PIL import Image, ImageTk
from detectar_video import procesar_video
from detectar_camara import procesar_camara
from core import obtener_ocupacion_estacionamiento, obtener_patentes_dentro, obtener_ultimos_movimientos
import configparser

# --- Constantes ---
TOTAL_ESPACIOS = 30

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de Estacionamiento")
        self.geometry("1024x768") # Aumentar tamaño de la ventana

        self.processing_thread = None
        self.stop_event = threading.Event()

        # --- Frame principal para el dashboard de ocupación ---
        dashboard_frame = ttk.Frame(self)
        dashboard_frame.pack(pady=10, padx=10, fill="x")

        self.occupancy_label = ttk.Label(dashboard_frame, text="Calculando...", font=("Arial", 16, "bold"))
        self.occupancy_label.pack(pady=(0, 10))

        # --- Notebook principal para separar vistas ---
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # --- Pestaña 1: Dashboard (Vehículos Dentro y Controles) ---
        dashboard_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(dashboard_tab, text="Dashboard y Controles")
        self.create_dashboard_tab(dashboard_tab)

        # --- Pestaña 2: Registro de Movimientos ---
        log_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(log_tab, text="Registro de Movimientos")
        self.create_log_tab(log_tab)

        # Iniciar la actualización periódica
        self.update_dashboard()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_dashboard_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab)
        main_frame.pack(expand=True, fill="both")

        patentes_frame = ttk.LabelFrame(main_frame, text="Vehículos Dentro")
        patentes_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.patentes_tree = ttk.Treeview(patentes_frame, columns=('Patente',), show='headings')
        self.patentes_tree.heading('Patente', text='Patente')
        self.patentes_tree.pack(fill="both", expand=True)

        control_notebook = ttk.Notebook(main_frame)
        control_notebook.pack(side="right", fill="both", expand=True)

        video_tab = ttk.Frame(control_notebook)
        control_notebook.add(video_tab, text="Procesar Video")
        self.create_video_tab(video_tab)

        camera_tab = ttk.Frame(control_notebook)
        control_notebook.add(camera_tab, text="Procesar Cámara")
        self.create_camera_tab(camera_tab)

    def create_log_tab(self, parent_tab):
        log_frame = ttk.LabelFrame(parent_tab, text="Últimos 50 Movimientos")
        log_frame.pack(expand=True, fill="both", padx=5, pady=5)

        self.log_tree = ttk.Treeview(log_frame, columns=('Patente', 'Movimiento', 'FechaHora'), show='headings')
        self.log_tree.heading('Patente', text='Patente')
        self.log_tree.heading('Movimiento', text='Movimiento')
        self.log_tree.heading('FechaHora', text='Fecha y Hora')
        
        self.log_tree.column('Patente', width=100, anchor='center')
        self.log_tree.column('Movimiento', width=100, anchor='center')
        self.log_tree.column('FechaHora', width=200)

        self.log_tree.pack(fill="both", expand=True)

    def create_video_tab(self, parent):
        # Frame para controles
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", pady=5)

        ttk.Label(controls_frame, text="Ruta:").pack(side="left", padx=(0, 5))
        self.video_path_entry = ttk.Entry(controls_frame, width=40)
        self.video_path_entry.pack(side="left", expand=True, fill="x")
        self.browse_button = ttk.Button(controls_frame, text="Examinar", command=self.browse_video)
        self.browse_button.pack(side="left", padx=5)

        # Frame para botones de acción
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill="x", pady=5)
        self.process_video_button = ttk.Button(action_frame, text="Procesar", command=self.process_video)
        self.process_video_button.pack(side="left", padx=5)
        self.stop_video_button = ttk.Button(action_frame, text="Detener", command=self.stop_processing, state="disabled")
        self.stop_video_button.pack(side="left", padx=5)

        # Label para mostrar el video
        self.video_label = ttk.Label(parent, background="black")
        self.video_label.pack(expand=True, fill="both", pady=10)

    def create_camera_tab(self, parent):
        # (Funcionalidad de cámara no modificada para mostrar video, solo la de video)
        ttk.Label(parent, text="URL de la cámara IP:").pack(pady=5)
        self.camera_url_entry = ttk.Entry(parent, width=40)
        self.camera_url_entry.pack(pady=5)
        config = configparser.ConfigParser()
        config.read('config.ini')
        camera_url = config.get('camera', 'url', fallback='rtsp://...')
        self.camera_url_entry.insert(0, camera_url)
        self.process_camera_button = ttk.Button(parent, text="Procesar Cámara", command=self.process_camera)
        self.process_camera_button.pack(pady=10)

    def browse_video(self):
        filepath = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if filepath:
            self.video_path_entry.delete(0, tk.END)
            self.video_path_entry.insert(0, filepath)

    def process_video(self):
        video_path = self.video_path_entry.get()
        if video_path:
            self.stop_event.clear()
            self.process_video_button.config(state="disabled")
            self.stop_video_button.config(state="normal")
            self.browse_button.config(state="disabled")
            
            self.processing_thread = threading.Thread(target=self._run_video_processing, args=(video_path,))
            self.processing_thread.start()

    def _run_video_processing(self, video_path):
        procesar_video(video_path, self.update_video_frame, self.stop_event)
        # Una vez que el bucle termina, reactivar los botones
        self.process_video_button.config(state="normal")
        self.stop_video_button.config(state="disabled")
        self.browse_button.config(state="normal")
        self.after(100, self.update_dashboard)

    def update_video_frame(self, frame):
        try:
            # Redimensionar el frame para que quepa en la GUI
            h, w, _ = frame.shape
            max_h = self.video_label.winfo_height()
            max_w = self.video_label.winfo_width()
            if max_h < 2 or max_w < 2: # Aún no se ha dibujado el widget
                self.after(20, lambda: self.update_video_frame(frame)) # Reintentar pronto
                return

            scale = min(max_w/w, max_h/h)
            new_w, new_h = int(w*scale), int(h*scale)
            
            resized_frame = cv2.resize(frame, (new_w, new_h))
            
            # Convertir para Tkinter
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Actualizar el label
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        except Exception as e:
            print(f"Error al actualizar frame de video: {e}")

    def stop_processing(self):
        self.stop_event.set()

    def process_camera(self):
        # La lógica de la cámara sigue igual, sin visualización integrada por ahora
        camera_url = self.camera_url_entry.get()
        if camera_url:
            thread = threading.Thread(target=self._run_camera_processing, args=(camera_url,))
            thread.start()

    def _run_camera_processing(self, camera_url):
        self.process_camera_button.config(state="disabled")
        procesar_camara(camera_url)
        self.process_camera_button.config(state="normal")
        self.after(100, self.update_dashboard)

    def update_dashboard(self):
        try:
            ocupados = obtener_ocupacion_estacionamiento()
            disponibles = TOTAL_ESPACIOS - ocupados
            self.occupancy_label.config(text=f"Espacios Disponibles: {disponibles} de {TOTAL_ESPACIOS}")

            patentes_dentro = obtener_patentes_dentro()
            self.patentes_tree.delete(*self.patentes_tree.get_children())
            for patente in patentes_dentro:
                self.patentes_tree.insert('', 'end', values=(patente,))

            ultimos_movimientos = obtener_ultimos_movimientos(limit=50)
            self.log_tree.delete(*self.log_tree.get_children())
            for movimiento in ultimos_movimientos:
                self.log_tree.insert('', 'end', values=movimiento)

        except Exception as e:
            print(f"Error en update_dashboard: {e}")
        finally:
            self.after(5000, self.update_dashboard)

    def on_closing(self):
        print("Cerrando aplicación...")
        self.stop_event.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()


