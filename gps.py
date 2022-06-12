from math import floor
import mpl_toolkits.mplot3d.axes3d as axes3d
import PIL
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import *
import re
import pyproj.crs
import geopandas as gpd
import operator
from functools import reduce


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


def dist_ang(coordA, coordB):
    return np.arccos(np.sin(coordA[1] * np.pi / 180) * np.sin(coordB[1] * np.pi / 180) +
                     np.cos(coordA[1] * np.pi / 180) * np.cos(coordB[1] * np.pi / 180) *
                     np.cos((coordA[0] - coordB[0]) * np.pi / 180)) * 6378137


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
        # self.raw = np.char.replace(self.raw, "\\n", r"\n")
        # self.raw = np.char.replace(self.raw, "\\r", r"\r")
        # self.raw = np.char.replace(self.raw, "$", "\n$")
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
                if 'GGA' in line[0] and len(line) > 10 and line[2] != '' and line[4] != '':
                    gga.append(line)
            except IndexError as e:
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
            if 'GSV' in line[0] and len(line) > 5:
                gsv.append(line)
        return gsv

    @property
    def gps_coords(self):
        """
        extraction des coordonnées GPS depuis les données GGA

        :return: latitudes et longitudes sexagesimales
        """
        long = []
        lat = []
        alt = []
        for line in self.gga:
            try:
                long.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
                lat.append(float(line[2]) if line[3] == 'N' else -float(line[6]))
                alt.append(float(line[9]))
            except Exception as e:
                pass
        return [long, lat, alt]

    @property
    def gps_coords_decimal(self):
        """
        extraction des coordonnées GPS en format décimal

        :return: latitudes et longitudes décimales
        """
        # dlong = -.19
        # dlat = .168
        dlong = dlat = 0
        long = []
        lat = []
        alts = []
        i = 0
        for line in self.gga:
            try:
                tmplong = nmea_to_decimal(line[4:6]) + dlong
                tmplat = nmea_to_decimal(line[2:4]) + dlat

                if i != 0 and abs(tmplong - long[-1]) < 1 and abs(tmplat - lat[-1]) < 1:
                    long.append(tmplong)
                    lat.append(tmplat)
                elif i == 0:
                    long.append(tmplong)
                    lat.append(tmplat)
                    i += 1
                alts.append(float(line[9]))

            except Exception as e:
                # print(line)
                pass
        return long, lat, alts

    @property
    def stats(self):
        temp = np.asarray(self.gps_coords_decimal)
        mean = (np.mean(temp[0]), np.mean(temp[1]))
        std = (np.std(temp[0]), np.std(temp[1]))
        return mean, std

    def __str__(self):
        return str(self.raw)

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
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.title('Tracé GPS du récepteur')
        plt.show()

    def plot_coords_3d(self):
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot(self.gps_coords[0],
                self.gps_coords[1],
                self.gps_coords[2], '--.')
        ax.set_xlabel('longitude')
        ax.set_ylabel('latitude')
        ax.set_zlabel('altitude')
        plt.title('Positions du récepteur GNSS')
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
        """renvoie une matrice transmission avec pour chaque relevé gps une liste de
            satellite contenant l'identité, l'élévation, l'azimut et la qualité du signal"""
        transmission = []
        nb_sat = 0
        for line in self.gsv:
            tmp = [re.sub('[a-zA-Z]*', '', re.sub('[*]\S*', '', el)) for el in line]
            line = [el if el != '' else '0' for el in tmp]
            if line[2] == '1':
                nb_sat = int(line[3])
                transmission.append([])
            n = min(nb_sat, 4)
            for i in range(0, n):
                # print([line[(i + 1) * 4],
                #        line[(i + 1) * 4 + 1], line[(i + 1) * 4 + 2],
                #        line[(i + 1) * 4 + 3]])
                try:
                    el = [float(tmp[(i + 1) * 4]),
                          float(tmp[(i + 1) * 4 + 1]), float(tmp[(i + 1) * 4 + 2])]
                    transmission[-1].append(el)
                except Exception as e:
                    pass
                nb_sat -= 1
        return transmission

    def plot_satellite(self, i):
        """
        Permet de représenter la position des satellites ayant enregistré la position numéro i de l'acquisition
        dans le système de coordonnées horizontales (référentiel terrestre en coordonnées sphériques)
        """
        satellite = self.satellite_pos()[i]
        a = 20

        L = []
        Ph = []
        for sat in satellite:
            Ph.append(np.pi / 2 - sat[1] * np.pi / 180)
            L.append(sat[2] * np.pi / 180)
        # lam, phi = np.meshgrid(L, Ph)
        # coordonnees x,y,z de la sphere discretisee selon le maillage regulier lambda, phi

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i in range(len(L)):
            x = a * np.cos(L[i]) * np.sin(Ph[i])
            y = a * np.sin(L[i]) * np.sin(Ph[i])
            z = a * np.cos(Ph[i])
            ax.scatter(x, y, z, c='r', marker='^')
        ax.scatter(0, 0, 0, c='b', s=100, marker='o')
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')

        plt.show()

    def visu_planet(self):
        # load bluemarble with PIL
        bm = PIL.Image.open('data/bluemarble.jpg')
        # it's big, so I'll rescale it, convert to array, and divide by 256 to get RGB values that matplotlib accept
        bm = np.array(bm.resize([int(d / 5) for d in bm.size])) / 256.

        # coordinates of the image - don't know if this is entirely accurate, but probably close
        lons = np.linspace(-180, 180, bm.shape[1]) * np.pi / 180
        lats = np.linspace(-90, 90, bm.shape[0])[::-1] * np.pi / 180

        # repeat code from one of the examples linked to in the question, except for specifying facecolors:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        x = np.outer(np.cos(lons), np.cos(lats)).T
        y = np.outer(np.sin(lons), np.cos(lats)).T
        z = np.outer(np.ones(np.size(lons)), np.sin(lats)).T
        ax.plot_surface(x, y, z, rstride=4, cstride=4, facecolors=bm)

        L, Ph = self.gps_coords_decimal
        print(Ph[0], L[0])
        phi = np.pi / 2 - Ph[0] * np.pi / 180
        lam = L[0] * np.pi / 180
        print(lam, phi)
        xc = 1.1 * np.cos(lam) * np.sin(phi)
        yc = 1.1 * np.sin(lam) * np.sin(phi)
        zc = 1.1 * np.cos(phi)
        print(xc, yc, zc)
        ax.scatter(xc, yc, zc, c='b', s=100, marker='*')

        # satellite
        satellite = self.satellite_pos()[0]
        R = [[-np.sin(lam), -np.sin(phi) * np.cos(phi), np.cos(phi) * np.cos(lam)],
             [np.cos(lam), -np.sin(phi) * np.sin(lam), np.cos(phi) * np.sin(lam)],
             [0, np.cos(phi), np.sin(phi)]]
        a = 3.14
        L_sat = []
        Ph_sat = []
        for sat in satellite:
            Ph_sat.append(np.pi / 2 - sat[1] * np.pi / 180)
            L_sat.append(sat[2] * np.pi / 180)
        # lam, phi = np.meshgrid(L, Ph)
        # coordonnees x,y,z de la sphere discretisee selon le maillage regulier lambda, phi

        for i in range(len(L_sat)):
            x = a * np.cos(L_sat[i]) * np.sin(Ph_sat[i])
            y = a * np.sin(L_sat[i]) * np.sin(Ph_sat[i])
            z = a * np.cos(Ph_sat[i])

            X = np.array(R).dot(np.array([x, y, z]).T)
            x, y, z = X.T
            if i == 1:
                print(X.T)
            ax.scatter(x, y, z, c='r', marker='^')

        plt.show()

    def compare(self, other):
        """ Permet de comparer graphiquement les données gps de deux acquisitions"""
        plt.plot(self.gps_coords_decimal[0], self.gps_coords_decimal[1], '.b')
        plt.plot(other.gps_coords_decimal[0], other.gps_coords_decimal[1], '.r')
        plt.legend(['acquisition 1', 'acquisition 2'])
        plt.show()


