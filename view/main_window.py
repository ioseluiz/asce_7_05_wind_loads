from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, 
                             QTabWidget, QTextEdit, QSplitter, QGroupBox, QFormLayout, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from .plot_canvas import MplCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Viento ASCE 7-05 (Completa)")
        self.resize(1200, 830) # Aumenté un poco la altura para el footer
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # CAMBIO: Usamos QVBoxLayout como layout principal para apilar el contenido y el footer
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 5) # Márgenes para que respire

        # --- INPUTS (Panel Izquierdo) ---
        scroll_container = QWidget()
        left_layout = QVBoxLayout(scroll_container)
        # Quitar márgenes internos para que encaje bien en el splitter
        left_layout.setContentsMargins(0, 0, 0, 0) 
        
        # Grupo Geometría
        grp_geo = QGroupBox("Geometría del Edificio")
        form_geo = QFormLayout()
        self.input_h = QLineEdit("6.0")
        form_geo.addRow("Altura Muro h (m):", self.input_h)
        self.input_L = QLineEdit("20.0")
        form_geo.addRow("Largo L (m):", self.input_L)
        self.input_B = QLineEdit("10.0")
        form_geo.addRow("Ancho B (m):", self.input_B)
        
        # INPUT: ANGULO
        self.input_theta = QLineEdit("15.0")
        form_geo.addRow("Ángulo Techo (°):", self.input_theta)
        
        self.input_trib = QLineEdit("5.0")
        form_geo.addRow("Ancho Trib. (m):", self.input_trib)
        grp_geo.setLayout(form_geo)
        left_layout.addWidget(grp_geo)

        # Grupo Viento
        grp_site = QGroupBox("Parámetros Viento")
        form_site = QFormLayout()
        self.input_V = QLineEdit("160")
        form_site.addRow("Velocidad (km/h):", self.input_V)
        self.combo_exp = QComboBox()
        self.combo_exp.addItems(["B", "C", "D"])
        form_site.addRow("Exposición:", self.combo_exp)
        self.combo_I = QComboBox()
        self.combo_I.addItems(["1.00", "1.15", "0.87"])
        form_site.addRow("Importancia:", self.combo_I)
        grp_site.setLayout(form_site)
        left_layout.addWidget(grp_site)

        # CONTROL CERRAMIENTO
        grp_enc = QGroupBox("Cerramiento")
        layout_enc = QVBoxLayout()
        self.combo_enclosure = QComboBox()
        self.combo_enclosure.addItems(["Cerrado", "Parcialmente Cerrado", "Abierto"])
        layout_enc.addWidget(self.combo_enclosure)
        grp_enc.setLayout(layout_enc)
        left_layout.addWidget(grp_enc)

        # Botones
        self.btn_calculate = QPushButton("CALCULAR")
        self.btn_calculate.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 12px; border-radius: 4px;")
        left_layout.addWidget(self.btn_calculate)
        
        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setStyleSheet("padding: 8px;")
        left_layout.addWidget(self.btn_pdf)
        
        left_layout.addStretch()

        # --- RESULTADOS (Panel Derecho) ---
        self.tabs = QTabWidget()
        
        # Tab Gráficos
        self.tab_graphics = QWidget()
        layout_gfx = QVBoxLayout(self.tab_graphics)
        
        # Selector de Dirección
        hbox_dir = QHBoxLayout()
        hbox_dir.addWidget(QLabel("Visualizar Dirección:"))
        self.radio_long = QRadioButton("Longitudinal (L)")
        self.radio_trans = QRadioButton("Transversal (B)")
        self.radio_long.setChecked(True)
        self.bg_dir = QButtonGroup()
        self.bg_dir.addButton(self.radio_long)
        self.bg_dir.addButton(self.radio_trans)
        hbox_dir.addWidget(self.radio_long)
        hbox_dir.addWidget(self.radio_trans)
        hbox_dir.addStretch()
        layout_gfx.addLayout(hbox_dir)

        # Canvas
        self.canvas_loads = MplCanvas(self, width=5, height=5)
        layout_gfx.addWidget(self.canvas_loads)
        
        self.tabs.addTab(self.tab_graphics, "Diagrama de Cargas")
        
        # Tab Reporte
        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setStyleSheet("font-family: Consolas, Monospace; font-size: 10pt;")
        self.tabs.addTab(self.txt_report, "Memoria de Cálculo")

        # --- SPLITTER PRINCIPAL ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(scroll_container)
        splitter.addWidget(self.tabs)
        splitter.setSizes([320, 880])
        
        # Añadimos el splitter al layout vertical principal (ocupa todo el espacio sobrante)
        main_layout.addWidget(splitter)

        # --- FOOTER DE COPYRIGHT ---
        # Creamos un widget contenedor para el footer si queremos color de fondo, 
        # o simplemente una etiqueta estilizada.
        lbl_copyright = QLabel("Ing. Jose Luis Muñoz\nTodos los derechos reservados © 2025")
        lbl_copyright.setAlignment(Qt.AlignCenter)
        lbl_copyright.setStyleSheet("""
            QLabel {
                color: #7f8c8d; 
                font-size: 11px; 
                font-weight: bold;
                padding-top: 5px;
                border-top: 1px solid #bdc3c7;
            }
        """)
        main_layout.addWidget(lbl_copyright)

    def get_inputs(self):
        return {
            'V': self.input_V.text(),
            'exposure': self.combo_exp.currentText(),
            'I': self.combo_I.currentText(),
            'h': self.input_h.text(),
            'L': self.input_L.text(),
            'B': self.input_B.text(),
            'theta': self.input_theta.text(),
            'trib_width': self.input_trib.text(),
            'enclosure': self.combo_enclosure.currentText()
        }
    
    def set_report(self, text):
        self.txt_report.setMarkdown(text)
        
    def show_error(self, msg):
        self.txt_report.setText(f"ERROR: {msg}")