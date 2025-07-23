import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class SpectrumViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agilent 86140B Spectrum Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.canvas = FigureCanvas(plt.Figure())
        self.ax = self.canvas.figure.subplots()
        self.layout.addWidget(self.canvas)

        self.btn_acquire = QPushButton("스펙트럼 불러오기 및 저장")
        self.btn_acquire.clicked.connect(self.acquire_spectrum)
        self.layout.addWidget(self.btn_acquire)

    def acquire_spectrum(self):
        import pyvisa
        import pandas as pd

        rm = pyvisa.ResourceManager()
        try:
            osa = rm.open_resource('GPIB0::18::INSTR')
            osa.timeout = 10000
            print("Device ID:", osa.query("*IDN?"))

            osa.write(":TRACe:DATA:Y?")
            data_str = osa.read()
        except Exception as e:
            QMessageBox.critical(self, "GPIB 연결 실패", f"GPIB 장치에 연결할 수 없습니다.\n\n오류 내용:\n{e}")
            return

        intensities = list(map(float, data_str.strip().split(',')))
        start_wavelength = float(osa.query(":SENSE:WAVELENGTH:START?")) * 1e9
        stop_wavelength = float(osa.query(":SENSE:WAVELENGTH:STOP?")) * 1e9
        num_points = len(intensities)

        wavelengths = [start_wavelength + i * (stop_wavelength - start_wavelength) / (num_points - 1)
                       for i in range(num_points)]

        df = pd.DataFrame({
            'Wavelength (nm)': wavelengths,
            'Power (dBm)': intensities
        })

        path, _ = QFileDialog.getSaveFileName(self, "CSV 저장", "agilent_86140b_trace.csv", "CSV Files (*.csv)")
        if path:
            df.to_csv(path, index=False)
            QMessageBox.information(self, "저장 완료", f"다음 위치에 저장됨:\n{path}")

        self.ax.clear()
        self.ax.plot(wavelengths, intensities)
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Power (dBm)")
        self.ax.set_title("Agilent 86140B Spectrum")
        self.canvas.draw()

if __name__ == "__main__":
    import pyvisa
    from PyQt5.QtWidgets import QApplication, QMessageBox
    try:
        rm = pyvisa.ResourceManager()
        osa = rm.open_resource('GPIB0::22::INSTR')
        osa.timeout = 10000
        osa.query("*IDN?")
    except Exception as e:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "GPIB 연결 실패", f"GPIB 장치에 연결할 수 없습니다.\n\n오류 내용:\n{e}")
        sys.exit(1)
    app = QApplication(sys.argv)
    viewer = SpectrumViewer()
    viewer.show()
    sys.exit(app.exec_())