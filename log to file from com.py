import time
from datetime import datetime
from serial import Serial
import logging


logging.basicConfig(filename='NTC100rs485debug '+datetime.now().strftime("%H%M%S")+'.log',
                    level=logging.WARNING, format='%(asctime)s %(message)s')
# , datefmt = '%m.%d.%Y %H:%M:%S'
line =[]

with Serial('COM2', 9600, timeout=0) as ser:
    while True:
        for c in ser.read():
            line.append(chr(c))
            if chr(c) == '\r':
                joined_line = ''.join(str(v) for v in line)
                print("{} {}".format(datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f"),joined_line.strip()))
                logging.warning(joined_line.strip())
                line = []
                break
quit()

