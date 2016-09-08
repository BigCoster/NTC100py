import serial
import time
import json
from influxdb import InfluxDBClient
from influxdb import SeriesHelper

# InfluxDB connections settings
host = 'localhost'
port = 8086
user = 'root'
password = 'root'
dbname = 'mydb'
myclient = InfluxDBClient(host, port, user, password, dbname)


# myclient.drop_database(dbname)
# Uncomment the following code if the database is not yet created
myclient.create_database(dbname)
myclient.create_retention_policy('awesome_policy', '3d', 3, default=True)

ser = serial.Serial('COM1', 57600, timeout=1)


class MySeriesHelper(SeriesHelper):
    # Meta class stores time series helper configuration.
    class Meta:
        # The client should be an instance of InfluxDBClient.
        client = myclient
        # The series name must be a string. Add dependent fields/tags in curly brackets.
        # series_name = 'events.stats.{server_name}'
        series_name = 'NTC100'
        # Defines all the fields in this time series.
        fields = ['task_temp', 'curr_temp']
        # Defines all the tags for the series.
        tags = ['dev_addr']
        # Defines the number of data points to store prior to writing on the wire.
        bulk_size = 16
        # autocommit must be set to True when using bulk_size
        autocommit = True


with ser:
    ser.write(b'g')
    time.sleep(0.1)
    inbytes = ser.readline()
    inbytes = inbytes.decode("ascii")
    print(inbytes)
    temp = json.loads(inbytes)
    # print(json.dumps(temp, sort_keys=True, indent=2))

    ser.write(b's')
    time.sleep(0.1)
    inbytes = ser.readline()
    inbytes = inbytes.decode("ascii")
    print(inbytes)
    task = json.loads(inbytes)
    # print(json.dumps(task, sort_keys=True, indent=2))
ser.close()

# The following will create *five* (immutable) data points.
# Since bulk_size is set to 5, upon the fifth construction call, *all* data
# points will be written on the wire via MySeriesHelper.Meta.client.
for dev in temp:
    # print(dev,':',temp[dev],',',task[dev])
    MySeriesHelper(dev_addr=dev, task_temp=task[str(dev)], curr_temp=temp[str(dev)])

# To inspect the JSON which will be written, call _json_body_():
# print(MySeriesHelper._json_body_())

# To manually submit data points which are not yet written, call commit:
MySeriesHelper.commit()

# print("Read ast_dataFrame")
# data = myclient.query("select * from NTC100")
# print(data)

quit()
