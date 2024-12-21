import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from obspy.clients.seedlink.easyseedlink import create_client
from obspy import UTCDateTime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SeismicThread(QThread):
    data_received = pyqtSignal(object)

    def run(self):
        client = create_client('172.19.3.150', self.data_handle)
        client.select_stream('IA', 'SMRI', 'SHZ')
        client.select_stream('IA', 'UGM', 'SHZ')
        client.run()

    def data_handle(self, trace):
        self.data_received.emit(trace)


class LivePlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.trace_data = []
        self.trace_time = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # Update every 1000 milliseconds (1 second)

    # @pyqtSlot(object)
    def update_data(self, trace):
        if trace.stats.station == 'UGM':
            # global merged_stream
            # # Add the received trace to the merged_stream
            # merged_stream += trace

            fig = plt.figure(1)
            ax = plt.subplot(2, 1, 1)
            # ax.cla()
            ax.plot(trace.times('matplotlib'), trace.data, 'k')
            ax.xaxis_date()
            fig.autofmt_xdate()
            # Set x-axis limits
            ax.set_xlim(UTCDateTime()-60, UTCDateTime())

        elif trace.stats.station == 'SMRI':
            fig = plt.figure(1)
            ax1 = plt.subplot(2, 1, 2)
            # ax1.cla()
            ax1.plot(trace.times('matplotlib'), trace.data, 'k')
            ax1.xaxis_date()
            fig.autofmt_xdate()
            # Set x-axis limits
            ax1.set_xlim(UTCDateTime()-60, UTCDateTime())

        plt.draw()
        # plt.pause(0.001)
        # self.trace_data.append(trace.data)
        # self.trace_time.append(trace.times('matplotlib'))
        # # print(self.trace_data)
        # self.update_plot()
        # self.ax.set_xlabel('Time (s)')
        # self.ax.set_ylabel('Amplitude')
        # self.ax.set_title('Seismic Data')
        # self.canvas.draw()

    def update_plot(self):
        # self.ax.clear()
        # self.ax.cla()
        for i in range(len(self.trace_data)):
            self.ax.plot(self.trace_time[i], self.trace_data[i], 'k')

        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_title('Seismic Data')
        self.canvas.draw()


class SeismicApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seismic Data Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = LivePlotWidget()
        self.setCentralWidget(self.central_widget)

        self.seismic_thread = SeismicThread()
        self.seismic_thread.data_received.connect(
            self.central_widget.update_data)

    def start_seismic_thread(self):
        self.seismic_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeismicApp()
    window.show()
    window.start_seismic_thread()  # Start the seismic thread
    sys.exit(app.exec_())
