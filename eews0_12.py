import io
from obspy.core.utcdatetime import UTCDateTime
from obspy import read
from obspy import Stream, UTCDateTime
from obspy.signal.trigger import recursive_sta_lta, trigger_onset
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QComboBox, QHBoxLayout
                             )
from obspy.clients.seedlink.easyseedlink import create_client
from obspy import UTCDateTime, Stream, read
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from obspy.signal.trigger import recursive_sta_lta
import sys
import json
import numpy as np

start = True
data_array = []


class Ui_MainWindow(object):
    dataChanged = pyqtSignal()

    def setupUi(self, MainWindow):
        self.data_array = data_array
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 1820, 950))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)

        self.setupTabWidget(MainWindow)

    def setupTabWidget(self, MainWindow):
        self.start_button = QPushButton("Start", self.tab)
        self.stop_button = QPushButton("Stop", self.tab)
        self.add_station_button = QPushButton("Add Station", self.tab)
        self.remove_station_button = QPushButton("Remove Station", self.tab)

        self.start_button.clicked.connect(self.toggleStatusOn)
        self.stop_button.clicked.connect(self.toggleStatusOff)
        self.add_station_button.clicked.connect(self.add_station_dialog)
        self.remove_station_button.clicked.connect(self.remove_station_dialog)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.add_station_button)
        self.button_layout.addWidget(self.remove_station_button)

        self.live_plot_widget = SeismicApp(data_array)
        self.live_plot_widget.start_seismic_thread()

        self.layout = QVBoxLayout(self.tab)
        self.layout.addLayout(self.button_layout)
        self.layout.addWidget(self.live_plot_widget)

        MainWindow.setWindowTitle("Seismic Data Viewer")

    def toggleStatusOn(self):
        global start
        start = True

    def toggleStatusOff(self):
        global start
        start = False

    def updateUI(self):
        self.clearLayout(self.layout)
        self.setupTabWidget(MainWindow)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def add_station_dialog(self):
        dialog = AddStationDialog("Add Station")
        if dialog.exec_():
            server = list(dialog.server_options.keys())[
                dialog.DropdownServer.currentIndex()]
            network = dialog.networkLineEdit.text()
            station = dialog.stationLineEdit.text()
            location = dialog.DropdownLoc.currentText()
            channel = dialog.channelLineEdit.text()
            data_array.append({"server": server, "network": network,
                              "station": station, "location": location, "channel": channel})
            with open('data_array.json', 'w') as file:
                json.dump(data_array, file)
            self.updateUI()

    def remove_station_dialog(self):
        dialog = RemoveStationDialog("Remove Station", self.data_array)
        if dialog.exec_():
            network = dialog.DropdownNetwork.currentText()
            station = dialog.DropdownStation.currentText()
            channel = dialog.DropdownChannel.currentText()
            for i, data in enumerate(self.data_array):
                if data["network"] == network and data["station"] == station and data["channel"] == channel:
                    del self.data_array[i]
                    break
            with open('data_array.json', 'w') as file:
                json.dump(self.data_array, file)
            self.updateUI()


class AddStationDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        self.server_options = {"geofon.gfz-potsdam.de": "Geofon",
                               "rtserve.iris.washington.edu": "IRIS", "172.19.3.65": "BMKG"}
        self.location_options = {"": "", "00": "00"}

        layout = QFormLayout(self)
        self.DropdownServer = QComboBox()
        self.DropdownServer.addItems(self.server_options.values())
        layout.addRow("Server:", self.DropdownServer)
        self.networkLineEdit = QLineEdit()
        layout.addRow("Network:", self.networkLineEdit)
        self.stationLineEdit = QLineEdit()
        layout.addRow("Station:", self.stationLineEdit)
        self.DropdownLoc = QComboBox()
        self.DropdownLoc.addItems(self.location_options.keys())
        layout.addRow("Location:", self.DropdownLoc)
        self.channelLineEdit = QLineEdit()
        layout.addRow("Channel:", self.channelLineEdit)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)


