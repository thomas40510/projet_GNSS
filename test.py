# pyGPS created by Lachlan Page
# Intended for use with GSTAR IV GPS
import serial
import math


class pyGPS:
    """ pyGPS allows for quick use of GSTAR IV gps """

    def __init__(self, baud_rate):
        self.m_serial = serial.Serial(port="COM5", baudrate=baud_rate, timeout=5)

        # Members vars related to gps function
        self.latitude = 0
        self.latitude_minutes = 0
        self.latitude_direction = "NULL"

        self.longitude = 0
        self.longitude_minutes = 0
        self.longitude_direction = "NULL"

        # UTC time of when fix was taken
        self.fix_time = 0

        self.status_code = 0

        self.num_satellites = 0

        self.horizontal_dilation = 0

        self.mean_altitude = 0

    """ updates the GPS data by reading serial and sets members """

    def updateData(self):
        raw_data = self.m_serial.readline()
        data_line = raw_data.decode('utf-8')
        data = data_line.split(",")

        # print data

        # returns lots of satellite data, we only care about GPGGA for the moment
        # First 2/3 decimal places of lat/long correspond to the actual lat/long
        # the rest of digits corespond to the degrees
        # 4807.038 -> 48 . 0703 degrees
        # South direction corresponds to a negative lat/long

        # Status code is a enum of 1 to 8 representing signal fix quality
        if data[0] == "$GPGGA":
            print(data)
            # try:
            self.fix_time = data[1]

            self.latitude = float(data[2])
            self.latitude_minutes = self.latitude % 100
            self.latitude = math.floor(self.latitude / 100)
            self.latitude_direction = data[3]

            if (self.latitude_direction == "S"):
                self.latitude = -self.latitude

            self.longitude = float(data[4])
            self.longitude_minutes = self.longitude % 100
            self.longitude = math.floor(self.longitude / 100)
            self.longitude_direction = data[5]

            if (self.longitude_direction == "W"):
                self.longitude = -self.longitude

            self.status_code = data[6]

            self.num_satellites = data[7]

            self.horizontal_dilation = data[8]

            self.mean_altitude = data[9]
            # except ValueError as e:
                # print(e)

        # Slows down GPS updating but handles lock on during startup
        else:
            self.updateData()

        # GPGSV relates to all satellites that are in view of position
        """
        if(data[0] == "$GPGSV"):
            prn_number = data[4]
            elevation_degrees = data[5]
            azimuth = data[6]
            snr = data[7]
            #Second SV
            prn_number_two = data[8]
            elevation_degrees_two = data[9]
            azimuth_two = data[10]
            snr_two = data[11]
            prn_number_three = data[12]
            elevation_degrees_three = data[13]
            azimuth_three = data[14]
            snr_three = data[15]
            print("Satellite: ")
            print("PRN: {}".format(prn_number))
            print("Elevation: {}".format(elevation_degrees))
            print("Azimuth: {}".format(azimuth))
            print("SNR: {}".format(snr))
            print("\n")
            print("Satellite Two: ")
            print("PRN: {}".format(prn_number_two))
            print("Elevation: {}".format(elevation_degrees_two))
            print("Azimuth: {}".format(azimuth_two))
            print("SNR: {}".format(snr_two))
            print("\n")
            print("Satellite Three: ")
            print("PRN: {}".format(prn_number_three))
            print("Elevation: {}".format(elevation_degrees_three))
            print("Azimuth: {}".format(azimuth_three))
            print("SNR: {}".format(snr_three))
            print("\n")
        """

    """ Pretty print of basic satellite data """

    def printData(self):
        print("Data Recieved: ")
        print("Status Code: {}".format(self.status_code))
        print("Lat: {} {}".format(self.latitude, self.latitude_minutes))
        print("Long: {} {}".format(self.longitude, self.longitude_minutes))
        print("Mean Altitude: {}".format(self.mean_altitude))
        print("Num Satellites: {}".format(self.num_satellites))
        print("Horiz Dilation: {}".format(self.horizontal_dilation))
        print("\n")
        # print(self.latitude, self.longitude, self.status_code)
