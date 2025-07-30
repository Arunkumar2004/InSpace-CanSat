# main_window.py
# PyQt window setup for CanSat GCS
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from gui.toolbar import ToolBar
from gui.graph_widget import GraphWidget
from gui.map_widget import MapWidget
from gui.table_widget import TableWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CanSat GCS")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.toolbar = ToolBar(self)
        self.addToolBar(self.toolbar)

        self.graph_widget = GraphWidget()
        self.map_widget = MapWidget()
        self.table_widget = TableWidget()

        self.layout.addWidget(self.graph_widget)
        self.layout.addWidget(self.map_widget)
        self.layout.addWidget(self.table_widget)
        self.setLayout(self.layout)