from math import floor

import folium
import matplotlib.pyplot as plt
import numpy as np
from folium.plugins import *


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
        self.original_file = filename

    def clean(self, save=False):
        """
        remove single quotes and newline
        """
        self.raw = np.char.replace(self.raw, "'", "")
        self.raw = np.char.replace(self.raw, ", ", ",")
        self.raw = np.char.replace(self.raw, "\\n", r"\n")
        self.raw = np.char.replace(self.raw, "\\r", r"\r")
        self.raw = np.char.replace(self.raw, "$", "\n$")
        # save to new file
        if save:
            np.savetxt(self.original_file.replace(".txt", "_clean.txt"),
                       self.raw, delimiter='', fmt='%s')

    @property
    def gga(self):
        """
        données de position

        :return: la trame GGA brute
        """
        gga = []
        L = [line.replace("'", "").split(',') for line in self.raw]
        for line in L:
            try:
                if line[0] == '$GPGGA' and len(line) == 9 and line[2] + line[4] != '':
                    print(line)
                    gga.append(line)
            except IndexError as e:
                print(e)
                pass
        return gga

    @property
    def vtg(self):
        """
        données de vitesse

        :return: la trame VTG brute
        """
        vtg = []
        L = [line.split(',') for line in self.raw]
        for line in L:
            if line[0] == '$GPVTG':
                vtg.append(line)
        return vtg

    @property
    def gsv(self):
        """
        données sur les satellites

        :return: la trame GSV brute
        """
        gsv = []
        L = [line.split(',') for line in self.raw]
        for line in L:
            if line[0] == '$GPGSV':
                gsv.append(line)
        return gsv

    @property
    def gps_coords(self):
        """
        extraction des coordonnées GPS depuis les données GGA

        :return: latitudes et longitudes sexagesimales
        """
        lat = []
        lon = []
        for line in self.gga:
            try:
                lat.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
                lon.append(float(line[2]) if line[3] == 'N' else -float(line[6]))
            except Exception as e:
                print(e)
                print(line)
                pass
        return lat, lon

    @property
    def gps_coords_decimal(self):
        """
        extraction des coordonnées GPS en format décimal

        :return: latitudes et longitudes décimales
        """
        # dlat = -.19
        # dlon = .168
        dlat = dlon = 0
        lat = []
        lon = []
        for line in self.gga:
            print(line)
            lat.append(nmea_to_decimal(line[4:6]) + dlat)
            lon.append(nmea_to_decimal(line[2:4]) + dlon)
        return lat, lon

    def plot_coords(self):
        """
        affichage des coordonnées GPS sur un axe 2D
        """
        try:
            plt.plot(self.gps_coords[0], self.gps_coords[1], '--.')
        except Exception as e:
            n = min(len(self.gps_coords[0]), len(self.gps_coords[1]))
            plt.plot(self.gps_coords[0][:n], self.gps_coords[1][:n], '--.')
            print(e)
            pass
        plt.show()

    def coords_on_map(self):
        """
        affichage des données GPS sur une carte grâce à folium

        :return: crée un fichier html
        """
        locEnsta = [48.4183363, -4.4730597]
        n = min(len(self.gps_coords[0]), len(self.gps_coords[1]))
        coords = list(zip(self.gps_coords_decimal[1][:n], self.gps_coords_decimal[0][:n]))
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
                transmission.append([int(line[pos]),
                                     int(line[pos + 1]),
                                     int(line[pos + 2])])
            nb_sat -= 1
        return np.asarray(transmission)

    def plot_satellites(self):
        """ Affiche les satellites en coordonnées polaires """
        plt.close('all')
        satpos = self.satellite_pos()
        elev = satpos[:, 0]
        azim = satpos[:, 1]
        plt.polar(elev, azim, '.')
        plt.show()

    # TODO: transformer les azimuts / élévation en carto 3D des satellites


if __name__ == '__main__':
    # d = Data('data/data_uv24.nmea')
    # d = Data('data/gpsdata110522.txt')
    filename = 'data/gps_export_1654070763.7245858_clean.txt'
    d = Data(filename)
    # d.clean()
    # d.plot_coords()
    # print(d.gsv)
    # print(d.gga)
    # satpos = d.satellite_pos()
    # t, r = satpos[:, 1], satpos[:, 0]
    #
    # plt.polar(t, r, '.')

    # plt.polar(satpos[:, 1], satpos[:, 0], '.')
    # fig.colorbar(c, ax=ax)

    # plt.show()
    d.coords_on_map()
