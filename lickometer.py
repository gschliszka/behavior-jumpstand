import logging
import serial
import serial.tools.list_ports as list_ports
import struct
import time
from enum import Enum


class Arduino:
    def __init__(self, **kwargs):
        # print('Start __init__ of Arduino...')
        super(Arduino, self).__init__(**kwargs)
        self.port = None
        self.rate = kwargs.get('rate')
        self.timeout = kwargs.get('timeout')
        self.serial = self.__connect()
        time.sleep(1)
        # print('End __init__ of Arduino')

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


class RewardAmount:
    ''' Handles reward size (small, big) and contingency (e.g. 80% of reward calls actually deliver the reward).
    Both can change with time. '''

    def __init__(self, **kwargs):
        # print('Start __init__ of RewardAmount...')
        super(RewardAmount, self).__init__()
        self.contingency_percent = kwargs.get('contingency_percent')
        self.size = kwargs.get('size')
        self.time_since_start = time.time()
        self.history = []
        # print('End __init__ of RewardAmount')

    @property
    def current_size(self):
        self.history.append(self.calculate_size())
        return self.history[-1]

    def calculate_size(self):
        rewarded = [v1 > 0 for v1 in self.history]  # size can vary, get the occurrences of nonzero rewards
        print(f"rewarded: {rewarded}")
        # print(f"len(self.history): {len(self.history)}\nself.contingency_percent: {self.contingency_percent}")
        if len(rewarded) < len(self.history) * self.contingency_percent / 100:
            return self.size
        else:
            return 0


class Protocol(Arduino, RewardAmount):
    def __init__(self, rate=19200, timeout=1, contingency_percent=80, size=1):
        # print('Start __init__ of Protocol...')
        super(Protocol, self).__init__(rate=rate, timeout=timeout, contingency_percent=contingency_percent, size=size)
        self.version = self.read_line()
        self.initial_values = self.read_line()
        self.command = {i.name.lower(): i for i in self.Order}
        self.printing = False
        # print('End __init__ of Protocol')
        print(f"\tv: {self.version}\n\tinit.val: {self.initial_values}")

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

        # parameter setting
        SIDE = 20
        LEFT = 21
        RIGHT = 22
        UP = 23

        SET_TIMEOUT = 25

        # control
        INVALID_ORDER = 90
        TIMEOUT = 91
        DONE = 92

        NONE = 100

    def set_timeout(self, timeout):
        if timeout > 0 and timeout != float('inf'):
            timeout *= 1000     # convert timeout: s --> ms
        else:
            timeout = 0

        if self.printing: print(f'\n-->Lickometer.set_timeout(t): t: {timeout}, type: {type(timeout)}')
        self.write_order(self.Order.SET_TIMEOUT)
        self.write_i32(timeout)
        result = self.read_i32()
        if self.printing: print(f'-->I got (for timeout): {result}, type: {type(result)}')
        result = self.read_line()
        if self.printing: print(f'-->Lickometer.set_timeout(t): r: {result}, type: {type(result)}')

    def watch_licks(self):
        self.write_order(self.Order.WFL)
        result2 = self.read_line()
        if self.printing: print(f'->Lickometer.watch(state): {result2}')
        return self.read_line()

    def reward(self, side: str):
        # size = self.current_size
        # TODO: transmit size to arduino
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

    print(f"version: {arduino.version}")
    print(f"init val: {arduino.initial_values}")

    i_8 = []
    i_16 = []
    i_32 = []

    for a in [100, 101, 102, 200, 201, 202]:
        print(f"\na: {a}, type(a): {type(a)}\n")

        arduino.write_i8(100)
        # time.sleep(0.5)
        i8 = arduino.read_i8()
        i_8.append(i8)
        print(f"i8: {i8}, type: {type(i8)}")

        arduino.write_i16(a)
        # time.sleep(0.5)
        i16 = arduino.read_i16()
        i_16.append(i16)
        print(f"i16: {i16}, type: {type(i16)}")

        arduino.write_i32(a)
        # time.sleep(0.5)
        i32 = arduino.read_i32()
        i_32.append(i32)
        print(f"i32: {i32}, type: {type(i32)}")

    arduino.close()
    print()
    [print(v) for v in i_8]
    print()
    [print(v) for v in i_16]
    print()
    [print(v) for v in i_32]
    exit(111)

    arduino.set_timeout(100)
    arduino.set_timeout(float('inf'))
    arduino.set_timeout(-100)

    t = 0

    write = arduino.write_order
    read = arduino.read_order   # arduino.read_i8 --> int

    arduino.close()
    exit(103)

    for command in order:
        print(command)
        write(command)
        time.sleep(t)
        print(read().value)

    time.sleep(2)
    arduino.close()