class RemoveStationDialog(QDialog):
    def __init__(self, title, data_array, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.data_array = data_array
        self.network = ""
        self.station = ""
        self.channel = ""

        layout = QFormLayout(self)
        self.DropdownNetwork = QComboBox()
        self.DropdownStation = QComboBox()
        self.DropdownChannel = QComboBox()

        layout.addRow("Network:", self.DropdownNetwork)
        layout.addRow("Station:", self.DropdownStation)
        layout.addRow("Channel:", self.DropdownChannel)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.DropdownNetwork.currentIndexChanged.connect(
            self.update_stations_and_channels)
        self.update_combobox_items()
        self.resize(300, 150)

    def update_combobox_items(self):
        added_network = set()

        self.DropdownNetwork.clear()
        self.DropdownStation.clear()
        self.DropdownChannel.clear()

        for data in self.data_array:
            network_name = data["network"]
            if network_name not in added_network:
                self.DropdownNetwork.addItem(network_name)
                added_network.add(network_name)

    def update_stations_and_channels(self):
        selected_network = self.DropdownNetwork.currentText()

        available_stations = set()
        available_channels = set()

        self.DropdownStation.clear()
        self.DropdownChannel.clear()

        for data in self.data_array:
            if data["network"] == selected_network:
                available_stations.add(data["station"])
                available_channels.add(data["channel"])

        for station_name in available_stations:
            self.DropdownStation.addItem(station_name)

        for channel_name in available_channels:
            self.DropdownChannel.addItem(channel_name)


class SeismicThread(QThread):
    data_received = pyqtSignal(object)

    def __init__(self, server_address, data_array):
        super().__init__()
        self.server_address = server_address
        self.data_array = data_array

    def run(self):
        client = create_client(self.server_address, self.data_handle)
        for data in self.data_array:
            if self.server_address in data['server']:
                client.select_stream(
                    data["network"], data["station"], data["channel"])
        client.run()

    def data_handle(self, trace):
        self.data_received.emit(trace)


class LivePlotWidget(QWidget):
    def __init__(self, data_array):
        super().__init__()

        self.data_array = data_array
        self.figure, self.axes = plt.subplots(
            len(data_array), 1, figsize=(6, 6*len(data_array)), sharex=True)
        self.canvas = FigureCanvas(self.figure)

        self.merged_stream = Stream()
        self.first_trigger_found = False

        self.station_axes = {}

        self.setup_plots()
        self.setup_table()

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def setup_plots(self):
        for i, data in enumerate(self.data_array):
            ax = self.axes[i]
            station = data['station']
            network = data['network']
            location = data['location']
            channel = data["channel"]

            key = (station, network, location, channel)
            ax.plot([], [], 'k')
            self.station_axes[key] = ax

            ax.get_yaxis().set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['left'].set_visible(False)
            if i != len(self.data_array) - 1:
                ax.spines['bottom'].set_visible(False)
                ax.tick_params(bottom=False)

        for ax in self.axes:
            ax.xaxis_date()
            ax.figure.autofmt_xdate()

    def setup_table(self):
        for i, data in enumerate(self.data_array):
            ax = self.axes[i]
            station = data['station'].ljust(7)
            network = data['network'].ljust(7)
            location = data['location'].ljust(5)
            channel = data["channel"].ljust(7)

            if not location:
                location = '   '

            cell_text = [[station, network, location, channel]]
            table = ax.table(cellText=cell_text, loc='left',
                             edges='open', cellLoc='center')
            table.auto_set_column_width(col=list(range(len(cell_text[0]))))
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 1.5)

    def update_data(self, trace):
        current_time = UTCDateTime()

        if current_time - self.last_refresh_time >= 120:
            self.merged_stream.clear()
            self.last_refresh_time = current_time

        self.merged_stream.append(trace)
        self.merged_stream = self.merged_stream.merge(method=0)

        for trace in self.merged_stream:
            station = trace.stats.station
            network = trace.stats.network
            location = trace.stats.location
            channel = trace.stats.channel
            key = (station, network, location, channel)
            ax = self.station_axes[key]

            trace_id = trace.id
            split_trace = trace_id.split(".")
            if split_trace[2] == "00" or split_trace[2] == "":
                tra = trace.copy()

                corners = 2
                freq_min = 1
                freq_max = 10
                sampling_rate = tra.stats.sampling_rate
                max_f_max = 0.9 * (sampling_rate / 2)
                freq_max = min(freq_max, max_f_max)
                corners = 2

                tra.data = tra.data - np.nanmean(tra.data)
                tra.filter("bandpass", freqmin=freq_min,
                           freqmax=freq_max, corners=corners, zerophase=True)

                stalta = recursive_sta_lta(tra.data, int(
                    1 * tra.stats.sampling_rate), int(24 * tra.stats.sampling_rate))
                triggers = trigger_onset(stalta, 5, 0.3)

                for trigger in enumerate(triggers):
                    if not self.first_trigger_found:
                        self.first_trigger_found = True
                        continue

                    ax.axvline(x=tra.times('matplotlib')
                               [trigger][0], color='r')

                ax.plot(tra.times('matplotlib'), tra.data, 'k')
                ax.set_xlim(UTCDateTime() - 360, UTCDateTime())

                if start:
                    ax.figure.canvas.draw()


class SeismicApp(QMainWindow):
    def __init__(self, data_array):
        super().__init__()

        self.central_widget = LivePlotWidget(data_array)
        self.setCentralWidget(self.central_widget)

        self.seismic_threads = []
        for server_address in ["geofon.gfz-potsdam.de", "172.19.3.65", "rtserve.iris.washington.edu"]:
            thread = SeismicThread(server_address, data_array)
            thread.data_received.connect(self.central_widget.update_data)
            self.seismic_threads.append(thread)

    def start_seismic_thread(self):
        for thread in self.seismic_threads:
            thread.start()

    def stop_seismic_thread(self):
        for thread in self.seismic_threads:
            thread.terminate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open('data_array.json', 'r') as file:
        data_array = json.load(file)

    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    MainWindow.show()

    sys.exit(app.exec_())