if __name__ == '__main__':
    # d = Data('data/data_uv24.nmea')
    # d = Data('data/gpsdata110522.txt')
    # filename = 'data/gps_export_1654070763.7245858_clean.txt'
    filename = 'data/not_precise_rugby.txt'
    # filename = 'data/data_uv24.nmea'
    d = Data(filename)
    d.clean()
    # print(d.gga)
    # d.plot_coords()
    print(d.stats)
    d2 = Data('data/precise_rugby.txt')
    d2.clean()
    print(d2.stats)
    d.compare(d2)
    # print(d.gsv)
    # print(d.gga)
    # satpos = d.satellite_pos()
    # t, r = satpos[:, 1], satpos[:, 0]
    #
    # plt.polar(t, r, '.')

    # plt.polar(satpos[:, 1], satpos[:, 0], '.')
    # fig.colorbar(c, ax=ax)

    # plt.show()
    # d.coords_on_map()
    print("distance de précis à pas précis :", dist_ang(d.stats[0], d2.stats[0]))
    print("incertitude pas précis :", dist_ang(list(np.array(d.stats[0]) + np.array(d.stats[1])),
                                               list(np.array(d.stats[0]) - np.array(d.stats[1]))))
    print("incertitude précis :", dist_ang(list(np.array(d2.stats[0]) + np.array(d2.stats[1])),
                                           list(np.array(d2.stats[0]) - np.array(d2.stats[1]))))
    ref = [-4.47424307, 48.41903413]
    print("distance réf à pas précis :", dist_ang(d.stats[0], ref))
    print("distance réf à précis :", dist_ang(d2.stats[0], ref))

    # d.visu_planet()
