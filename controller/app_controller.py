from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from model.wind_logic import WindASCE705

class AppController:
    def __init__(self, view):
        self.view = view
        self.model = WindASCE705()
        self.cached_results = None
        
        # Conexiones
        self.view.btn_calculate.clicked.connect(self.run_calculation)
        self.view.btn_pdf.clicked.connect(self.export_pdf)
        
        # Cambio de gráfico dinámico
        self.view.radio_long.toggled.connect(self.update_plots)
        self.view.radio_trans.toggled.connect(self.update_plots)

        self.run_calculation()

    def run_calculation(self):
        try:
            raw = self.view.get_inputs()
            self.cached_results = self.model.calculate(raw)
            self.view.set_report(self.model.generate_report())
            self.update_plots()
            
        except ValueError as e:
            self.view.show_error(str(e))

    def update_plots(self):
        if not self.cached_results: return
        
        r = self.cached_results
        
        # Determinar qué dirección mostrar
        if self.view.radio_long.isChecked():
            # Dirección Longitudinal (L es el ancho del marco en el dibujo 2D lateral)
            # NOTA: En analisis 2D, si viento va en L, vemos el perfil de longitud L.
            data_load = r['long']
            width_frame = r['L']
            title = "Dirección Longitudinal (Viento // L)"
        else:
            # Dirección Transversal
            data_load = r['trans']
            width_frame = r['B']
            title = "Dirección Transversal (Viento // B)"
            
        self.view.canvas_loads.plot_frame_load(
            h_wall=r['h'],
            width=width_frame,
            theta=r['theta'],
            loads=data_load,
            title=title
        )

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self.view, "Guardar PDF", "Reporte.pdf", "*.pdf")
        if filename:
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.view.txt_report.print_(printer)