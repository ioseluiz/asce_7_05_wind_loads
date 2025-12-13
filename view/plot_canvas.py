from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(FigureCanvas):
    """
    Widget personalizado de Qt que aloja un gráfico de Matplotlib.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)

    def plot_geometry_sketch(self, L, B):
        """Dibuja la vista en planta del edificio (Metros)."""
        self.axes.clear()
        
        # Dibujar rectángulo del edificio
        rect = patches.Rectangle((0, 0), L, B, linewidth=2, edgecolor='#2c3e50', facecolor='#ecf0f1', label='Planta')
        self.axes.add_patch(rect)
        
        # Flecha indicando dirección del viento
        self.axes.arrow(-L*0.2, B/2, L*0.15, 0, head_width=B/10, head_length=L*0.05, fc='#e74c3c', ec='#c0392b')
        self.axes.text(-L*0.2, B/2 + B/10, "Viento", color='#c0392b', fontsize=10, fontweight='bold')
        
        # Cotas simples
        self.axes.text(L/2, -B*0.1, f"L = {L:.1f} m", ha='center', color='blue')
        self.axes.text(-L*0.05, B/2, f"B = {B:.1f} m", va='center', rotation=90, color='blue')

        # Configuración de ejes
        margin = max(L, B) * 0.5
        self.axes.set_xlim(-L*0.3, L + margin)
        self.axes.set_ylim(-B*0.2, B + margin)
        self.axes.set_aspect('equal')
        self.axes.set_title("Vista en Planta (Geometría)", fontsize=10)
        self.axes.grid(True, linestyle='--', alpha=0.5)
        self.draw()

    def plot_frame_load(self, h_wall, width, theta, loads, title="Cargas"):
        """
        Dibuja el marco (Paredes + Techo) con sus cargas.
        Esta es la función que busca el controlador.
        
        Args:
            h_wall (float): Altura del muro (m).
            width (float): Ancho total en la dirección analizada (L o B).
            theta (float): Ángulo del techo en grados.
            loads (dict): Diccionario con 'p_ww', 'p_lw', 'p_roof_ww', 'p_roof_lw'.
        """
        self.axes.clear()
        
        # 1. Geometría
        # Altura del techo (cumbrera)
        h_roof = (width / 2.0) * np.tan(np.radians(theta))
        h_total = h_wall + h_roof
        
        # Coordenadas del polígono del edificio
        # (0,0) -> (0, h_wall) -> (w/2, h_total) -> (w, h_wall) -> (w, 0)
        x_coords = [0, 0, width/2, width, width]
        y_coords = [0, h_wall, h_total, h_wall, 0]
        
        poly = patches.Polygon(np.column_stack((x_coords, y_coords)), 
                               closed=True, edgecolor='black', facecolor='#ecf0f1', linewidth=2)
        self.axes.add_patch(poly)
        
        # Suelo
        self.axes.plot([-width*0.2, width*1.2], [0, 0], color='#27ae60', linewidth=3)

        # 2. Vectores de Carga (Flechas)
        # Factor de escala visual
        scale = width * 0.15
        
        def draw_arrow(x, y, dx, dy, color, text):
            self.axes.arrow(x, y, dx, dy, head_width=scale*0.3, head_length=scale*0.3, fc=color, ec=color)
            # Texto con offset para evitar solapamiento
            offset_scale = 1.5 # Ajusta este valor para mayor separación
            self.axes.text(x + dx*offset_scale, y + dy*offset_scale, text, color=color, fontsize=9, ha='center', va='center', fontweight='bold')

        # --- Pared Barlovento (Izquierda) ---
        # Presión positiva (empuja a la derecha)
        p_ww = loads['p_ww']
        mx = 0
        my = h_wall / 2
        draw_arrow(mx - scale, my, scale*0.8, 0, 'red', f"{p_ww:.1f}")

        # --- Pared Sotavento (Derecha) ---
        # Succión (jala a la derecha)
        p_lw = loads['p_lw'] # Es negativo en cálculo, pero dibujamos la dirección física
        mx = width
        my = h_wall / 2
        # Si p_lw es negativo (lo usual), es succión -> Jala hacia afuera (derecha)
        # Dibujamos flecha saliendo del edificio
        draw_arrow(mx, my, scale*0.8, 0, 'blue', f"{abs(p_lw):.1f}")

        # --- Techo Barlovento (Izquierda) ---
        # Vector normal a la superficie izquierda
        # Pendiente m = tan(theta). Vector director (1, m). Normal (-m, 1) -> Izq (-sin, cos)
        rad = np.radians(theta)
        nx_ww = -np.sin(rad)
        ny_ww = np.cos(rad)
        
        p_r_ww = loads['p_roof_ww']
        # Punto medio techo izq
        mx_r1 = width / 4
        my_r1 = h_wall + h_roof / 2
        
        if p_r_ww < 0: # Succión (Jala hacia afuera/arriba)
            draw_arrow(mx_r1, my_r1, nx_ww*scale, ny_ww*scale, 'blue', f"{abs(p_r_ww):.1f}")
        else: # Presión (Empuja hacia adentro)
            draw_arrow(mx_r1 + nx_ww*scale, my_r1 + ny_ww*scale, -nx_ww*scale, -ny_ww*scale, 'red', f"{p_r_ww:.1f}")

        # --- Techo Sotavento (Derecha) ---
        # Normal superficie derecha (apunta derecha/arriba)
        nx_lw = np.sin(rad)
        ny_lw = np.cos(rad)
        
        p_r_lw = loads['p_roof_lw']
        mx_r2 = width * 0.75
        my_r2 = h_wall + h_roof / 2
        
        # Sotavento techo casi siempre es succión
        if p_r_lw < 0: # Succión (Hacia afuera)
            draw_arrow(mx_r2, my_r2, nx_lw*scale, ny_lw*scale, 'blue', f"{abs(p_r_lw):.1f}")
        else:
             draw_arrow(mx_r2 + nx_lw*scale, my_r2 + ny_lw*scale, -nx_lw*scale, -ny_lw*scale, 'red', f"{p_r_lw:.1f}")

        # Configuración
        self.axes.set_aspect('equal')
        margin = width * 0.5
        self.axes.set_xlim(-margin, width + margin)
        self.axes.set_ylim(0, h_total + margin)
        self.axes.set_title(title)
        self.axes.grid(True, linestyle=':', alpha=0.3)
        self.draw()