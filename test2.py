# Simple example use of using pyGPS
import test
import time

# Setup pyGPS with a baud rate of 4800
gps = test.pyGPS(4800)
file = f"data/gps_export_{time.time()}.txt"

while True:
    # gps.updateData()

    raw_data = gps.m_serial.readline()
    data_line = raw_data.decode('utf-8')
    data = data_line.split(",")
    # if (data[0] == "$GPGGA"):
    #             f = open('DONNEES_GPS.txt','w')
    #             for element in data:
    #                 f.write(element+",")
    #             f.write("\n")
    print(data)
    with open(file, 'a') as f:
        f.write(str(data).replace('[', '').replace(']', '') + "\n")

    time.sleep(2)
    gps.printData()



