import customtkinter as ctk
import tkinter as tk

class RecordingOverlay(ctk.CTkToplevel):
    """Ventana flotante pequeña que muestra el estado de grabación"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuración de ventana - TRIPLICADO de 50x25 a 150x75
        self.title("")
        self.geometry("150x75")
        self.resizable(False, False)
        
        # Always on top
        self.attributes('-topmost', True)
        
        # Sin bordes de ventana
        self.overrideredirect(True)
        
        # Posicionar en esquina superior derecha
        screen_width = self.winfo_screenwidth()
        self.geometry(f"+{int(screen_width - 160)}+10")
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8)
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # LED indicator (círculo de color) - TRIPLICADO
        self.led_canvas = tk.Canvas(self.main_frame, width=30, height=30, 
                                     bg="#1E293B", highlightthickness=0)
        self.led_canvas.pack(side="left", padx=8, pady=8)
        self.led = self.led_canvas.create_oval(5, 5, 25, 25, fill="gray", outline="")
        
        # Timer label - Fuente más grande
        self.timer_label = ctk.CTkLabel(self.main_frame, text="00:00", 
                                        font=("Segoe UI", 24, "bold"), 
                                        text_color="#F8FAFC")
        self.timer_label.pack(side="left", padx=8)
        
        # Estado inicial
        self.is_recording = False
        self.elapsed_time = 0
        
        # Bind para arrastrar la ventana
        self.main_frame.bind("<Button-1>", self.start_move)
        self.main_frame.bind("<B1-Motion>", self.do_move)
        self.timer_label.bind("<Button-1>", self.start_move)
        self.timer_label.bind("<B1-Motion>", self.do_move)
        
        # Ocultar por defecto
        self.withdraw()
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = int(self.winfo_x() + deltax)
        y = int(self.winfo_y() + deltay)
        self.geometry(f"+{x}+{y}")
    
    def set_recording(self):
        """Establecer estado de grabación"""
        self.is_recording = True
        self.led_canvas.itemconfig(self.led, fill="#10B981")  # Verde
        self.deiconify()  # Mostrar ventana
    
    def set_processing(self):
        """Establecer estado de procesamiento"""
        self.is_recording = False
        self.led_canvas.itemconfig(self.led, fill="#F59E0B")  # Amarillo/Naranja
    
    def set_ready(self):
        """Establecer estado listo"""
        self.is_recording = False
        self.led_canvas.itemconfig(self.led, fill="gray")
        self.withdraw()  # Ocultar ventana
    
    def set_error(self):
        """Establecer estado de error"""
        self.is_recording = False
        self.led_canvas.itemconfig(self.led, fill="#EF4444")  # Rojo
    
    def update_timer(self, minutes, seconds):
        """Actualizar el timer"""
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
