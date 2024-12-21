import folium

lat = -7.8928333333
long = 110.524833
tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'
attr = ('Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC')
m = folium.Map(location=[lat, long], tiles=tiles, attr=attr, zoom_start=8)
info_popup = folium.Popup(f'{lat}, {long}vvvvvv vvvv vvvvvvv vv mmmmmmm mmmmmm', max_width=200 ,show=True)
folium.Marker([lat, long], popup=info_popup, icon=folium.Icon(icon_color="orange", icon="star"),).add_to(m)


# Simpan peta sebagai file HTML
m.save('peta.html')
