import serial
import serial.tools.list_ports
import time
import platform
from constant import *


class SerialConnector:
    def __init__(self, rate=9600, timeout=1):
        self.rate = rate
        self.timeout = timeout
        self.waitForConf = False
        self.ser = self.connect()
        self.ser.reset_input_buffer()

    def connect(self):
        os = platform.system()
        if os == 'Windows':
            import findArduinoWindows as fA
            port = fA.connect(self.rate)
        elif os == 'Linux':
            port = '/dev/ttyACM0'
        else:
            raise TypeError(f"Only Windows and Linux are allowed OS! You want to run on a {os} machine")

        return serial.Serial(port, self.rate, timeout=self.timeout)

    def readlines(self, incoming=3):
        line = []
        while self.ser.inWaiting() > 0: #len(line) < incoming:
            inp = self.ser.readline().decode('utf-8')[:-2]
            line.append([inp[0], inp[1:]])
        return line
        #return [[line.decode('utf-8')[0], line.decode('utf-8')[1:-2]] for line in self.ser.readlines()]

    def write(self, command):
        self.ser.write(command.encode('utf-8'))
        #self.ser.write(command2.encode('utf-8'))

    def input(self):
        return self.ser.inWaiting()

    def close(self):
        self.ser.close()
        time.sleep(0.5)


def main():
    Arduino = SerialConnector(rate=19200)
    while Arduino.input() == 0:
        pass
    line = Arduino.readlines(incoming=1)
    print(line)
    print(line[0][1][:4])
    if '#1.0' in line[0][1]:
        print('Connected')
        Arduino.write('')

    """
    data = []
    process = []
    while True:
        if Arduino.input() > 0:
            data.append(Arduino.readlines())

        if len(data) > 0 and process == []:
            print(data)
            process = data.pop(0)

        if process[]
    """

    Arduino.write(f"{CAT}")
    time.sleep(1)
    print(Arduino.readlines())
    line = []
    while not line:
        line = Arduino.readlines()
        if line:
            print(line)
            print('Cat in position')
    #time.sleep(2)
    print(Arduino.readlines())
    Arduino.write(f"{RaC}{LEFT}{2000}")
    time.sleep(3)
    print(Arduino.readlines())
    Arduino.close()


if __name__ == '__main__':
    main()
