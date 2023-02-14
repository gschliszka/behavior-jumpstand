import logging
import random

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
        self.rew_size = kwargs.get('rew_size')
        self.time_since_start = time.time()
        self.history = []
        # print('End __init__ of RewardAmount')

    # @property
    def current_size(self):
        print('-----------------')
        self.history.append(self.calculate_size())
        print(f"self.history: {self.history}")
        print('-----------------\n')
        return self.history[-1]

    def calculate_size(self):
        rewarded = [v1 > 0 for v1 in self.history]  # size can vary, get the occurrences of nonzero rewards
        print(f"rewarded: {rewarded} --> sum: {sum(rewarded)}")
        print(f"len(self.history): {len(self.history)}\nself.contingency_percent: {self.contingency_percent}")
        if len(rewarded) == 0:
            return self.rew_size
        if sum(rewarded) < len(self.history) * self.contingency_percent / 100:
            return self.rew_size
        else:
            return 0


class Protocol(Arduino, RewardAmount):
    def __init__(self, rate=19200, timeout=1, contingency_percent=80, rew_size=1):
        # print('Start __init__ of Protocol...')
        super(Protocol, self).__init__(rate=rate, timeout=timeout, contingency_percent=contingency_percent, rew_size=rew_size)
        self.version = self.read_line()
        self.initial_values = self.read_line()
        self.command = {i.name.lower(): i for i in self.Order}
        self.printing = True
        # print('End __init__ of Protocol')
        # print(f"\tv: {self.version}\n\tinit.val: {self.initial_values}")

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
        ALL = 24

        SET_TIMEOUT = 25
        SET_SIZE = 26
        CALIBRATE = 27

        # control
        INVALID_ORDER = 90
        TIMEOUT = 91
        DONE = 92

        NONE = 100

    '''
    def set_size(self, size):
        self.write_order(self.Order.SET_SIZE)
        self.write_i16(size)
        result = self.read_i16()
        if self.printing: print(f'Lickometer.set_size({result})')

    def calibrate_pump(self, pump:list, motor_time, motor_speed):
        if motor_time > 0 and motor_time != float('inf'):
            motor_time *= 1000  # convert timeout: s --> ms
        else:
            motor_time = 0

        allowed_pumps = ['up', 'left', 'right']
        self.write_order(self.Order.CALIBRATE)

        self.write_i32(motor_time)
        time = self.read_i32()

        self.write_i16(motor_speed)
        speed = self.read_i16()

        if self.printing: print(f'Lickometer.calibrate_pump({time}, {speed})')

        """for p in pump:
            self.write_order(self.Order.CALIBRATE)

            self.write_order(self.command[p])
            self.write_i32(motor_time)
            self.write_i8(motor_speed)

            side = self.read_order()
            time = self.read_i32()
            speed = self.read_i8()

            if self.printing: print(f'Lickometer.calibrate_pump({side}, {time}, {speed})')
        """

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

    def reward(self, side: str, size=-1):
        # size = self.current_size

        # set reward size
        if not size == -1:
            self.set_size(size)

        # set rewarding side
        self.write_order(self.Order.SIDE)
        self.write_order(self.command[side])
        result = self.read_line()
        if self.printing: print(f'-->Lickometer.reward(side): {result}')

        # give reward
        self.write_order(self.Order.REW)
        result2 = self.read_line()
        if self.printing: print(f'->Lickometer.reward(state): {result2}')
        return self.read_line()

    def punish(self):
        self.write_order(self.Order.NOR)
        result = self.read_line()
        if self.printing: print(f'-->Lickometer.punish: {result}')
    '''

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


