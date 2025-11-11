import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import cv2
from PIL import Image, ImageTk
from detectar_video import procesar_video
from detectar_camara import procesar_camara
from core import (
    obtener_ocupacion_estacionamiento, obtener_vehiculos_dentro, 
    obtener_ultimos_movimientos, crear_rol, obtener_roles, 
    actualizar_rol, eliminar_rol, crear_persona, obtener_personas,
    actualizar_persona, eliminar_persona, obtener_vehiculos,
    obtener_personas_para_asignacion, asignar_vehiculo
)
import configparser

# --- Constantes ---
TOTAL_ESPACIOS = 30

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de Estacionamiento")
        self.geometry("1280x800")

        self.processing_thread = None
        self.stop_event = threading.Event()
        self.roles_map = {}
        self.personas_map = {}

        style = ttk.Style(self)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

        dashboard_frame = ttk.Frame(self)
        dashboard_frame.pack(pady=10, padx=10, fill="x")
        self.occupancy_label = ttk.Label(dashboard_frame, text="Calculando...", font=("Arial", 16, "bold"))
        self.occupancy_label.pack(pady=(0, 10))

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(pady=10, padx=10, expand=True, fill="both")

        dashboard_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(dashboard_tab, text="Dashboard y Controles")
        self.create_dashboard_tab(dashboard_tab)

        log_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(log_tab, text="Registro de Movimientos")
        self.create_log_tab(log_tab)

        gestion_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(gestion_tab, text="Gestión")
        self.create_gestion_tab(gestion_tab)

        self.update_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_dashboard_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab)
        main_frame.pack(expand=True, fill="both")
        patentes_frame = ttk.LabelFrame(main_frame, text="Vehículos Dentro")
        patentes_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.patentes_tree = ttk.Treeview(patentes_frame, columns=('Patente', 'Propietario'), show='headings')
        self.patentes_tree.heading('Patente', text='Patente')
        self.patentes_tree.heading('Propietario', text='Propietario')
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
        self.log_tree.heading('Patente', text='Patente'); self.log_tree.heading('Movimiento', text='Movimiento'); self.log_tree.heading('FechaHora', text='Fecha y Hora')
        self.log_tree.column('Patente', width=100, anchor='center'); self.log_tree.column('Movimiento', width=100, anchor='center'); self.log_tree.column('FechaHora', width=200)
        self.log_tree.pack(fill="both", expand=True)

    def create_gestion_tab(self, parent_tab):
        gestion_notebook = ttk.Notebook(parent_tab)
        gestion_notebook.pack(expand=True, fill="both", padx=5, pady=5)
        roles_tab = ttk.Frame(gestion_notebook); gestion_notebook.add(roles_tab, text="Roles"); self.create_gestion_roles_tab(roles_tab)
        personas_tab = ttk.Frame(gestion_notebook); gestion_notebook.add(personas_tab, text="Personas"); self.create_gestion_personas_tab(personas_tab)
        vehiculos_tab = ttk.Frame(gestion_notebook); gestion_notebook.add(vehiculos_tab, text="Vehículos"); self.create_gestion_vehiculos_tab(vehiculos_tab)

    def create_gestion_roles_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab); main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        list_frame = ttk.LabelFrame(main_frame, text="Listado de Roles"); list_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        form_frame = ttk.LabelFrame(main_frame, text="Formulario de Rol"); form_frame.pack(side='right', fill='y', padx=(10,0))
        self.roles_tree = ttk.Treeview(list_frame, columns=('ID', 'Nombre'), show='headings'); self.roles_tree.heading('ID', text='ID'); self.roles_tree.heading('Nombre', text='Nombre'); self.roles_tree.column('ID', width=50); self.roles_tree.pack(fill='both', expand=True)
        self.roles_tree.bind('<<TreeviewSelect>>', self.on_rol_select)
        ttk.Label(form_frame, text="Nombre del Rol:").pack(padx=10, pady=(10, 0)); self.rol_nombre_entry = ttk.Entry(form_frame, width=30); self.rol_nombre_entry.pack(padx=10, pady=5)
        buttons_frame = ttk.Frame(form_frame); buttons_frame.pack(padx=10, pady=20, fill='x')
        ttk.Button(buttons_frame, text="Limpiar", command=self.limpiar_form_rol).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Agregar Rol", command=self.agregar_rol).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Guardar Cambios", command=self.guardar_rol).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Eliminar Rol", command=self.eliminar_rol_seleccionado).pack(fill='x', pady=2)
        self.refrescar_roles_treeview()

    def create_gestion_personas_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab); main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        list_frame = ttk.LabelFrame(main_frame, text="Listado de Personas"); list_frame.pack(fill='both', expand=True)
        form_frame = ttk.LabelFrame(main_frame, text="Formulario de Persona"); form_frame.pack(fill='x', pady=10)
        cols = ('RUT', 'Nombre', 'Apellido', 'Teléfono', 'Rol', 'Activo'); self.personas_tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        for col in cols: self.personas_tree.heading(col, text=col)
        self.personas_tree.pack(fill='both', expand=True); self.personas_tree.bind('<<TreeviewSelect>>', self.on_persona_select)
        form_grid = ttk.Frame(form_frame); form_grid.pack(padx=10, pady=10)
        form_labels = ["RUT:", "Nombre:", "Apellido:", "Teléfono:", "Rol:"]; self.persona_entries = {}
        for i, label in enumerate(form_labels):
            ttk.Label(form_grid, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=5)
            if label == "Rol:": self.persona_entries['Rol'] = ttk.Combobox(form_grid, state="readonly"); self.persona_entries['Rol'].grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            else: entry = ttk.Entry(form_grid); entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5); self.persona_entries[label[:-1]] = entry
        self.persona_activo_var = tk.BooleanVar(value=True); ttk.Checkbutton(form_grid, text="Activo", variable=self.persona_activo_var).grid(row=len(form_labels), column=1, sticky='w', padx=5, pady=5)
        buttons_frame = ttk.Frame(form_frame); buttons_frame.pack(pady=10)
        ttk.Button(buttons_frame, text="Limpiar", command=self.limpiar_form_persona).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Agregar Persona", command=self.agregar_persona).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Guardar Cambios", command=self.guardar_persona).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Eliminar Persona", command=self.eliminar_persona_seleccionada).pack(side='left', padx=5)
        self.refrescar_personas_treeview()

    def create_gestion_vehiculos_tab(self, parent_tab):
        main_frame = ttk.Frame(parent_tab); main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        list_frame = ttk.LabelFrame(main_frame, text="Listado de Vehículos"); list_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        form_frame = ttk.LabelFrame(main_frame, text="Asignar Propietario"); form_frame.pack(side='right', fill='y', padx=(10,0))
        cols = ('Patente', 'RUT Dueño', 'Nombre Dueño'); self.vehiculos_tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        for col in cols: self.vehiculos_tree.heading(col, text=col)
        self.vehiculos_tree.pack(fill='both', expand=True)
        self.vehiculos_tree.bind('<<TreeviewSelect>>', self.on_vehiculo_select)
        ttk.Label(form_frame, text="Vehículo Seleccionado:").pack(padx=10, pady=(10,0)); self.vehiculo_seleccionado_label = ttk.Label(form_frame, text="Ninguno", font=('Arial', 10, 'bold')); self.vehiculo_seleccionado_label.pack(padx=10, pady=2)
        ttk.Label(form_frame, text="Asignar a Persona:").pack(padx=10, pady=(10,0)); self.vehiculo_persona_combo = ttk.Combobox(form_frame, state="readonly", width=35); self.vehiculo_persona_combo.pack(padx=10, pady=5)
        buttons_frame = ttk.Frame(form_frame); buttons_frame.pack(padx=10, pady=20, fill='x')
        ttk.Button(buttons_frame, text="Asignar", command=self.asignar_vehiculo_seleccionado).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Quitar Asignación", command=self.desasignar_vehiculo_seleccionado).pack(fill='x', pady=2)
        self.refrescar_vehiculos_treeview()

    def refrescar_roles_treeview(self):
        self.roles_map = {name: id for id, name in obtener_roles()}
        self.roles_tree.delete(*self.roles_tree.get_children())
        for name, id in self.roles_map.items(): self.roles_tree.insert('', 'end', values=(id, name))
        if hasattr(self, 'persona_entries'): self.persona_entries['Rol']['values'] = list(self.roles_map.keys())
    def on_rol_select(self, event): item = self.roles_tree.focus(); self.rol_nombre_entry.delete(0, tk.END); self.rol_nombre_entry.insert(0, self.roles_tree.item(item, 'values')[1]) if item else None
    def limpiar_form_rol(self): self.rol_nombre_entry.delete(0, tk.END); self.roles_tree.selection_remove(self.roles_tree.selection())
    def agregar_rol(self): nombre = self.rol_nombre_entry.get().strip(); success, msg = crear_rol(nombre); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_rol(); self.refrescar_roles_treeview()
    def guardar_rol(self): item = self.roles_tree.focus(); rol_id = self.roles_tree.item(item, 'values')[0]; nombre = self.rol_nombre_entry.get().strip(); success, msg = actualizar_rol(rol_id, nombre); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_rol(); self.refrescar_roles_treeview()
    def eliminar_rol_seleccionado(self): item = self.roles_tree.focus(); rol_id, nombre = self.roles_tree.item(item, 'values'); success, msg = eliminar_rol(rol_id); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_rol(); self.refrescar_roles_treeview()

    def refrescar_personas_treeview(self):
        self.personas_tree.delete(*self.personas_tree.get_children())
        personas_list = obtener_personas()
        for p in personas_list: self.personas_tree.insert('', 'end', values=(p.RUT, p.Nombre, p.Apellido, p.Telefono or '', p.Rol or '', 'Sí' if p.Activo else 'No'))
        self.personas_map = {f"{p.Nombre} {p.Apellido} ({p.RUT})": p.RUT for p in personas_list}
        if hasattr(self, 'vehiculo_persona_combo'): self.vehiculo_persona_combo['values'] = list(self.personas_map.keys())
    def on_persona_select(self, event):
        item = self.personas_tree.focus(); values = self.personas_tree.item(item, 'values'); self.limpiar_form_persona(keep_selection=True)
        self.persona_entries['RUT'].insert(0, values[0]); self.persona_entries['RUT'].config(state='readonly'); self.persona_entries['Nombre'].insert(0, values[1]); self.persona_entries['Apellido'].insert(0, values[2]); self.persona_entries['Teléfono'].insert(0, values[3]); self.persona_entries['Rol'].set(values[4]); self.persona_activo_var.set(True if values[5] == 'Sí' else False)
    def limpiar_form_persona(self, keep_selection=False):
        for key, entry in self.persona_entries.items():
            if key != 'Rol': entry.delete(0, tk.END)
            if key == 'RUT': entry.config(state='normal')
        self.persona_entries['Rol'].set(''); self.persona_activo_var.set(True)
        if not keep_selection: self.personas_tree.selection_remove(self.personas_tree.selection())
    def agregar_persona(self): rut, nombre, apellido, telefono, rol_nombre = [self.persona_entries[k].get().strip() for k in ['RUT', 'Nombre', 'Apellido', 'Teléfono', 'Rol']]; id_rol = self.roles_map.get(rol_nombre); activo = self.persona_activo_var.get(); success, msg = crear_persona(rut, nombre, apellido, telefono, id_rol, activo); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_persona(); self.refrescar_personas_treeview()
    def guardar_persona(self): rut = self.persona_entries['RUT'].get().strip(); nombre, apellido, telefono, rol_nombre = [self.persona_entries[k].get().strip() for k in ['Nombre', 'Apellido', 'Teléfono', 'Rol']]; id_rol = self.roles_map.get(rol_nombre); activo = self.persona_activo_var.get(); success, msg = actualizar_persona(rut, nombre, apellido, telefono, id_rol, activo); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_persona(); self.refrescar_personas_treeview()
    def eliminar_persona_seleccionada(self): rut = self.persona_entries['RUT'].get().strip(); success, msg = eliminar_persona(rut); messagebox.showinfo("Resultado", msg or "Éxito"); self.limpiar_form_persona(); self.refrescar_personas_treeview()

    def refrescar_vehiculos_treeview(self):
        self.vehiculos_tree.delete(*self.vehiculos_tree.get_children())
        for v in obtener_vehiculos(): self.vehiculos_tree.insert('', 'end', values=v)
    def on_vehiculo_select(self, event): item = self.vehiculos_tree.focus(); patente = self.vehiculos_tree.item(item, 'values')[0]; self.vehiculo_seleccionado_label.config(text=patente)
    def asignar_vehiculo_seleccionado(self):
        patente = self.vehiculo_seleccionado_label.cget("text")
        persona_str = self.vehiculo_persona_combo.get()
        if patente == "Ninguno" or not persona_str: messagebox.showwarning("Faltan Datos", "Selecciona un vehículo y una persona."); return
        rut = self.personas_map.get(persona_str)
        success, msg = asignar_vehiculo(patente, rut); messagebox.showinfo("Resultado", msg or "Éxito"); self.refrescar_vehiculos_treeview()
    def desasignar_vehiculo_seleccionado(self):
        patente = self.vehiculo_seleccionado_label.cget("text")
        if patente == "Ninguno": messagebox.showwarning("Faltan Datos", "Selecciona un vehículo."); return
        success, msg = asignar_vehiculo(patente, None); messagebox.showinfo("Resultado", msg or "Éxito"); self.refrescar_vehiculos_treeview()

    def create_video_tab(self, parent):
        controls_frame = ttk.Frame(parent); controls_frame.pack(fill="x", pady=5); ttk.Label(controls_frame, text="Ruta:").pack(side="left", padx=(0, 5)); self.video_path_entry = ttk.Entry(controls_frame, width=40); self.video_path_entry.pack(side="left", expand=True, fill="x"); self.browse_button = ttk.Button(controls_frame, text="Examinar", command=self.browse_video); self.browse_button.pack(side="left", padx=5)
        action_frame = ttk.Frame(parent); action_frame.pack(fill="x", pady=5); self.process_video_button = ttk.Button(action_frame, text="Procesar", command=self.process_video); self.process_video_button.pack(side="left", padx=5); self.stop_video_button = ttk.Button(action_frame, text="Detener", command=self.stop_processing, state="disabled"); self.stop_video_button.pack(side="left", padx=5)
        self.video_label = ttk.Label(parent, background="black"); self.video_label.pack(expand=True, fill="both", pady=10)
    def create_camera_tab(self, parent):
        ttk.Label(parent, text="URL de la cámara IP:").pack(pady=5); self.camera_url_entry = ttk.Entry(parent, width=40); self.camera_url_entry.pack(pady=5); config = configparser.ConfigParser(); config.read('config.ini'); self.camera_url_entry.insert(0, config.get('camera', 'url', fallback='rtsp://...')); self.process_camera_button = ttk.Button(parent, text="Procesar Cámara", command=self.process_camera); self.process_camera_button.pack(pady=10)
    def browse_video(self): filepath = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")]); self.video_path_entry.delete(0, tk.END); self.video_path_entry.insert(0, filepath)
    def process_video(self):
        video_path = self.video_path_entry.get()
        if video_path: self.stop_event.clear(); self.process_video_button.config(state="disabled"); self.stop_video_button.config(state="normal"); self.browse_button.config(state="disabled"); self.processing_thread = threading.Thread(target=self._run_video_processing, args=(video_path,)); self.processing_thread.start()
    def _run_video_processing(self, video_path): procesar_video(video_path, self.update_video_frame, self.stop_event); self.process_video_button.config(state="normal"); self.stop_video_button.config(state="disabled"); self.browse_button.config(state="normal"); self.after(100, self.update_dashboard)
    def update_video_frame(self, frame):
        try:
            h, w, _ = frame.shape; max_h = self.video_label.winfo_height(); max_w = self.video_label.winfo_width()
            if max_h < 2 or max_w < 2: self.after(20, lambda: self.update_video_frame(frame)); return
            scale = min(max_w/w, max_h/h); new_w, new_h = int(w*scale), int(h*scale); resized_frame = cv2.resize(frame, (new_w, new_h)); rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB); img = Image.fromarray(rgb_frame); imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk; self.video_label.config(image=imgtk)
        except Exception as e: print(f"Error al actualizar frame de video: {e}")
    def stop_processing(self): self.stop_event.set()
    def process_camera(self): camera_url = self.camera_url_entry.get(); thread = threading.Thread(target=self._run_camera_processing, args=(camera_url,)); thread.start()
    def _run_camera_processing(self, camera_url): self.process_camera_button.config(state="disabled"); procesar_camara(camera_url); self.process_camera_button.config(state="normal"); self.after(100, self.update_dashboard)
    def update_dashboard(self):
        try:
            ocupados = obtener_ocupacion_estacionamiento(); disponibles = TOTAL_ESPACIOS - ocupados; self.occupancy_label.config(text=f"Espacios Disponibles: {disponibles} de {TOTAL_ESPACIOS}")
            self.patentes_tree.delete(*self.patentes_tree.get_children())
            for vehiculo in obtener_vehiculos_dentro(): self.patentes_tree.insert('', 'end', values=vehiculo)
            self.log_tree.delete(*self.log_tree.get_children())
            for movimiento in obtener_ultimos_movimientos(limit=50): self.log_tree.insert('', 'end', values=movimiento)
            if hasattr(self, 'roles_tree'): self.refrescar_roles_treeview()
            if hasattr(self, 'personas_tree'): self.refrescar_personas_treeview()
            if hasattr(self, 'vehiculos_tree'): self.refrescar_vehiculos_treeview()
        except Exception as e: print(f"Error en update_dashboard: {e}")
        finally: self.after(5000, self.update_dashboard)
    def on_closing(self):
        print("Cerrando aplicación..."); self.stop_event.set()
        if self.processing_thread and self.processing_thread.is_alive(): self.processing_thread.join(timeout=1.0)
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()


