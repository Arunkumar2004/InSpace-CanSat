# graph_widget.py
# Graph UI using pyqtgraph for CanSat GCS
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super(GraphWidget, self).__init__(parent)

        self.layout = QVBoxLayout(self)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Sensor Data")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        self.layout.addWidget(self.canvas)

    def plot(self, x_data, y_data):
        self.ax.clear()
        self.ax.plot(x_data, y_data)
        self.ax.set_title("Sensor Data")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.canvas.draw()
