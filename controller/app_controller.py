from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QFileDialog
from model.wind_logic import WindASCE705

class AppController:
    def __init__(self, view):
        self.view = view
        self.model = WindASCE705()
        self.cached_results = None
        
        # Conexiones
        self.view.btn_calculate.clicked.connect(self.run_calculation)
        self.view.btn_pdf.clicked.connect(self.export_pdf)
        self.view.radio_long.toggled.connect(self.update_plots)
        self.view.radio_trans.toggled.connect(self.update_plots)

        # Cálculo inicial
        self.run_calculation()

    def run_calculation(self):
        try:
            inputs = self.view.get_inputs()
            self.cached_results = self.model.calculate(inputs)
            # Generar reporte HTML
            self.view.set_report(self.model.generate_report())
            # Actualizar gráficos
            self.update_plots()
        except ValueError as e:
            self.view.show_error(str(e))

    def update_plots(self):
        if not self.cached_results: return
        
        # 1. Determinar qué set de datos usar (Longitudinal o Transversal)
        if self.view.radio_long.isChecked():
            data_key = 'long'
            # En vista longitudinal, el ancho visual es L
            width_frame = float(self.view.input_L.text())
        else:
            data_key = 'trans'
            # En vista transversal, el ancho visual es B
            width_frame = float(self.view.input_B.text())
            
        rows = self.cached_results[data_key]
        
        # 2. Función auxiliar para extraer la presión de la lista de filas
        def get_p(search_term):
            for r in rows:
                # Usamos 'in' para que coincida aunque el nombre tenga "(Windward)"
                if search_term in r['elem']:
                    # CORRECCIÓN AQUÍ: Usamos la clave 'p_pos' que define wind_logic.py
                    return r['p_pos'] 
            return 0.0

        # 3. Mapear datos para el gráfico
        # Buscamos por palabras clave que coincidan con los nombres en wind_logic.py
        loads_summary = {
            'p_ww': get_p('Pared Barlovento'), 
            'p_lw': get_p('Pared Sotavento'),
            'p_roof_ww': get_p('Techo Barlovento'),
            'p_roof_lw': get_p('Techo Sotavento')
        }
        
        h = float(self.view.input_h.text())
        theta = float(self.view.input_theta.text())

        # 4. Dibujar
        self.view.canvas_loads.plot_frame_load(
            h_wall=h,
            width=width_frame,
            theta=theta,
            loads=loads_summary,
            title=f"Cargas de Viento - {data_key.upper()}"
        )

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self.view, "Guardar Reporte", "CalculoViento.pdf", "*.pdf")
        if filename:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            # Imprimir el contenido HTML del QTextEdit
            self.view.txt_report.print_(printer)