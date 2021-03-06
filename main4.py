import time
import json
from influxdb import InfluxDBClient
from influxdb import SeriesHelper
from serial import Serial
from os import path
import logging.handlers
from configparser import ConfigParser
import sys
from list_serial_ports import serial_ports

# conf logging
levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
console = logging.StreamHandler()
console.setFormatter(formatter)
filehandler = logging.handlers.RotatingFileHandler('NTC100.log', maxBytes=1048576, backupCount=5)
# filehandler = logging.handlers.TimedRotatingFileHandler('NTC1001.log', when='M', backupCount=7)

filehandler.setFormatter(formatter)
log.addHandler(console)
log.addHandler(filehandler)

log.info('Start application')

config = ConfigParser()
# def values:
config['influxdb'] = {'host': 'localhost', 'port': '8086', 'user': 'root',
                      'pass': 'root', 'db': 'mydb', 'retention_days': '30'}
config['comport'] = {'name': 'COM1', 'boudrate': '57600'}
config['logging'] = {'level': 'INFO', '; available levels' : ','.join(levels.keys())}

if not path.exists('config.ini'):
    log.warning('No config! It will be created with def values...')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
else:
    config.read('config.ini')
log.info('Logging level: ' + config['logging']['level'])
log.setLevel(config['logging']['level'])


myclient = InfluxDBClient(config['influxdb']['host'], config['influxdb']['port'],
                          config['influxdb']['user'], config['influxdb']['pass'],
                          config['influxdb']['db'])

tmp_data = {}
msges = ['Start', 'Reset', 'Onboa']


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
        comm_data = inbytes = ser.readline()
        if inbytes:
            try:
                inbytes = inbytes.decode("ascii")
                if not (inbytes[:5] in msges):
                    log.debug(inbytes.strip())
                    try:
                        data = json.loads(inbytes.strip())
                        if data != tmp_data:
                            tmp_data = data
                            for dev in sorted(data):
                                MySeriesHelper(dev_addr=dev, curr_temp=data[dev][0], task_temp=data[dev][1],
                                               curr_work=data[dev][2], frame=data[dev][3], time_resp=data[dev][4],
                                               dev_resp=data[dev][5])
                            try:
                                MySeriesHelper.commit()
                            except Exception as msg:
                                log.error('Coul`d not connect to influxdb')
                                log.error(msg)
                        else:
                            log.warning('^ Dublicated data, not write in db')
                    except Exception as msg:
                        log.warning('Corrupted json -> ' + inbytes.strip())
                        log.warning(msg)
                else:
                    log.info(inbytes.strip())
            except Exception as msg:
                log.warning('Corrupted ascii -> ' + repr(comm_data))
                log.warning(msg)
        time.sleep(1)
except Exception as msg:
    log.error('Can`t open ' + config['comport']['name'])
    log.error(msg)
    log.error('Available ports: %s.', ', '.join(serial_ports()))
sys.exit()
