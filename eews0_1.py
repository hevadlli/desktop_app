from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from obspy.clients.seedlink.easyseedlink import create_client
from PyQt5 import QtCore, QtGui, QtWidgets
from obspy import UTCDateTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1115, 594)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 1111, 601))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setAccessibleName("")
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1115, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.live_plot_widget = SeismicApp()
        self.live_plot_widget.start_seismic_thread()
        self.layout = QVBoxLayout(self.tab)
        self.layout.addWidget(self.live_plot_widget)

        # Add start and stop buttons
        self.start_button = QPushButton("Start", self.tab)
        self.start_button.setGeometry(QtCore.QRect(20, 20, 75, 23))
        self.stop_button = QPushButton("Stop", self.tab)
        self.stop_button.setGeometry(QtCore.QRect(100, 20, 75, 23))

        # Connect buttons to functions
        self.start_button.clicked.connect(self.live_plot_widget.start_seismic_thread)
        self.stop_button.clicked.connect(self.live_plot_widget.stop_seismic_thread)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Enabled"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Disabled"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))

class SeismicThread(QThread):
    data_received = pyqtSignal(object)

    def run(self):
        client = create_client('geofon.gfz-potsdam.de', self.data_handle)
        client.select_stream('GE', 'SMRI', 'SHZ')
        client.select_stream('GE', 'UGM', 'SHZ')
        client.run()


    def data_handle(self, trace):
        self.data_received.emit(trace)


class LivePlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def update_data(self, trace):
        if trace.stats.station == 'UGM':
            self.ax1.plot(trace.times('matplotlib'), trace.data, 'k')
            self.ax1.xaxis_date()
            self.figure.autofmt_xdate()
            # Set x-axis limits
            self.ax1.set_xlim(UTCDateTime()-600, UTCDateTime())

        elif trace.stats.station == 'SMRI':
            self.ax2.plot(trace.times('matplotlib'), trace.data, 'k')
            self.ax2.xaxis_date()
            self.figure.autofmt_xdate()
            # Set x-axis limits
            self.ax2.set_xlim(UTCDateTime()-600, UTCDateTime())

        self.canvas.draw()


class SeismicApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = LivePlotWidget()
        self.setCentralWidget(self.central_widget)

        self.seismic_thread = SeismicThread()
        self.seismic_thread.data_received.connect(
            self.central_widget.update_data)

    def start_seismic_thread(self):
        self.seismic_thread.start()

    def stop_seismic_thread(self):
        self.seismic_thread.terminate()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())
