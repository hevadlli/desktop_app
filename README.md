# Earthquake Early Warning System Prototype

Program untuk mendeteksi gelombang P, melakukan perhitungan parameter gempa, serta pengiriman peringatan melalui channel telegram [@eewsmbkm](https://t.me/eewsmbkm).

**Catatan:**

- Untuk menjalankan program, jalankan script `bash_eews.sh`.
- Untuk menghentikan program yang berjalan di latar belakang, silakan tekan CTRL+C atau jalankan script `bash_kill_eews.sh`.
- Sejauh ini efektif untuk dijalankan di Linux Ubuntu. Perlu beberapa penyesuaian jika akan dijalankan di Windows.
- Hanya gempa dengan magnitudo >= 3, kedalaman >= 1 yang diproses.
- Jika akan dilakukan penambahan stasiun untuk memperluas wilayah deteksi episentrum, program hanya efektif untuk penambahan stasiun di kuadran lintang selatan dan bujur timur. Perlu penyesuaian kode jika akan dilakukan penambahan stasiun di lintang utara. Cek panduan HYPO71 untuk lebih lengkap.

## Deskripsi File

- `eews_part1.py`: skrip untuk mendeteksi trigger gelombang P, melakukan perhitungan parameter gempa, penyimpanan parameter gempa, dan pengiriman pesan ke channel telegram [@eewsmbkm](https://t.me/eewsmbkm).
- `eews_part2.py` sampai `eews_part5.py`: skrip hanya untuk mendeteksi trigger gelombang P. Kode belum dirapikan, masih ada kode yang tidak jadi digunakan –misalnya PyQt5 untuk tampilan GUI– yang belum dihapus.
- `data_array1.json` sampai `data_array5.json`: data stasiun seismograf yang digunakan.
- `eews_gui.py`: skrip untuk menampilkan parameter gempa, menampilkan peta, dan waktu hitung mundur kedatangan gelombang S di suatu kota.
- `raw_triggers.txt`: file untuk menyimpan semua trigger yang terdeteksi. File akan dibersihkan setiap program `eews_part1.py` dijalankan.
- `triggers.txt`: file untuk menyimpan setiap trigger yang akan dijadikan input perhitungan parameter gempa. Terdapat mekanisme penghapusan beberapa baris data jika tercapai jumlah stasiun berbeda dengan jumlah tertentu. Penghapusan baris data menyisakan ±20 baris data. Silakan cek skrip `eews_part1.py` bagian fungsi `estimate_parameter` untuk memastikan.
- `input_head.txt`: data stasiun seismograf beserta koordinat dan elevasi.
- `input_arrival.txt`: data waktu tiba gelombang P yang telah diformat menyesuaikan format input program HYPO71.
- `HYPO71`: program berbahasa Fortran untuk menghitung parameter gempa dengan menggunakan metode Geiger.
- `HYPO71.INP`: input parameter perhitungan parameter untuk HYPO71. Gabungan dari file `input_head.txt` dan `input_arrival.txt`.
- `HYPO71.PRT`: hasil perhitungan parameter gempa dengan detail.
- `HYPO71.OUT`: hasil perhitungan parameter gempa dengan ringkas.
- `earthquake.txt`: parameter gempa.
- `s_arrival.csv`: data waktu tiba gelombang S di beberapa kota dari gempa yang terakhir dihitung.

## Keterbatasan

- Skrip `eews_part1.py` sampai `eews_part5.py` masih sering error, tiba-tiba berhenti. Maka dari itu digunakan file `bash_eews.sh` untuk restart program setiap satu jam.
- Menutup jendela tampilan seismogram tidak otomatis menghentikan proses triggering yang berjalan di latar belakang. Untuk menghentikannya, silakan tekan CTRL+C pada terminal yang menjalankan skrip `bash_eews.sh`. Untuk memastikan program pendeteksian trigger benar-benar berhenti, silakan cek system monitor (di Ubuntu). Jika masih terdapat proses dari Python dengan command line dari skrip `eews_part*.py` dengan status masih `running`, silakan jalankan file `bash_kill_eews.sh` untuk menghentikan semua proses triggering yang masih berjalan.
- Program masih sering mendeteksi gempa jauh, misalnya dari NTT ke timur, tetapi hasil perhitungan parameternya masih menghasilkan koordinat episentrum gempa di wilayah PGR VII. Akurasi parameter masih rendah untuk gempa yang jauh.
- Nilai maksimal dan minimal sumbu Y pada tampilan plot seismogram masih belum autoscaling.
- Penggabungan sinyal seismik masih belum efektif. Masih sering terjadi lonjakan amplitudo di saat kondisi normal.
- Multithreading untuk triggering dan plotting masih belum efektif. Sebagai contoh dampaknya, program `eews_part1.py` yang memiliki tampilan plot seismogram akan mengalami error "can't create new thread" setelah beberapa jam dijalankan. Solusi saat ini yaitu programnya direstart. Terdapat juga kemungkinan pengiriman pesan ganda peringatan ke channel telegram dan pendeteksian ganda gelombang P.
- Kode UI masih belum rapi. Integrasi script UI dan triggering juga masih belum baik.
- Belum dibuat mekanisme untuk reconnecting koneksi yang baik ketika terdapat kendala dengan koneksi. Ada kemungkinan server sibuk atau tidak memberikan respons. Untuk solusinya saat ini adalah dengan mengganti IP server di semua skrip `eews_part*.py` dan `data_array*.json`. Pilihan server yang bisa dipilih saat program ini ditulis antara lain `172.19.3.65`, `172.19.3.69`, dan `172.19.3.150`.
- Fitur menu yang berfungsi hanya fitur peta, fitur filter belum 
- Fitur peta dapat ditekan beberapa kali sehingga akan mengakibatkan sistem semakin berat
