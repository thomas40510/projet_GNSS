from math import floor

import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import *
import pyproj.crs
import geopandas as gpd


def sexagesimal_to_decimal(sexagesimal):
    decimal = 0
    if sexagesimal[-1] == 'E':
        decimal = float(sexagesimal[0]) + float(sexagesimal[0]) / 60
    elif sexagesimal[-1] == 'W':
        decimal = -float(sexagesimal[0]) - float(sexagesimal[0]) / 60
    elif sexagesimal[-1] == 'N':
        decimal = float(sexagesimal[0]) + float(sexagesimal[0]) / 60
    elif sexagesimal[-1] == 'S':
        decimal = -float(sexagesimal[0]) - float(sexagesimal[0]) / 60
    return decimal


def min_to_deg(minutes):
    return minutes / 60


def nmea_to_decimal(nmea):
    coord = float(nmea[0])
    dir = nmea[-1]
    deg = floor(coord / 100)
    min = coord - deg * 100
    mult = -1 if dir == 'S' or dir == 'W' else 1
    decimal = deg + min_to_deg(min)
    return mult * decimal


class Data:
    def __init__(self, filename):
        self.raw = np.loadtxt(fname=filename, delimiter='\n', dtype=str)

    @property
    def gga(self):
        gga = []
        L = [line.replace("'", "").split(',') for line in self.raw]
        for line in L:
            if line[0] == '$GPGGA':
                gga.append(line)
        return gga

    @property
    def vtg(self):
        vtg = []
        L = [line.split(',') for line in self.raw]
        for line in L:
            if line[0] == '$GPVTG':
                vtg.append(line)
        return vtg

    @property
    def gsv(self):
        gsv = []
        L = [line.split(',') for line in self.raw]
        for line in L:
            if line[0] == '$GPGSV':
                gsv.append(line)
        return gsv

    @property
    def gps_coords(self):
        lat = []
        lon = []
        for line in self.gga:
            lat.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
            lon.append(float(line[2]) if line[3] == 'N' else -float(line[6]))
        return lat, lon

    @property
    def gps_coords_decimal(self):
        # dlat = -.19
        # dlon = .168
        dlat = dlon = 0
        lat = []
        lon = []
        for line in self.gga:
            lat.append(nmea_to_decimal(line[4:6]) + dlat)
            lon.append(nmea_to_decimal(line[2:4]) + dlon)
        return lat, lon

    def plot_coords(self):
        plt.plot(self.gps_coords[0], self.gps_coords[1], '--.')
        plt.show()

    def coords_on_map(self):
        locEnsta = [48.4183363, -4.4730597]
        # coordx = [el/99.653 for el in self.gps_coords[1]]
        # coordy = [el/95.76 for el in self.gps_coords[0]]
        coords = list(zip(self.gps_coords_decimal[1], self.gps_coords_decimal[0]))
        m = folium.Map(location=coords[0], zoom_start=15, control_scale=True)
        folium.Marker([48.41955333953407, -4.47470559068223],
                      popup='ENSTA', tooltip='ENSTA').add_to(m)
        PolyLineOffset(coords).add_to(m)
        m.save('out/gps_map.html')

    def satellite_pos(self):
        """
        extrait depuis les trames GSV les azimut et élévation des satellites en donnant la force du signal

        :return: matrice transmission
        """
        transmission = []
        nb_sat = 0
        for line in self.gsv:
            if line[2] == '1':
                nb_sat = int(line[3])
            n = min(nb_sat, 4)
            for i in range(0, n):
                pos = (i + 1) * 4
                transmission.append([int(line[pos]), int(line[pos + 1]), int(line[pos + 2])])
                nb_sat -= 1
        return np.asarray(transmission)


if __name__ == '__main__':
    d = Data('data/data_uv24.nmea')
    # d = Data('data/gpsdata110522.txt')
    # d.plot_coords()
    print(d.gps_coords_decimal)
    print(d.gsv)
    satpos = d.satellite_pos()
    plt.polar(satpos[:, 1], satpos[:, 2], '.')
    plt.show()
    # print(d2.gps_coords_decimal)
    # d.coords_on_map()
