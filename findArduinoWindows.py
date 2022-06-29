import serial.tools.list_ports
import logging


def get_ports():
    ports = serial.tools.list_ports.comports()
    return ports


def findArduino(portsFound):
    commPort = 'None'
    numConnection = len(portsFound)
    for i in range(0,numConnection):
        port = portsFound[i]
        strPort = str(port)
        logging.info(strPort)
        if 'Arduino' in strPort:
            splitPort = strPort.split(' ')
            commPort = (splitPort[0])
    return commPort


def connect(rate=9600):
    foundPorts = get_ports()
    connectPort = findArduino(foundPorts)
    #connectPort = 'COM3'
    if connectPort != 'None':
        logging.info('Connected to ' + connectPort)
        return connectPort
    else:
        logging.warning('Arduino not found!')
        exit('Connection failed')
        return 'None'


def main():
    ser = connect()
    print(ser)


if __name__ == '__main__':
    main()
