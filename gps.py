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
    deg = coord / 100
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
        L = [line.split(',') for line in self.raw]
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
    def gps_coords(self):
        lat = []
        lon = []
        for line in self.gga:
            lat.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
            lon.append(float(line[2]) if line[3] == 'N' else -float(line[6]))
        return lat, lon

    @property
    def gps_coords_decimal(self):
        lat = []
        lon = []
        for line in self.gga:
            lat.append(nmea_to_decimal(line[4:6]) - .19)
            lon.append(nmea_to_decimal(line[2:4]) + .168)
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
        folium.Marker([48.41955333953407, -4.47470559068223], popup='ENSTA', tooltip='hey!').add_to(m)
        PolyLineOffset(coords).add_to(m)
        m.save('gps_map.html')


if __name__ == '__main__':
    d = Data('data/data_uv24.nmea')
    # d.plot_coords()
    print(d.gps_coords_decimal)
    d.coords_on_map()
