import logging
import serial
import serial.tools.list_ports as list_ports
import struct
import time
from enum import Enum


class Arduino:
    def __init__(self, rate=19200, timeout=1):
        self.port = None
        self.rate = rate
        self.timeout = timeout
        self.serial = self.__connect()
        time.sleep(1)

    def __connect(self):
        com_ports = list_ports.comports()
        for port in com_ports:
            name = port.manufacturer
            if name and 'Arduino' in name:
                print(f'Arduino found, port = {port.device}')
                self.port = port.device
        if self.port is None:
            print('No Arduino found, exit')
            exit(1)
        return serial.Serial(self.port, self.rate, timeout=self.timeout)

    def input(self):
        return self.serial.inWaiting()

    def read_line(self):
        while self.input() == 0:
            pass
        line = self.serial.readline()
        return line.strip().decode()

    def close(self):
        self.serial.close()
        time.sleep(0.5)
        print(f'Port {self.port} is closed')


class Protocol(Arduino):
    def __init__(self, rate=19200, timeout=1):
        super(Protocol, self).__init__(rate, timeout)
        self.version = self.read_line()
        self.initial_values = self.read_line()
        self.command = {i.name.lower(): i for i in self.Order}
        self.printing = True

    class Order(Enum):
        """
        Pre-defined orders
        """
        # states
        OFF = 0
        CAT = 1
        STM = 2
        WFL = 3
        NOR = 4
        REW = 5

        SIDE = 20
        LEFT = 21
        RIGHT = 22
        UP = 23

        # control
        INVALID_ORDER = 90
        TIMEOUT = 91
        DONE = 92

        NONE = 100

    def watch_licks(self):
        self.write_order(self.Order.WFL)
        result2 = self.read_line()
        if self.printing: print(f'->Lickometer.watch(state): {result2}')
        return self.read_line()

    def reward(self, side: str):
        self.write_order(self.Order.SIDE)
        self.write_order(self.command[side])
        result = self.read_line()
        if self.printing: print(f'-->Lickometer.reward(side): {result}')
        self.write_order(self.Order.REW)
        result2 = self.read_line()
        if self.printing: print(f'->Lickometer.reward(state): {result2}')
        return self.read_line()

    def punish(self):
        self.write_order(self.Order.NOR)
        result = self.read_line()
        if self.printing: print(f'-->Lickometer.punish: {result}')

    def read_order(self):
        """
        :return: (Order Enum Object)
        """
        order_read = self.read_i8()
        try:
            return self.Order(order_read)
        except:
            # logging.warning(f"\nNot a valid order: {order_read}")
            return order_read # self.Order.INVALID_ORDER

    def read_i8(self):
        """
        :return: (int8_t)
        """
        return struct.unpack('<b', bytearray(self.serial.read(1)))[0]

    def read_i16(self):
        """
        :return: (int16_t)
        """
        return struct.unpack('<h', bytearray(self.serial.read(2)))[0]

    def read_i32(self):
        """
        :return: (int32_t)
        """
        return struct.unpack('<l', bytearray(self.serial.read(4)))[0]

    def write_order(self, order):
        """
        :param order: (Order Enum Object)
        """
        self.write_i8(order.value)

    def write_i8(self, value):
        """
        :param value: (int8_t)
        """
        if -128 <= value <= 127:
            self.serial.write(struct.pack('<b', value))
        else:
            print("Value error:{}".format(value))

    def write_i16(self, value):
        """
        :param value: (int16_t)
        """
        self.serial.write(struct.pack('<h', value))

    def write_i32(self, value):
        """
        :param value: (int32_t)
        """
        self.serial.write(struct.pack('<l', value))

    def write_ov(self, o, v):
        """
        Write order-value pair into serial port
        :param o: order
        :param v: value
        """
        try:
            print(f"Send order: {self.Order(o).name}")
            self.write_order(self.Order(o))
        except:
            print(f"Send order: {o}")
            self.write_i8(o)
        print(f"Send value: {v}")
        self.write_i16(v)

    def read_ovt(self, timeout=1):
        """
        Read order, value, time
        :param timeout:
        :return:
        """
        t = time.time()
        out_of_time = False
        while self.input() < 7 and not out_of_time:
            if time.time() - t > timeout:
                out_of_time = True
        if out_of_time:
            return self.Order.TIMEOUT, 0, -1
        else:
            return self.read_order(), self.read_i16(), self.read_i32()


if __name__ == '__main__':
    arduino = Protocol()
    order = arduino.Order

    print(arduino.version)
    print(arduino.initial_values)

    t = 0

    write = arduino.write_order
    read = arduino.read_order   # arduino.read_i8 --> int

    for command in order:
        print(command)
        write(command)
        time.sleep(t)
        print(read().value)

    time.sleep(2)
    arduino.close()
