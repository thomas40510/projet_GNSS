import numpy as np
import matplotlib.pyplot as plt


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

    def plot_coords(self):
        lat = []
        lon = []
        for line in self.gga:
            lat.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
            lon.append(float(line[2]) if line[3] == 'N' else -float(line[6]))
        plt.plot(lat, lon, '--.')
        plt.show()


if __name__ == '__main__':
    d = Data('data/data_uv24.nmea')
    d.plot_coords()
