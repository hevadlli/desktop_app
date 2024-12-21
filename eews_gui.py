import sys
import time
import pandas as pd
from obspy import UTCDateTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QSizePolicy, QHBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QWidget, QGridLayout, QHeaderView
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal, QObject, Qt, QUrl, QThread
from PyQt5.QtGui import QFont
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from math import radians, sin, cos, atan2, sqrt, degrees
import subprocess

class FileWatcher(QObject, FileSystemEventHandler):
    file_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def on_modified(self, event):
        if event.src_path.endswith('earthquake.txt') or event.src_path.endswith('s_arrival.csv'):
            self.file_changed.emit()

class EarthquakeData:
    def __init__(self, eq_file, arrival_file):
        self.eq_file = eq_file
        self.arrival_file = arrival_file
    
    def read_latest_earthquake(self):
        df = pd.read_csv(self.eq_file)
        latest_earthquake = df.iloc[-1]
        return {
            'origin_time': UTCDateTime(latest_earthquake['origin_time']),
            'latitude': latest_earthquake['latitude'],
            'longitude': latest_earthquake['longitude'],
            'depth': latest_earthquake['depth'],
            'magnitudo': latest_earthquake['magnitudo']
        }
    
    def read_s_arrival_times(self):
        return pd.read_csv(self.arrival_file)
    
# class ScriptRunner(QThread):
#     update_status = pyqtSignal(str)

#     def __init__(self):
#         super().__init__()
#         self.running = False

#     def run(self):
#         self.running = True
#         while self.running:
#             self.process_stop = subprocess.Popen(['nohup', '--', './eews_stop.sh'])
#             self.process_start = subprocess.Popen(['nohup', '--', './eews_start.sh'])
#             #self.update_status.emit('Status: Connected')
#             time.sleep(30)

#     def stop(self):
#         self.running = False
#         self.process_stop = subprocess.Popen(['nohup', '--', './eews_stop.sh'])
#         #self.update_status.emit('Status: Not Connected')

class MapPlotter:
    def __init__(self, latitude=0, longitude=0):
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'
        attr = ('Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC')
        self.map = folium.Map(location=[latitude, longitude], zoom_control=False, tiles=tiles, attr=attr, zoom_start=7)
    
    def add_circle(self, m, location, radius, opacity):
        folium.Circle(
            location=location,
            radius=radius,
            color='red',
            fill=False,
            opacity=opacity
        ).add_to(m)

    
    def plot_earthquake(self, latitude, longitude, magnitudo):        
        # folium.Marker(
        #     location=[latitude, longitude],
        #     popup=f"magnitudo: {magnitudo}",
        #     icon=folium.Icon(color="red", icon="info-sign")
        # ).add_to(self.map)
                # Menambahkan Marker dengan icon di tengah lingkaran
        icon_html = '''
        <div style="
            position: absolute;
            transform: translate(-25%, -30%);
            font-size: 24px;
            color: #ff8100;
        ">&#9733;</div>
        '''
        folium.Marker(
            location=[latitude, longitude],
            icon=folium.DivIcon(html=icon_html)
        ).add_to(self.map)

        # Tambahkan lingkaran dengan opacity berbeda
        center = [latitude, longitude]
        radii_m = [200, 400, 600, 800, 1000]
        radii = [r*100 for r in radii_m]
        opacities = [1.0, 0.8, 0.6, 0.4, 0.2]

        for radius, opacity in zip(radii, opacities):
            self.add_circle(self.map, center, radius, opacity)

    def get_map(self):
        map_html = self.map._repr_html_()
        map_html = map_html.replace('<div style="', '<div style="margin-top: 25px; ')
        return map_html


    def set_initial_location(self, latitude, longitude):
        self.map.location = [latitude, longitude]

