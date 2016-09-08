import time
import json
from influxdb import InfluxDBClient
from influxdb import SeriesHelper
import os
from serial import Serial
import logging

logging.basicConfig(filename='NTC100.log', level=logging.WARNING, format='%(asctime)s %(message)s', datefmt='%m.%d.%Y %I:%M:%S')

# InfluxDB connections settings
host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'mydb'
comport = 'COM1'
myclient = InfluxDBClient(host, port, user, password, dbname)

# myclient.drop_database(dbname)
# Uncomment the following code if the database is not yet created
# myclient.create_database(dbname)
# myclient.create_retention_policy('awesome_policy', '3d', 3, default=True)


class MySeriesHelper(SeriesHelper):
    # Meta class stores time series helper configuration.
    class Meta:
        # The client should be an instance of InfluxDBClient.
        client = myclient
        # The series name must be a string. Add dependent fields/tags in curly brackets.
        # series_name = 'events.stats.{server_name}'
        series_name = 'NTC100'
        # Defines all the fields in this time series.
        fields = ['curr_temp', 'task_temp', 'frame']
        # Defines all the tags for the series.
        tags = ['dev_addr']
        # Defines the number of data points to store prior to writing on the wire.
        bulk_size = 16
        # autocommit must be set to True when using bulk_size
        autocommit = True


with Serial(comport, 57600, timeout=2) as ser:
    while True:    
        ser.write(b'a')
        time.sleep(0.5)
        inbytes = ser.readline()

        logging.warning(inbytes)
        # logging.warning("get data: {}".format(inbytes))

        print(inbytes)
        if inbytes:
            try:
                inbytes = inbytes.decode("ascii")
                # print("Input data: ", inbytes.strip())
                # print(inbytes.strip())

                try:
                    data = json.loads(inbytes)
                    # print(json.dumps(data, sort_keys=True, indent=None))

                    # print("Storred data:")
                    for dev in sorted(data):
                        # print("{0}:[{1},{2},{3}]".format(dev, data[dev][0], data[dev][1], data[dev][2]))
                        MySeriesHelper(dev_addr=dev, curr_temp=data[dev][0], task_temp=data[dev][1], frame=data[dev][2])

                    # To inspect the JSON which will be written, call _json_body_():
                    # print(MySeriesHelper._json_body_())

                    # To manually submit data points which are not yet written, call commit:
                    MySeriesHelper.commit()

                    # print("Read ast_dataFrame")
                    # data = myclient.query("select * from NTC100")
                    # print(data)
                except Exception:
                    print('Corrupted json.')
                    logging.warning('Bad json.')
            except Exception:
                print('Corrupted ascii.')
                logging.warning('Corrupted ascii.')
        else:
            print('Empty data.')
        time.sleep(2)
quit()
