import time
import json
from influxdb import InfluxDBClient
from influxdb import SeriesHelper
from datetime import datetime
from serial import Serial
from os import path
import logging
from configparser import ConfigParser

logging.basicConfig(filename='NTC100 '+datetime.now().strftime("%H%M%S")+'.log',
                    level=logging.WARNING, format='%(asctime)s %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S')
config = ConfigParser()
# def values:
config['influxdb'] = {'host': 'localhost', 'port': '8086', 'user': 'root',
                      'pass': 'root', 'db': 'mydb','retention_days':'30'}
config['comport'] = {'name': 'COM1', 'boudrate': '57600'}
config['logging'] = {'enabled':'True'}

def timenow():
    return datetime.now().strftime('%m.%d.%Y %H:%M:%S')

if not path.exists('config.ini'):
    print(timenow(), 'No config! It will be created with def values...')
    logging.warning('No config! It will be created with def values...')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
else:
    config.read('config.ini')

myclient = InfluxDBClient(config['influxdb']['host'], config['influxdb']['port'],
                          config['influxdb']['user'], config['influxdb']['pass'],
                          config['influxdb']['db'])

tmp_data = {}

class MySeriesHelper(SeriesHelper):
    # Meta class stores time series helper configuration.
    class Meta:
        # The client should be an instance of InfluxDBClient.
        client = myclient
        # The series name must be a string. Add dependent fields/tags in curly brackets.
        # series_name = 'events.stats.{server_name}'
        series_name = 'NTC100'
        # Defines all the fields in this time series.
        fields = ['curr_temp', 'task_temp', 'curr_work', 'frame', 'time_resp', 'dev_resp']
        # Defines all the tags for the series.
        tags = ['dev_addr']
        # Defines the number of data points to store prior to writing on the wire.
        bulk_size = 16
        # autocommit must be set to True when using bulk_size
        autocommit = True

try:
    ser = Serial(config['comport']['name'], config['comport']['boudrate'], timeout=15)
    while True:
        inbytes = ser.readline()
        if inbytes:
            try:
                inbytes = inbytes.decode("ascii")
                print(timenow(), inbytes.strip())
                logging.warning(inbytes.strip())
                try:
                    data = json.loads(inbytes)
                    if data != tmp_data:
                        tmp_data = data
                        for dev in sorted(data):
                            MySeriesHelper(dev_addr=dev, curr_temp=data[dev][0], task_temp=data[dev][1],
                                           curr_work=data[dev][2], frame=data[dev][3], time_resp=data[dev][4],
                                           dev_resp=data[dev][5])
                        try:
                            MySeriesHelper.commit()
                        except Exception as msg:
                            print(timenow(), msg)
                            logging.error(msg)
                    else: 
                        print (timenow(),'^ Dublicated data, not write in db')
                        logging.warning('^ Dublicated data, not write in db')
                except Exception as msg:
                    print(timenow(),'^ Corrupted json')
                    print(timenow(), msg)
                    logging.warning('^ Corrupted json')
                    logging.warning(msg)
            except Exception as msg:
                print(timenow(),'^ Corrupted ascii')
                print(timenow(),msg)
                logging.warning('^ Corrupted ascii')
                logging.warning(msg)
        time.sleep(1)
except Exception as msg:
    print(timenow(), 'Can`t open ', config['comport']['name'])
    print(timenow(), msg)
    logging.warning('Can`t open ', config['comport']['name'])
    logging.warning(msg)
quit()