class EarthquakeApp(QMainWindow):
    def __init__(self, eq_data):
        super().__init__()
        self.eq_data = eq_data
        self.initUI()

        self.selected_city = None

        # Setup file watcher
        self.file_watcher = FileWatcher()
        self.file_watcher.file_changed.connect(self.update_all)
        self.observer = Observer()
        self.observer.schedule(self.file_watcher, '.', recursive=False)
        self.observer.start()

        # Setup script runner
        # self.script_runner = ScriptRunner()
        #self.script_runner.update_status.connect(self.update_connection_status)

    def initUI(self):
        # Set the background color to white
        self.setStyleSheet("background-color: white;")
        
        self.setWindowTitle('Earthquake Alert')
        self.setGeometry(100, 100, 1200, 800)
        
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        
        self.layout = QGridLayout(self.centralWidget)
        #self.layout.setColumnStretch(0, 1)  # Set kolom pertama dengan faktor perpanjangan 2
        #self.layout.setColumnStretch(1, 1)  # Set kolom kedua dengan faktor perpanjangan 1

        self.layout.setContentsMargins(10, 5, 10, 10)
        
        """ # Current time label
        self.current_time_label = QLabel(self)
        self.current_time_label.setFont(QFont("Noto Mono", 30))  
        self.current_time_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_time_label, 0, 2, 1, 2) """

        # Current time label
        self.current_time_label = QLabel("Current time:", self)
        self.current_time_label.setFont(QFont("Noto Mono", 16))
        self.current_time_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.current_time_label, 2, 2, 1, 2)  # Update grid position

        # Timer to update current time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # Earthquake Information
        self.earthquake_info_label = QLabel(self)
        eq_font = QFont("Noto Mono", 16)
        eq_font.setLetterSpacing(QFont.PercentageSpacing,110)
        self.earthquake_info_label.setFont(eq_font)
        self.layout.addWidget(self.earthquake_info_label, 0, 0, 1, 2)
        
        """ # City selection and countdown
        self.city_label = QLabel('Select City:', self)
        self.city_label.setFont(QFont("Noto Mono", 16))
        self.layout.addWidget(self.city_label, 2, 0)
        
        self.city_combo = QComboBox(self)
        self.city_combo.addItems(self.eq_data.read_s_arrival_times()['City'].tolist())
        self.layout.addWidget(self.city_combo, 2, 1)
        
        self.countdown_label = QLabel('S-wave arrival time:', self)
        self.countdown_label.setFont(QFont("Noto Mono", 16)) 
        self.layout.addWidget(self.countdown_label, 2, 2) """
        
        # City selection and countdown
        self.city_label = QLabel('Select City:', self)
        self.city_label.setFont(QFont("Noto Mono", 16))
        self.layout.addWidget(self.city_label, 2, 0)  # Update grid position

        self.city_combo = QComboBox(self)
                # Set stylesheet
        self.city_combo.setStyleSheet("""
            QComboBox {
                background-color: white; /* Background color of the combobox */
                color: black;             /* Text color of the combobox */
            }
            QComboBox QAbstractItemView {
                background-color: white;  /* Background color of the item view (list) */
                color: black;            /* Text color of the item view (list) */
            }
        """)
        self.city_combo.addItems(self.eq_data.read_s_arrival_times()['City'].tolist())
        self.city_combo.currentIndexChanged.connect(self.city_selection_changed)
        self.layout.addWidget(self.city_combo, 2, 1)  # Update grid position

        self.countdown_label = QLabel('S-wave arrival time:\n', self)
        self.countdown_label.setFont(QFont("Noto Mono", 16))
        self.countdown_label.setContentsMargins(0, 25, 0, 0)
        self.layout.addWidget(self.countdown_label, 0, 2, 1, 2)  # Update grid position
        
        # Map
        latest_eq = self.eq_data.read_latest_earthquake()
        self.map_plotter = MapPlotter(latitude=latest_eq['latitude'], longitude=latest_eq['longitude'])
        self.map_view = QWebEngineView()
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.map_view.setHtml(self.map_plotter.get_map(), baseUrl=QUrl.fromLocalFile(os.getcwd()))

        self.update_map()
        self.layout.addWidget(self.map_view, 3, 0, 2, 2)
        
        # Earthquake table
        self.eq_table = QTableWidget(self)
        self.eq_table.setColumnCount(5)
        self.eq_table.setHorizontalHeaderLabels(['Origin Time', 'Latitude', 'Longitude', 'Depth', 'Magnitude'])
        #self.eq_table.horizontalHeader().setStretchLastSection(True)
        self.eq_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.eq_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.update_eq_table()
        self.layout.addWidget(self.eq_table, 3, 2, 2, 2)

        self.update_earthquake_info()

        # # Start and Stop Buttons
        # self.start_button = QPushButton('Start', self)
        # self.start_button.clicked.connect(self.start_script)
        # self.layout.addWidget(self.start_button, 5, 0)

        # self.stop_button = QPushButton('Stop', self)
        # self.stop_button.clicked.connect(self.stop_script)
        # self.layout.addWidget(self.stop_button, 5, 1)

        # # Connection Status
        # self.connection_status_label = QLabel("Status: Not Connected", self)
        # self.connection_status_label.setFont(QFont("Noto Mono", 16))
        # self.layout.addWidget(self.connection_status_label, 5, 2, 1, 2)
        
    def update_time(self):
        current_time = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        self.current_time_label.setText(f"Current time: {current_time} WIB")
        
        # Update countdown
        selected_city = self.city_combo.currentText()
        arrival_times = self.eq_data.read_s_arrival_times()
        city_data = arrival_times[arrival_times['City'] == selected_city].iloc[0]
        s_arrival_time = UTCDateTime(city_data['utc arrival'])
        current_utc_time = UTCDateTime()
        countdown = s_arrival_time - current_utc_time
        countdown = round(countdown)
        if countdown < 0:
            countdown = 0
        #self.countdown_label.setText(f"S-wave arrival in {selected_city}: {countdown} seconds")
        
        # Set text with different font sizes
        countdown_text = f"<span style='font-size: 22px;font-family: 'Noto Mono', monospace;'>S-wave arrival in {selected_city}:</span><br>"
        countdown_text += f"<span style='font-size: 22px;'>{self.time_to_str(s_arrival_time)}</span><br><br>"
        countdown_text += f"<span style='font-size: 40px; text-align: center;white-space: pre;'>         {countdown} seconds</span><br><br><br>"
        self.countdown_label.setText(countdown_text)
       
    def update_map(self):
        latest_eq = self.eq_data.read_latest_earthquake()
        self.map_plotter = MapPlotter(latitude=latest_eq['latitude'], longitude=latest_eq['longitude'])
        self.map_plotter.plot_earthquake(
            latest_eq['latitude'], latest_eq['longitude'], latest_eq['magnitudo']
        )
        self.map_view.setHtml(self.map_plotter.get_map())

    def time_to_str(self, utc): #wib
        origin_time_wib = utc + 7*60*60
        year = origin_time_wib.year
        month = origin_time_wib.month
        day = origin_time_wib.day
        hr = origin_time_wib.hour
        mn = origin_time_wib.minute
        sc = origin_time_wib.second

        month_name = ("Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        )

        month = month_name[month - 1]

        formatted_time = f'{day}-{month}-{year} {hr:02d}:{mn:02d}:{sc:02d} WIB'
        return formatted_time
        
    def update_eq_table(self):
        eq_df = pd.read_csv(self.eq_data.eq_file)        
        eq_df['origin_time'] = eq_df['origin_time'].apply(UTCDateTime)
        self.eq_table.setRowCount(len(eq_df))
        for index, row in eq_df.iterrows():
            self.eq_table.setItem(len(eq_df)-1-index, 0, QTableWidgetItem(str(self.time_to_str(row['origin_time']))))
            self.eq_table.setItem(len(eq_df)-1-index, 1, QTableWidgetItem(str(row['latitude'])))
            self.eq_table.setItem(len(eq_df)-1-index, 2, QTableWidgetItem(str(row['longitude'])))
            self.eq_table.setItem(len(eq_df)-1-index, 3, QTableWidgetItem(str(row['depth'])))
            self.eq_table.setItem(len(eq_df)-1-index, 4, QTableWidgetItem(str(row['magnitudo'])))

        self.eq_table.setColumnWidth(0, 220)
        self.eq_table.setColumnWidth(1, 90)
        self.eq_table.setColumnWidth(2, 90)
        self.eq_table.setColumnWidth(3, 90)
        self.eq_table.setColumnWidth(4, 90) 

    def hypo_dist(self, depth, jarak_horizontal):
        return sqrt(depth**2+jarak_horizontal**2)
    
    def haversine(self, coord1, coord2):
        # radius of the Earth in km
        R = 6371.0
    
        # convert coordinates from degrees to radians
        lat1, lon1 = radians(coord1[0]), radians(coord1[1])
        lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    
        # differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1
    
        # haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
        # calculate the distance
        distance = R * c
        return distance

    def azimuth(self, coord1, coord2):
        lat1, lon1 = radians(coord1[0]), radians(coord1[1])
        lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    
        # differences in coordinates
        dlon = lon2 - lon1
    
        # calculate azimuth
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        initial_bearing = atan2(x, y)
        initial_bearing = degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
    
        return compass_bearing

    def nearest_city(self, lat, long):
        cities = pd.read_csv('cities.csv', sep=',', skipinitialspace=True)
        distances = []
        for index, row in cities.iterrows():
            city = row['City']
            lat_city = row['Latitude']
            long_city = row['Longitude']
            distance = self.haversine((lat, long), (lat_city, long_city))
            azimuth_val = self.azimuth((lat, long), (lat_city, long_city))
            distances.append((city, distance, azimuth_val))
        distances.sort(key=lambda x: x[1])
        nearest = distances[0][0]
        distance = distances[0][1]
        azimuth_val = distances[0][2]
        return (nearest, distance, azimuth_val)

    def back_azimuth_func(self, azimuth):
        back_azimuth = (azimuth + 180) % 360
        return back_azimuth
    
    def direction_func(self, back_azimuth):
        if back_azimuth < 360:
            if back_azimuth < 270:
                if back_azimuth < 180:
                    if back_azimuth < 90:
                        direction = 'Timur Laut'
                    else:
                        direction = 'Tenggara'
                else:
                    direction = 'Barat Daya'
            else:
                direction = 'Barat Laut'
        return direction
    
    def update_earthquake_info(self):
        latest_eq = self.eq_data.read_latest_earthquake()
        city, distance, azimuth_val = self.nearest_city(latest_eq['latitude'], latest_eq['longitude'])
        back_azimuth = self.back_azimuth_func(azimuth_val)
        direction = self.direction_func(back_azimuth)
        # info_text = (
        #     f"Origin Time: {self.time_to_str(latest_eq['origin_time'])}\n"
        #     f"Latitude: {latest_eq['latitude']}\n"
        #     f"Longitude: {latest_eq['longitude']}\n"
        #     f"Depth: {latest_eq['depth']} km\n"
        #     f"Magnitude: {latest_eq['magnitudo']}\n"
        #     f"Location: {round(distance)} km {direction} {city.upper()}"
        # )
        blank = "&nbsp;"
        info_text = (
            f"Origin Time   : {self.time_to_str(latest_eq['origin_time'])}<br>"
            f"Magnitude     : {latest_eq['magnitudo']}<br>"
            f"Latitude      : {latest_eq['latitude']}<br>"
            f"Longitude     : {latest_eq['longitude']}<br>"
            f"Depth         : {latest_eq['depth']} km<br>"
            f"Location      : {round(distance)} km {direction} {city.upper()}"
        )

        # Use HTML to set the text with line spacing
        html_text = f"<div style='line-height: 1.1; white-space: pre-wrap; tab-size: 4em;'>{info_text}</div>"
        self.earthquake_info_label.setText(html_text)
        #self.earthquake_info_label.setText(info_text)

    # def update_connection_status(self, status):
    #     if status == "Connected":
    #         self.connection_status_label.setText('Status: Connected')
    #     elif status == "Not Connected":
    #         self.connection_status_label.setText('Status: Not Connected')

    def city_selection_changed(self, index):
        # Fungsi ini akan dipanggil ketika pilihan kota berubah
        if index >= 0:
            self.selected_city = self.city_combo.currentText()

    def update_all(self):
        # Simpan pilihan kota saat ini sebelum pembaruan
        current_city = self.selected_city

        # Update data dari file yang diawasi
        self.city_combo.clear()
        self.city_combo.addItems(self.eq_data.read_s_arrival_times()['City'].tolist())

        # Get the list of current items in the QComboBox
        items = [self.city_combo.itemText(i) for i in range(self.city_combo.count())]

        # Set pilihan kota ke yang sebelumnya dipilih (jika masih tersedia)
        if current_city is not None and current_city in items:
            index = self.city_combo.findText(current_city)
            self.city_combo.setCurrentIndex(index)
        else:
            # Jika tidak ada atau kota sebelumnya tidak tersedia, atur ke indeks 0
            self.selected_city = self.city_combo.itemText(0)

        self.update_map()
        self.update_eq_table()
        self.update_earthquake_info()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_map()
    
    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        event.accept()

if __name__ == '__main__':
    eq_file = 'earthquake.txt'
    arrival_file = 's_arrival.csv'
    
    eq_data = EarthquakeData(eq_file, arrival_file)
    
    app = QApplication(sys.argv)
    ex = EarthquakeApp(eq_data)
    ex.show()
    sys.exit(app.exec_())
