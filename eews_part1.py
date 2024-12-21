import io
from obspy.core.utcdatetime import UTCDateTime
from obspy import read
from obspy import Stream, UTCDateTime
from obspy.signal.trigger import recursive_sta_lta, trigger_onset
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
                             QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QComboBox, QHBoxLayout
                             )
from obspy.clients.seedlink.easyseedlink import create_client
from obspy.clients.seedlink.seedlinkexception import SeedLinkException
from obspy import UTCDateTime, Stream, read
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from obspy.signal.trigger import recursive_sta_lta
import sys
import json
import numpy as np
import pandas as pd
import platform
import subprocess
import threading
import pygame
import time
import folium
import asyncio
from telegram import Bot
from math import radians, sin, cos, atan2, sqrt, degrees
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import subprocess
import os

start = True
data_array = []

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1180, 684)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("")
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout.addItem(spacerItem)
        self.Plot = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Plot.sizePolicy().hasHeightForWidth())
        self.Plot.setSizePolicy(sizePolicy)
        self.Plot.setMinimumSize(QtCore.QSize(800, 0))
        self.Plot.setObjectName("Plot")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.Plot)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout_2.addItem(spacerItem1)
        self.plot = QtWidgets.QWidget(self.Plot)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plot.sizePolicy().hasHeightForWidth())
        self.plot.setSizePolicy(sizePolicy)
        self.plot.setMinimumSize(QtCore.QSize(0, 600))
        self.plot.setObjectName("plot")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.plot)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2.addWidget(self.plot)
        self.horizontalLayout.addWidget(self.Plot)
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1180, 22))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        MainWindow.setMenuBar(self.menubar)
        self.Filter = QtWidgets.QAction(MainWindow)
        self.Filter.setObjectName("Filter")
        self.Maps = QtWidgets.QAction(MainWindow)
        self.Maps.setObjectName("Maps")
        self.menuMenu.addAction(self.Filter)
        self.menuMenu.addAction(self.Maps)
        self.menubar.addAction(self.menuMenu.menuAction())
        self.setupWidget(MainWindow)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.centralwidget.setStyleSheet("background-color: white;")
        
        self.Maps.triggered.connect(self.open_map_window)

    def setupWidget(self, MainWindow):
        # Assuming SeismicApp is a class that creates a seismic plot widget
        self.live_plot_widget = SeismicApp(data_array)
        self.live_plot_widget.start_seismic_thread()
        self.verticalLayout_3.addWidget(self.live_plot_widget)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.Filter.setText(_translate("MainWindow", "Filter"))
        self.Maps.setText(_translate("MainWindow", "Maps"))

    def open_map_window(self):
        self.map_thread = MapThread()
        self.map_thread.start()

class MapThread(QThread):
    def run(self):
        subprocess.run(["python3", "eews_gui.py"])

