import numpy as np
import matplotlib.pyplot as plt
import pynmeagps as nmea


def np_open(filename):
    """Open a file and return a numpy array."""
    # data = np.loadtxt(filename, delimiter=',', dtype=str)
    return np.loadtxt(filename, delimiter='\n', dtype=str)


def select_data(data, data_type='GGA'):
    """
    Select lines given a type of data to extract.

    :param data: raw nmea data
    :param data_type: type of data to extract
    :return:
    """
    L = [line.split(',') for line in data]
    res = []
    for line in L:
        if line[0] == f"$GP{data_type}":
            res.append(line)
    return res


def plot_data(data):
    """
    Plot data.

    :param data:
    """
    lat = []
    lon = []
    for line in data:
        lat.append(float(line[4]) if line[5] == 'E' else -float(line[4]))
        lon.append(float(line[2]) if line[3] == 'N' else -float(line[2]))
    plt.plot(lat, lon)
    plt.show()


if __name__ == '__main__':
    data = np_open('data/data_uv24.nmea')
    print(select_data(data))
    plot_data(select_data(data))
