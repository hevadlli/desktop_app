import QtQuick 2.0
import QtLocation 5.6

Item {
    id: root
    width: 800
    height: 600

    Plugin {
        id: mapPlugin
        name: "osm" // Ganti dengan provider peta Anda
    }

    Map {
        id: map
        anchors.fill: parent
        plugin: mapPlugin
        center: QtPositioning.coordinate(0, 0)
        zoomLevel: 10
    }
}