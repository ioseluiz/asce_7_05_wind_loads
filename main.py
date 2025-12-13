import sys
from PyQt5.QtWidgets import QApplication
from view.main_window import MainWindow
from controller.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    
    # Estilo Fusion para look profesional
    app.setStyle('Fusion')
    
    window = MainWindow()
    controller = AppController(window)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()