class Lickometer(Protocol):
    def __init__(self, **kwargs):
        super(Lickometer, self).__init__(**kwargs)
        self.allowed_pumps = ['up', 'left', 'right']

    def set_size(self, size, pumps=None):
        if not pumps:
            pumps = ['all']

        for p in pumps:
            # Order
            self.write_order(self.Order.SET_SIZE)
            order_result = self.read_order()
            if self.printing: print(f'Lickometer.set_size: {order_result}')

            # Parameters
            #   pump
            self.write_order(self.command[p])
            pump_result = self.read_order()
            #   size
            self.write_i16(size)
            size_result = self.read_i16()
            if self.printing: print(f'Lickometer.set_size({pump_result}, {size_result})\n')

    def calibrate_pump(self, motor_time, motor_speed, pumps=None):
        if not pumps:
            pumps = ['all']

        # Validate motor_time and motor_speed
        if motor_time > 0 and motor_time != float('inf'):
            motor_time *= 1000  # convert motor_time: s --> ms
            motor_time = int(motor_time)
        else:
            motor_time = 0

        if motor_speed < 0:
            motor_speed = 0
        if motor_speed > 255:
            motor_speed = 255

        for p in pumps:
            # Order
            self.write_order(self.Order.CALIBRATE)
            order_result = self.read_order()
            if self.printing: print(f'Lickometer.calibrate_pump: {order_result}')

            # Parameters
            #   pump
            self.write_order(self.command[p])
            pump_result = self.read_order()
            #   motor_time
            self.write_i32(motor_time)
            time_result = self.read_i32()
            #   motor_speed
            self.write_i16(motor_speed)
            speed_result = self.read_i16()
            if self.printing: print(f'Lickometer.calibrate_pump({pump_result}, {time_result}, {speed_result})\n')

    def set_timeout(self, timeout):
        # Validate timeout
        if timeout > 0 and timeout != float('inf'):
            timeout *= 1000     # convert timeout: s --> ms
        else:
            timeout = 0

        # Order
        self.write_order(self.Order.SET_TIMEOUT)
        order_result = self.read_order()
        if self.printing: print(f'Lickometer.set_timeout: {order_result}')

        # Parameters
        self.write_i32(timeout)
        time_result = self.read_i32()
        inf_result = self.read_order()
        if self.printing: print(f'Lickometer.set_timeout({time_result}, finite timeout={inf_result})\n')

    def watch_licks(self):
        """
        Set Lickometer in WFL (wait for licking) state and give feedback
        Returns
        -------
        str: 'abc' a: up, b: left, c: right --> a, b, c: lick=1 & no_lick=0
        """

        # Order
        self.write_order(self.Order.WFL)
        order_result = self.read_order()
        if self.printing: print(f'Lickometer.watch_licks: {order_result}')

        # Wait for response
        while self.input() < 1:
            pass

        # Parameters
        lick_result = self.read_i8()
        # lick_result2 = self.read_line()
        if self.printing: print(f'Lickometer.watch_licks({lick_result}-->{lick_result:03})\n')
        # print(f'Lickometer.watch_licks({lick_result2})')

        return f"{lick_result:03}"

    def set_side(self, side: str):
        # Order
        self.write_order(self.Order.SIDE)
        order_result = self.read_order()
        if self.printing: print(f'Lickometer.set_side: {order_result}')

        # Parameter
        self.write_order(self.command[side])
        side_selected = self.read_order()
        side_result = self.read_order()
        if self.printing: print(f'Lickometer.set_side({side_selected}, {side_result})\n')

    def reward(self, side: str, size=-1):
        # Set reward size
        if not size == -1:
            self.set_size(size)
        # 'up' lickometer: 100%
        elif side == 'up':
            self.set_size(self.rew_size)
        elif side != 'up':
            s = self.current_size()
            self.set_size(s)

        # Set rewarding side
        self.set_side(side=side)

        # Give reward
        # Order
        self.write_order(self.Order.REW)
        order_result = self.read_order()
        if self.printing: print(f'Lickometer.reward: {order_result}')
        time.sleep(0.1)

        # Results
        reward_result = self.read_order()
        if self.printing: print(f'Lickometer.reward({reward_result})\n')
        return reward_result

    def punish(self):
        self.write_order(self.Order.NOR)
        result = self.read_line()
        if self.printing: print(f'Lickometer.punish: {result}')


if __name__ == '__main__':
    arduino = Lickometer()
    order = arduino.Order

    print(f"version: {arduino.version}")
    print(f"init val: {arduino.initial_values}")

    # arduino.calibrate_pump(['up'], 1000, 200)
    # arduino.calibrate_pump(['left', 'right'], 2000, 180)

    """
    arduino.calibrate_pump([], 2, 200)
    print('Reward up')
    arduino.reward('up')
    time.sleep(3)
    """

    """
    arduino.set_size(2, ['up', 'left'])

    arduino.set_size(1)

    arduino.calibrate_pump(0.02, 200, ['left', 'right'])
    arduino.calibrate_pump(0.1, 255)

    arduino.set_timeout(3)
    arduino.set_timeout(float('inf'))

    arduino.set_side('up')
    """

    arduino.set_size(1)
    arduino.calibrate_pump(2, 255)

    print('\n\t----Testing:----\n\n')

    # arduino.set_timeout(5)
    resp = arduino.watch_licks()
    print(f"I've got: {resp}, type: {type(resp)}")

    arduino.reward('up')
    arduino.calibrate_pump(3, 200, ['left'])
    arduino.reward('left')
    time.sleep(5)
    arduino.set_size(3, ['left'])
    arduino.reward('left', 3)
    print("Fin")

    exit(214)

    arduino.reward('left', 1)
    time.sleep(0.5)
    arduino.reward('up', 1)
    time.sleep(0.5)
    arduino.reward('right', 1)
    time.sleep(0.5)
    arduino.reward('up', 1)
    time.sleep(2)
    arduino.reward('cat')
    print("Itt vok")
    time.sleep(3)

    exit(111)

    for i in range(20):
        print(f"Iteration: {i}.")
        random.shuffle(sides)
        arduino.reward(sides[0])
        time.sleep(0.2)

    exit(111)
    arduino.calibrate_pump([], 1, 255)
    print('Reward left')
    arduino.reward('left')
    time.sleep(1+1)

    #exit(519)

    arduino.set_size(2)
    print('Reward left')
    arduino.reward('left')
    time.sleep(2 + 1)

    arduino.set_size(3)
    print('Reward left')
    arduino.reward('left')
    time.sleep(3 + 1)

    arduino.calibrate_pump([], 3, 200)
    print('Reward right')
    arduino.reward('right')
    time.sleep(3)

    arduino.calibrate_pump([], 3, 255)
    print('Reward right')
    arduino.reward('right')
    time.sleep(3)

    arduino.calibrate_pump([], 3, 200)
    print('Reward right')
    arduino.reward('right')
    time.sleep(3)

    exit(518)

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
