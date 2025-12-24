import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, 
                             QTabWidget, QTextEdit, QSplitter, QGroupBox, QFormLayout, 
                             QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from .plot_canvas import MplCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora Viento ASCE 7-05 (Estilo Excel)")
        self.resize(1300, 850)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- PANEL DE ENTRADA (Izquierda) ---
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # 1. Datos Generales
        grp_gen = QGroupBox("1. Datos Generales")
        form_gen = QFormLayout()
        self.input_V = QLineEdit("115") 
        form_gen.addRow("Velocidad V (km/h):", self.input_V)
        self.combo_exp = QComboBox()
        self.combo_exp.addItems(["B", "C", "D"])
        self.combo_exp.setCurrentText("C") 
        form_gen.addRow("Exposición:", self.combo_exp)
        self.combo_I = QComboBox()
        self.combo_I.addItems(["1.00", "0.87", "1.15"])
        form_gen.addRow("Importancia (I):", self.combo_I)
        grp_gen.setLayout(form_gen)
        input_layout.addWidget(grp_gen)

        # --- 2. Geometría ---
        grp_geo = QGroupBox("2. Geometría del Edificio")
        layout_geo_main = QVBoxLayout()
        
        # A. Fila de Inputs
        form_geo = QFormLayout()
        self.input_h = QLineEdit("3.45")
        form_geo.addRow("Altura Media h (m):", self.input_h)
        self.input_L = QLineEdit("11.55")
        form_geo.addRow("Largo L (m):", self.input_L)
        self.input_B = QLineEdit("15.80")
        form_geo.addRow("Ancho B (m):", self.input_B)
        self.input_theta = QLineEdit("15.0")
        form_geo.addRow("Ángulo Techo (°):", self.input_theta)
        
        layout_geo_main.addLayout(form_geo)

        # B. Área de Imagen (CARGADA DESDE ASSETS)
        self.lbl_diagram = QLabel()
        self.lbl_diagram.setAlignment(Qt.AlignCenter)
        self.lbl_diagram.setStyleSheet("border: 1px solid #bdc3c7; background-color: #ecf0f1; border-radius: 4px;")
        self.lbl_diagram.setMinimumHeight(180) # Altura para la imagen
        
        # --- LÓGICA DE RUTA PARA ASSETS ---
        # 1. Obtenemos la ruta donde está este archivo (main_window.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 2. Subimos un nivel (si main_window está en 'view', subimos a la raíz)
        # Nota: Ajusta esto según donde esté main_window.py. 
        # Si main_window.py está en la raíz junto a main.py, usa current_dir.
        # Si main_window.py está en /view/, usa project_root = os.path.dirname(current_dir)
        project_root = os.path.dirname(current_dir) # Asumiendo estructura /view/main_window.py
        
        # 3. Construimos la ruta a assets/esquema.png
        image_path = os.path.join(project_root, "assets", "esquema.png")
        
        # Depuración: Si no carga, descomenta esto para ver dónde busca
        # print(f"Buscando imagen en: {image_path}")

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Escalar imagen para que quepa bien
            self.lbl_diagram.setPixmap(pixmap.scaled(300, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback si no encuentra la imagen
            self.lbl_diagram.setText(f"IMAGEN NO ENCONTRADA\nColoque 'esquema.png' en:\n{image_path}")
            self.lbl_diagram.setStyleSheet("color: red; border: 1px dashed red; font-size: 10px;")

        layout_geo_main.addWidget(self.lbl_diagram)
        
        lbl_note = QLabel("Nota: L y B dimensiones en planta.\nEl programa rota el viento automáticamente.")
        lbl_note.setStyleSheet("font-size: 10px; color: #7f8c8d; font-style: italic;")
        lbl_note.setAlignment(Qt.AlignCenter)
        layout_geo_main.addWidget(lbl_note)

        grp_geo.setLayout(layout_geo_main)
        input_layout.addWidget(grp_geo)
        
        # 3. Cerramiento
        grp_enc = QGroupBox("3. Cerramiento")
        l_enc = QVBoxLayout()
        self.combo_enclosure = QComboBox()
        self.combo_enclosure.addItems(["Parcialmente Cerrado", "Cerrado", "Abierto"])
        l_enc.addWidget(self.combo_enclosure)
        grp_enc.setLayout(l_enc)
        input_layout.addWidget(grp_enc)

        # Botones
        self.btn_calculate = QPushButton("CALCULAR CARGAS")
        self.btn_calculate.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        input_layout.addWidget(self.btn_calculate)
        
        self.btn_pdf = QPushButton("Exportar PDF")
        input_layout.addWidget(self.btn_pdf)
        
        input_layout.addStretch()

        # --- PANEL DERECHO ---
        self.tabs = QTabWidget()
        
        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 11pt;")
        self.tabs.addTab(self.txt_report, "Memoria de Cálculo")
        
        self.tab_gfx = QWidget()
        gfx_layout = QVBoxLayout(self.tab_gfx)
        
        hbox_ctrl = QHBoxLayout()
        self.radio_long = QRadioButton("Dirección Longitudinal (L)")
        self.radio_trans = QRadioButton("Dirección Transversal (B)")
        self.radio_long.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.radio_long)
        bg.addButton(self.radio_trans)
        hbox_ctrl.addWidget(QLabel("Vista:"))
        hbox_ctrl.addWidget(self.radio_long)
        hbox_ctrl.addWidget(self.radio_trans)
        hbox_ctrl.addStretch()
        gfx_layout.addLayout(hbox_ctrl)
        
        self.canvas_loads = MplCanvas(self, width=5, height=4)
        gfx_layout.addWidget(self.canvas_loads)
        
        self.tabs.addTab(self.tab_gfx, "Diagrama de Cargas")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(input_widget)
        splitter.addWidget(self.tabs)
        splitter.setSizes([350, 900])
        
        main_layout.addWidget(splitter)

    def get_inputs(self):
        return {
            'V': self.input_V.text(),
            'exposure': self.combo_exp.currentText(),
            'I': self.combo_I.currentText(),
            'h': self.input_h.text(),
            'L': self.input_L.text(),
            'B': self.input_B.text(),
            'theta': self.input_theta.text(),
            'enclosure': self.combo_enclosure.currentText()
        }

    def set_report(self, html_text):
        self.txt_report.setHtml(html_text)

    def show_error(self, msg):
        self.txt_report.setPlainText(f"ERROR: {msg}")