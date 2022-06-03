from math import floor
import mpl_toolkits.mplot3d.axes3d as axes3d
import PIL
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
                last = line[-1].split('*')
                gsv.append(line)
                gsv[-1][-1] = last[0]
                gsv[-1].append(last[1])

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
        folium.Marker([48.41955333953407, -4.47470559068223], popup='ENSTA', tooltip='hey!').add_to(m)
        PolyLineOffset(coords).add_to(m)
        m.save('out/gps_map.out')
        
    def satellite_pos(self):
            """renvoie une matrice transmission avec pour chaque relevé gps une liste de
            satellite contenant l'identité, l'élévation, l'azimut et la qualité du signal"""
            transmission = []
            nb_sat = 0
            for line in self.gsv:
                if line[2] == '1':
                    nb_sat = int(line[3])
                    transmission.append([])
                n = min(nb_sat,4)
                for i in range(0,n):
                    transmission[-1].append([int(line[(i+1)*4]),\
                                int(line[(i+1)*4+1]), int(line[(i+1)*4 + 2]), int(line[(i+1)*4 +3])])
                    nb_sat -= 1
            return transmission



    def plot_satellite(self,i):
        """
        Permet de représenter la position des satellites ayant enregistré la position numéro i de l'acquisition
        dans le système de coordonnées horizontales (référentiel terrestre en coordonnées sphériques)
        """
        satellite = self.satellite_pos()[i]
        print(satellite)
        a = 20

        L = []
        Ph = []
        for sat in satellite:
            Ph.append(np.pi/2 - sat[1]*np.pi/180)
            L.append(sat[2]*np.pi/180)
        #lam, phi = np.meshgrid(L, Ph)
        # coordonnees x,y,z de la sphere discretisee selon le maillage regulier lambda, phi

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i in range(len(L)):
            x = a * np.cos(L[i]) * np.sin(Ph[i])
            y = a * np.sin(L[i]) * np.sin(Ph[i])
            z = a * np.cos(Ph[i])
            ax.scatter(x,y,z,c='r', marker='^')
        ax.scatter(0,0,0, c='b', s= 100, marker ='o')
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
        phi = np.pi/2 - Ph[0] * np.pi / 180
        lam = L[0] * np.pi / 180
        print(lam, phi)
        xc = 1.1*np.cos(lam) * np.sin(phi)
        yc = 1.1*np.sin(lam) * np.sin(phi)
        zc = 1.1*np.cos(phi)
        print(xc,yc,zc)
        ax.scatter(xc, yc, zc, c='b', s=100, marker='*')

        #satellite
        satellite = self.satellite_pos()[0]
        R = [[-np.sin(lam), -np.sin(phi)*np.cos(phi), np.cos(phi)*np.cos(lam)],
             [np.cos(lam), -np.sin(phi)*np.sin(lam), np.cos(phi)*np.sin(lam)],
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

            X = np.array(R).dot(np.array([x,y,z]).T)
            x,y,z = X.T
            if i == 1:
                print(X.T)
            ax.scatter(x, y, z, c='r', marker='^')

        plt.show()



if __name__ == '__main__':
    d = Data('data/data_uv24.nmea')
    #d = Data('data/gpsdata110522.txt')
    # d.plot_coords()
    #print(d.gsv)
    #print(d.satellite_pos())
    #print(d.gps_coords_decimal)
    # print(d2.gps_coords_decimal)
    #d.coords_on_map()
    #d.plot_satellite(0)
    #print(d.gps_coords_decimal)

    d.visu_planet()