class SeismicThread(QThread):
    data_received = pyqtSignal(object)

    def __init__(self, server_address, data_array):
        super().__init__()
        self.server_address = server_address
        self.data_array = data_array

    def run(self):
        client = False
        connected = False
        while not connected:
            try:
                client = create_client(self.server_address, self.data_handle)
                connected = True
            
            except SeedLinkException as e:
                print(f"Koneksi ke server gagal: {e}")

            
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
        self.last_station_num = 0
        self.mpd = -1

        self.data_array = data_array
        self.figure, self.axes = plt.subplots(
            len(data_array), 1, figsize=(15, 15*len(data_array)), sharex=True)
        self.canvas = FigureCanvas(self.figure)

        self.merged_stream = Stream()
        self.first_trigger_skipped = False

        self.station_axes = {}
        self.data_axes = dict()
        self.last_refresh_time = UTCDateTime()

        self.sent_msg = 0
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
            station = data['station']
            network = data['network']
            location = data['location']
            channel = data["channel"]

            if not location:
                location = '  '

            cell_text = [[station, network, location, channel]]
            table = ax.table(cellText=cell_text, loc='left',
                             edges='open', cellLoc='center')
            table.auto_set_column_width(col=list(range(len(cell_text[0]))))

            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 1.5)

    # Fungsi untuk menghitung jarak hiposentral
    def hypo_dist(self, depth, jarak_horizontal):
        return sqrt(depth**2+jarak_horizontal**2)
    
    # Fungsi untuk menghitung jarak 2 titik di bumi
    def haversine(self, coord1, coord2):
        # radius of the Earth in km
        R = 6371.0 # km
    
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

    # Fungsi untuk menghitung azimuth dari satu titik ke titik lain
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

    # Fungsi untuk menghitung kota terdekat dari sebuah titik di bumi
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

    # Fungsi untuk menghitung back-azimuth
    def back_azimuth_func(self, azimuth):
        back_azimuth = (azimuth + 180) % 360
        return back_azimuth
    
    # Fungsi untuk menentukan arah berdasarkan sudut back-azimuth
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
    
    # Fungsi untuk menjalankan file audio di latar belakang
    def play_audio(self, file_path):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)

    # Fungsi mengubah format waktu menjadi UTCDateTime
    def string_to_utc_datetime(self, date_str, origin_str):
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:])
        hour = int(origin_str[:2])
        minute = int(origin_str[3:5])
        second = int(origin_str[6:8])
        microsecond = int(origin_str[9:]) * 10000

        return UTCDateTime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=microsecond)
    
    # Fungsi konversi format koordinat derajat-menit ke derajat
    def coordinate_conv(self, coor):
        derajat, menit = coor.split('-')

        derajat = float(derajat)
        menit = float(menit)

        return derajat + menit/60
    
    # Fungsi untuk mengambil nilai parameter gempa
    def eq_parameter(self, file_path, index):
        # Membaca file riwayat gempa dari file HYPO71.OUT
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Mengambil data dari setiap baris
        data = []
        line = lines[1]
        date = line[0:6]
        origin = line[7:17]
        lat = line[18:26]
        long = line[27:36]
        depth = line[37:43]
        mag = line[46:50]
        no = line[51:53]
        gap = line[54:57]
        dmin = line[58:62]
        rms = line[62:67]
        erh = line[69:72]
        erz = line[73:77]
        qm = line[78:80]
        data.append([date, origin, lat, long, depth, mag,
                        no, gap, dmin, rms, erh, erz, qm])

        # Penyesuaian format sesuai format input HYPO71
        data_gempa = pd.DataFrame(data, columns=[
                                  'DATE', 'ORIGIN', 'LAT', 'LONG', 'DEPTH', 'MAG', 'NO', 'GAP', 'DMIN', 'RMS', 'ERH', 'ERZ', 'QM'])
        
        data_gempa['LAT'] = data_gempa['LAT'].apply(self.coordinate_conv)
        data_gempa['LONG'] = data_gempa['LONG'].apply(self.coordinate_conv)
        data_gempa['LAT'] = data_gempa['LAT'].apply(lambda x: -1*x)
        data_gempa['ORIGIN'] = data_gempa['ORIGIN'].apply(
            lambda origin: f"{origin[:2]}:{origin[2:4]}:{origin[5:]}")
        data_gempa['ORIGIN'] = data_gempa['ORIGIN'].apply(
            lambda x: x.replace(' ', '0'))
        data_gempa['ORIGIN TIME'] = data_gempa.apply(
            lambda x: self.string_to_utc_datetime(x['DATE'], x['ORIGIN']), axis=1)
        data_gempa['DEPTH'] = data_gempa['DEPTH'].apply(float)

        # Parameter siap diambil nilainya
        origin_time = UTCDateTime(data_gempa.iloc[index]['ORIGIN TIME'])
        lat = data_gempa.iloc[index]['LAT']
        long = data_gempa.iloc[index]['LONG']
        depth = data_gempa.iloc[index]['DEPTH']

        return origin_time, lat, long, depth

    # Fungsi untuk mengirim pesan ke channel telgram
    async def send_message(self, msg):
        bot_token = '7199379819:AAGVybyveMVLK8J48u30xJb7bRYZAnx_6Hk' # @eews_mbkm_bmkg
        channel_id = '@eewsmbkm'

        bot = Bot(token=bot_token)

        # Kirim pesan ke channel
        await bot.send_message(chat_id=channel_id, text=msg)

    # Fungsi untuk menyimpan peta dari folium menjadi gambar .png
    def save_map_as_image(self):
        # Path ke geckodriver
        geckodriver_path = '/usr/bin/geckodriver'

        # Set opsi untuk Firefox
        options = Options()
        options.add_argument('--headless')  # Jalankan Firefox dalam mode headless

        # Inisialisasi WebDriver
        service = Service(executable_path=geckodriver_path)
        driver = webdriver.Firefox(service=service, options=options)

        # Atur ukuran jendela
        driver.set_window_size(600, 600)

        # Buka file HTML
        driver.get(f'file://{os.getcwd()}/peta_pulau_jawa.html')

        # Tunggu beberapa detik untuk memastikan peta ter-render
        time.sleep(5)

        # Ambil screenshot dan simpan sebagai gambar
        screenshot_path = 'map.png'
        driver.save_screenshot(screenshot_path)

        # Tutup browser
        driver.quit()

        return screenshot_path

    # Fungsi untuk mengirim gambar ke channel telegram
    async def send_image_to_telegram(self, image_path):
        # Informasi bot Telegram
        TELEGRAM_TOKEN = '7199379819:AAGVybyveMVLK8J48u30xJb7bRYZAnx_6Hk'
        CHAT_ID = '@eewsmbkm'
        # Inisialisasi bot
        bot = Bot(token=TELEGRAM_TOKEN)

        # Kirim gambar ke channel
        with open(image_path, 'rb') as image_file:
            await bot.send_photo(chat_id=CHAT_ID, photo=image_file)

    # Buat fungsi untuk menambahkan lingkaran dengan opacity yang berbeda
    def add_circle(self, m, location, radius, opacity):
        folium.Circle(
            location=location,
            radius=radius,
            color='red',
            fill=False,
            opacity=opacity
        ).add_to(m)
     

    # Fungsi estimasi magnitudo Pd
    # Coba-coba pake koefisien ugm dulu
    def mag_pd(self, peak, hypo_dist):
        a = 14.380685400419035 
        b = 1.644721476169526
        c = -2.5892085518901258

        m = np.log(peak)-a - c* np.log(hypo_dist)
        m /= b
        return m
    
    # Fungsi mendapatkan waktu tiba gelombang S di beberapa kota
    def estimate_arrival(self, cities_list="cities_coor.csv", eq_list="earthquake.txt"):
        df_cities = pd.read_csv(cities_list, sep=',', skipinitialspace=True)
        df_eq = pd.read_csv(eq_list, sep=',', skipinitialspace=True)
        last_row = df_eq.iloc[-1]

        # Mengambil data parameter gempa terakhir
        self.eq_OT = UTCDateTime(last_row['origin_time'])
        self.eq_lat = last_row['latitude']
        self.eq_long = last_row['longitude']
        self.eq_depth = last_row['depth']
        self.eq_mag = last_row['magnitudo']

        S_velocity = 4 #km/s, asumsi lapisan bumi adalah homogen

        for index, row in df_cities.iterrows():
            epi_distance = self.haversine([row['Latitude'], row['Longitude']], [self.eq_lat, self.eq_long])
            hypo_distance = self.hypo_dist(self.eq_depth, epi_distance)
            s_arrived = hypo_distance/S_velocity
            time_arrived = self.eq_OT+s_arrived
            df_cities.at[index, 'utc arrival'] = time_arrived
            df_cities.at[index, 'arrival'] = self.time_to_str(time_arrived)
        
        df_cities = df_cities.sort_values(by='utc arrival')

        df_cities.to_csv('s_arrival.csv', sep= ",", index=False)

        return df_cities
    
    def detect_triggers_threaded(self, ax, trace):
        current_time = UTCDateTime()

        # Menghapus kumpulan stream setelah 60 detik
        if current_time - self.last_refresh_time >= 60:
            del self.merged_stream
            self.merged_stream = Stream()

            self.last_refresh_time = current_time

        self.merged_stream.append(trace)
        self.merged_stream = self.merged_stream.merge(method=1, fill_value='interpolate', interpolation_samples=-1)

        for trace in self.merged_stream:
            station = trace.stats.station
            network = trace.stats.network
            location = trace.stats.location
            channel = trace.stats.channel
            key = (station, network, location, channel)
            ax = self.station_axes[key]

            tra = trace.copy()
            
            corners = 3
            freq_min = 4
            freq_max = 8
            sampling_rate = tra.stats.sampling_rate
            max_f_max = 0.9 * (sampling_rate / 2)
            freq_max = min(freq_max, max_f_max)
            
            tra.filter("bandpass",
                       freqmin=freq_min,
                       freqmax=freq_max,
                       corners=corners,
                       zerophase=True)

            station_trig = tra.stats.station

            stalta = recursive_sta_lta(tra.data, int(
                0.5 * sampling_rate), int(10 * sampling_rate))
            
            # Penyesuaian threshold trigger
            tr_on = 10
            tr_off = 0.26
            triggers = trigger_onset(stalta, tr_on, tr_off)

            with open('triggers.txt', 'r') as file:
                isi_triggers = set(file.readlines())

            # Plot triggers on each trace
            if len(triggers)>0:
                time_trig = (tra.stats.starttime + triggers[0][0]/sampling_rate)

                # Mpd parameter
                trace_window = tra.slice(starttime=time_trig,endtime=time_trig+3)
                peak = abs(round(trace_window.max())) # termasuk amplitude negatif, diambil nilai mutlaknya
                #peak = trace_window.data.max() # positive amplitude only

                trigger_output = f"{station_trig} {time_trig} {peak}"
                duration = UTCDateTime() - time_trig
                time_limit = 120 # seconds

                if trigger_output + '\n' not in isi_triggers:
                    if triggers[0][0] > 1:
                        
                        with open('triggers.txt', 'a') as file:
                            file.write(trigger_output+'\n')

                        with open('raw_triggers.txt', 'a') as file:
                            file.write(trigger_output+'\n')

                        with open('raw_triggers.txt', 'r') as file:
                            raw_count = len(file.readlines())

                        if raw_count > 0:
                            raw_trigger = pd.read_csv('raw_triggers.txt', sep=' ', header=None)
                            raw_trigger.iloc[:, 1] = raw_trigger.iloc[:, 1].apply(UTCDateTime)
                            raw_trigger.sort_values(by=1)

                            raw_trigger = raw_trigger.drop_duplicates(subset=[1], keep='last')
                            raw_trigger.to_csv('raw_triggers.txt', sep= " ", header=False, index=False)

                        with open('triggers.txt', 'r') as file:
                            line_count = len(file.readlines())

                        if line_count > 0:
                            if duration < time_limit:
                                ax.axvline(x=tra.times('matplotlib')[triggers[0]][0], color='r')

                                print("Trigger:", station_trig, self.time_to_str(time_trig), peak, "===", round(UTCDateTime()-time_trig),"sec ago.")
                                 # Mulai pemutaran audio di latar belakang saat trigger menyala
                                #audio_thread = threading.Thread(target=self.play_audio, args=('warning-sound-6686.mp3',))
                                #audio_thread.start()

    # Fungsi untuk mengubah format UTCDateTime ke string WIB
    def time_to_str(self, utc): 
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

    # Fungsi untuk menghitung parameter gempa
    def estimate_parameter(self):
        with open('triggers.txt', 'r') as file:
            line_count = len(file.readlines())

        # Kode untuk menghilangkan nilai duplikat pada kumpul triggers
        if line_count > 0:                    
            trigger = pd.read_csv('triggers.txt', sep=' ', header=None)
            trigger.iloc[:, 1] = trigger.iloc[:, 1].apply(UTCDateTime)
            trigger.sort_values(by=1)
            trigger = trigger.drop_duplicates(subset=[0], keep='last')

            if trigger.shape[0]>20:
                trigger = trigger.iloc[-20:]
                trigger.to_csv('triggers.txt', sep= " ", header=False, index=False)

        if line_count > 0:
            df_trigger = pd.read_csv('triggers.txt', sep=' ', header=None)
            df_trigger.iloc[:, 1] = df_trigger.iloc[:, 1].apply(UTCDateTime)
            df_trigger.sort_values(by=1)
            df_trigger = df_trigger.drop_duplicates(subset=[0], keep='last')
            min_duration = 30
            df_trigger = df_trigger[df_trigger[1] > UTCDateTime()-min_duration]

            # Melakukan perhitungan parameter gempa jika data trigger minimal ... stasiun
            num_of_sta = df_trigger.shape[0]
            minimal_station = 7

            # Fungsi untuk menghitung parameter gempa jika batas minimal stasiun terpenuhi
            if num_of_sta >= minimal_station:
                if num_of_sta > self.last_station_num:
                    # Di sini kode buat hitung parameter
                    print("Melakukan perhitungan...")
                    # Formatting the data
                    with open('input_arrival.txt', 'w') as file:
                        file.write("")
                    df_trigger['Arrival Time'] = df_trigger.iloc[:, 1].apply(
                        UTCDateTime)
                    df_trigger['Arrival Time'] = df_trigger['Arrival Time'].apply(
                        lambda x: x.strftime("%y%m%d%H%M%S.%f")[:-4])
                    df_trigger['Parameter EP'] = 'EP'
                    df_trigger['Parameter Unknown'] = 0 #ga tau buat apa
                    df_trigger['Modified Name'] = df_trigger[0]
                    df_trigger['Modified Name'] = df_trigger['Modified Name'].apply(
                        lambda x: x[:-1] if len(x) == 5 else (x + ' ' if len(x) == 3 else x))
                    df_trigger['Modified Name'] = df_trigger['Modified Name'] + \
                        df_trigger['Parameter EP']
                    with open('phase_information.txt', 'w') as f:
                        for index, row in df_trigger[['Modified Name', 'Parameter Unknown', 'Arrival Time']].iterrows():
                            f.write(
                                f"{row['Modified Name']} {row['Parameter Unknown']} {row['Arrival Time']}\n")
                    with open('phase_information.txt', 'r') as f_phase:
                        lines_phase = f_phase.readlines()
                    with open('input_arrival.txt', 'w') as f_teks1:
                        f_teks1.writelines(lines_phase)
                    file = open('input_arrival.txt', 'a')
                    file.write("""                 
                    """)
                    file.close()

                    # Merge the head and the arrival input
                    with open('input_head.txt', 'r') as f1:
                        data1 = f1.read()
                    with open('input_arrival.txt', 'r') as f2:
                        data2 = f2.read()
                    combined_data = data1 + data2
                    with open('HYPO71.INP', 'w') as output:
                        output.write(combined_data)

                    # Parameter estimation
                    system_info = platform.system()
                    if system_info == 'Linux':
                        # Definisikan perintah yang ingin dijalankan
                        perintah = """chmod +x Hypo71PC
                        ./Hypo71PC < input
                        """
                        # Jalankan perintah menggunakan subprocess
                        output = subprocess.run(
                            perintah, shell=True, capture_output=True, text=True)
                        file_path = 'HYPO71.OUT'
                        
                        #with open('HYPO71.OUT', 'r') as source_file:
                        #    line = source_file.readlines()
 
                    elif system_info == 'Windows':
                        # Jalankan program eksternal dengan menggunakan subprocess.Popen
                        process = subprocess.Popen(
                            'HYPO71PC.exe', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        file_path = 'HYPO71PC.PUN'
                        
                        #with open('HYPO71PC.PUN', 'r') as source_file2:
                        #   line = source_file2.readlines()

                    # Saving the earthquake history
                    with open(file_path, 'r') as source_file:
                        line = source_file.readlines()
                    if len(line) >= 2:
                        if len(line[1].strip()) > 0:
                            # play warning audio
                            audio_eq_thread = threading.Thread(
                                    target=self.play_audio, args=('046570_alarmclockbeepsaif-77772.mp3',))
                            audio_eq_thread.start()

                            origin_time, lat, long, depth = self.eq_parameter(file_path,
                                    -1)
                            
                            # Jika depth <= 1, biasanya parameter salah. Skip aja?
                            # Wilayah PGR VII: long>=108.65 and long<= 114.1
                            if depth > 1 and long >= 106 and long <= 115.71:
                                lat = round(lat, 4)
                                long = round(long, 4)
                                origin_time_wib = origin_time + 7*60*60
                                city, distance, azimuth_val = self.nearest_city(lat, long)
                                back_azimuth = self.back_azimuth_func(azimuth_val)
                                direction = self.direction_func(back_azimuth)
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

                                if self.sent_msg == 0:
                                    
                                    df_stasiun = pd.read_csv("daftar_stasiun.csv", sep="|")
                                    df_peak = df_trigger[[0,1,2]]
                                    df_peak.columns = ['Station', 'Trigger Time', 'Peak']
                                    df_merged = pd.merge(df_peak, df_stasiun[['Station','Latitude','Longitude']], on='Station', how='left')
                                    df_merged['Magnitudo'] = None

                                    # Mendapatkan nilai magnitudo
                                    for index, row in df_merged.iterrows():
                                        dist = self.haversine([lat, long],[row['Latitude'],row['Longitude']])
                                        h_dist = self.hypo_dist(depth, dist)
                                        df_merged.at[index, 'Magnitudo'] = self.mag_pd(row['Peak'],h_dist)

                                    # Daftar stasiun yang Mpd-nya cocok dengan koefisien persamaan Mpd
                                    daftar_stasiun = ['TAGJI', 'SAKJI', 'GKJM', 'PGJM', 'PRJI', 'GRJI', 'BUJI', 'CMJI', 'MKJM',
                                                      'PCJI', 'SCJI', 'SYJI', 'UGM', 'PLJI', 'TBJI']

                                    # Memfilter DataFrame
                                    df_merged = df_merged[df_merged['Station'].isin(daftar_stasiun)]
                                    self.mpd = df_merged['Magnitudo'].mean()

                                    # Mengeluarkan peringatan jika magnitudonya di atas 3
                                    if self.mpd >= 3:
                                        desc = f'PERINGATAN DINI GEMPA BUMI\nMag: {self.mpd:.1f}, {day}-{month}-{year} {hr:02d}:{mn:02d}:{sc:02d} WIB, Lokasi: {abs(lat):.4f}LS, {abs(long):.4f}BT ({round(distance)} km {direction} {city.upper()}), Kedalaman: {round(depth)} km.\n'

                                        print(desc)
                                        disclaimer = '\nDisclaimer: Informasi ini berupa estimasi sederhana dengan mengutamakan kecepatan, serta ditujukan untuk peringatan dini. Silakan kunjungi laman resmi BMKG untuk informasi yang lebih akurat.'
                                        gap = UTCDateTime() - origin_time
                                        gap_desc = f'\n\n::Pesan ini terkirim {round(gap)} detik setelah gempa terjadi.'

                                        msg = desc+disclaimer+gap_desc
                                        asyncio.run(self.send_message(msg))
                                        self.sent_msg += 1

                                        latest_desc = f'PERINGATAN DINI GEMPA BUMI\n{day}-{month}-{year} {hr:02d}:{mn:02d}:{sc:02d} WIB\nLokasi: {abs(lat):.4f}LS, {abs(long):.4f}BT\n{round(distance)} km {direction} {city.upper()}\nKedalaman: {round(depth)} km.\n'
                                
                                        #with open('latest.txt', 'w') as dest_file:
                                        #    dest_file.write(latest_desc+"\nEstimasi magnitudo: "+str(round(self.mpd,1))+"\n\nChannel Telegram EEWS: @eewsmbkm")

                                        eq_output = f'{origin_time},{lat},{long},{depth},{num_of_sta},{round(self.mpd, 1)}\n'
                                        with open('earthquake.txt', 'r') as file:
                                            isi_file = set(file.readlines())

                                        if eq_output not in isi_file:
                                            with open('earthquake.txt', 'a') as dest_file:
                                                dest_file.write(eq_output)

                                        # Membuat peta lokasi gempa
                                        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'
                                        attr = ('Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC')
                                        m = folium.Map(location=[lat, long], control_scale=False, zoom_control=False, tiles=tiles, attr=attr, zoom_start=7)
                                        icon_html = '''
                                        <div style="
                                            position: absolute;
                                            transform: translate(-25%, -30%);
                                            font-size: 24px;
                                            color: #ff8100;
                                        ">&#9733;</div>
                                        '''
                                        folium.Marker(
                                            location=[lat, long],
                                            icon=folium.DivIcon(html=icon_html)
                                        ).add_to(m)

                                        # Tambahkan lingkaran dengan opacity berbeda
                                        center = [lat, long]
                                        radii_m = [100, 200, 300, 400, 500]
                                        radii = [r*100*2 for r in radii_m]
                                        opacities = [1.0, 0.8, 0.6, 0.4, 0.2]

                                        for radius, opacity in zip(radii, opacities):
                                            self.add_circle(m, center, radius, opacity)
                                        m.save('peta_pulau_jawa.html')

                                        with open('HYPO71.PRT', 'r') as file:
                                            data_to_append = file.read()

                                        #with open('earthquake_log.txt', 'a') as file:
                                        #    file.write(data_to_append)

                                        self.last_station_num = num_of_sta

                                        # Dataframe waktu tiba gelombang S
                                        df_cities = self.estimate_arrival()

                                        with open('latest.txt', 'w') as dest_file:
                                            dest_file.write("Perkiraan waktu tiba gelombang S:\n")
                                            for index, row in df_cities.iterrows():
                                                dest_file.write(row['arrival']+" "+row['City']+"\n")

                                        with open('latest.txt', 'r') as file:
                                            isi_file = file.read()

                                        # Mengirim pesan ke telgram
                                        asyncio.run(self.send_message(isi_file))
                                        image_path = self.save_map_as_image()
                                        asyncio.run(self.send_image_to_telegram(image_path))
                        else:
                            print("Data tidak mencukupi.")
            else:   
                self.sent_msg = 0
                self.last_station_num = 0
                self.mpd = -1

    # Fungsi baru untuk menangani plot waveform
    def plot_waveform_threaded(self, ax, trace):
        station = trace.stats.station
        network = trace.stats.network
        location = trace.stats.location
        channel = trace.stats.channel
        key = (station, network, location, channel)
        ax = self.station_axes[key]
        tra = trace.copy()
        corners = 3
        freq_min = 4
        freq_max = 8
        sampling_rate = tra.stats.sampling_rate
        #sampling_rate = 10.0
        max_f_max = 0.9 * (sampling_rate / 2)
        freq_max = min(freq_max, max_f_max)

        #tra.resample(sampling_rate)

        tra.data = tra.data - np.nanmean(tra.data)

        tra.taper(type='cosine', max_percentage=0.05)

        t_zpad = 1.5 * corners / freq_min
        endtime_remainder = tra.stats.endtime
        tra.trim(starttime=None, endtime=endtime_remainder +
                 t_zpad, pad=True, fill_value=0)

        # trace.trim(starttime=trace.stats.starttime + 4)
        tra.filter("bandpass",
                   freqmin=freq_min,
                   freqmax=freq_max,
                   corners=corners,
                   zerophase=True)

        tra.trim(starttime=None, endtime=endtime_remainder)
        
        # Plot each trace
        ax.plot(tra.times('matplotlib'), tra.data, 'gray')
        ax.set_xlim(UTCDateTime() - 600, UTCDateTime())

        if start:
            ax.figure.canvas.draw()
        
    def detect_triggers(self, ax, trace):
        threading.Thread(target=self.detect_triggers_threaded, args=(ax,trace)).start()
 
    def plot_waveform(self, ax, trace):
        threading.Thread(target= self.plot_waveform_threaded, args=(ax,trace)).start()

    

    def update_data(self, trace):
        # def process_update(trace):
        station = trace.stats.station
        network = trace.stats.network
        location = trace.stats.location
        channel = trace.stats.channel
        key = (station, network, location, channel)
        ax = self.station_axes[key]

        trace_id = trace.id
        split_trace = trace_id.split(".")
        if split_trace[2] == "00" or split_trace[2] == "":
            self.plot_waveform(ax, trace)  # Panggil fungsi plot_waveform
            self.detect_triggers(ax, trace)  # Panggil fungsi detect_triggers
            self.estimate_parameter()
            
class SeismicApp(QMainWindow):
    def __init__(self, data_array):
        super().__init__()
        
        self.central_widget = LivePlotWidget(data_array)
        self.setCentralWidget(self.central_widget)

        self.seismic_threads = []
        for server_address in ["172.19.3.69"]:
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
    with open('triggers.txt', 'w') as file:
        file.write("")  # Clear file trigger

    with open('raw_triggers.txt', 'w') as file:
        file.write("")

    app = QApplication(sys.argv)
    with open('data_array1.json', 'r') as file:
        data_array = json.load(file)    

    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    MainWindow.show()
    #MainWindow.hide()

    sys.exit(app.exec_())
