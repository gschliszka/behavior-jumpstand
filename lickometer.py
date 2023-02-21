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

        # sides (pump & lick sensor)
        ALL = 20
        LEFT = 21
        RIGHT = 22
        UP = 23

        # parameter setting
        SET_SIDE = 30
        SET_TIMEOUT = 31
        SET_SIZE = 32
        CALIBRATE = 33
        SET_WASHSPEED = 34

        # control
        INVALID_ORDER = 90
        TIMEOUT = 91
        DONE = 92

        NONE = 100

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

    def set_wash_speed(self, speed: int, pumps=None):
        """
        Set the motor speed for washing and TTL-controlled rewarding.

        Parameters
        ----------
        speed : int
            The new speed applied for washing or TTL-controlled rewarding.
        pumps : list, optional
            List of pumps that changes. (Default: ['all'])

        Returns
        -------

        """

        if not pumps:
            pumps = ['all']

        for p in pumps:
            # Order
            self.write_order(self.Order.SET_WASHSPEED)
            order_result = self.read_order()
            if self.printing: print(f'Lickometer.set_wash_speed: {order_result}')

            # Parameters
            #   pump
            self.write_order(self.command[p])
            pump_result = self.read_order()
            #   wash speed
            self.write_i16(speed)
            speed_result = self.read_i16()
            if self.printing: print(f'Lickometer.set_wash_speed({pump_result}, {speed_result})\n')

    def set_size(self, size: int, pumps=None):
        """
        Set the reward size of requested pumps.

        Parameters
        ----------
        size : int
            reward_length = motor_time * size
        pumps : list, optional
            List of pumps that changes. (Default: ['all'])

        Returns
        -------

        """

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
        """
        Set reward's motor time and motor speed of requested pumps.

        Parameters
        ----------
        motor_time : int, [0; inf)
            Motor time in seconds.
        motor_speed : int, [0; 255]
            Speed value of the pump which goes to the motor shield.
        pumps : list, optional
            List of pumps that changes. (Default: ['all'])

        Returns
        -------

        """

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
        """
        Set duration of waiting for licking in WFL state.

        Parameters
        ----------
        timeout : int, (0; inf]
            Duration of waiting in seconds.

        Returns
        -------

        """

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
        """
        Set the next rewarded side before rewarding.

        Parameters
        ----------
        side : str
            One of the allowed side

        Returns
        -------

        """

        # Order
        self.write_order(self.Order.SET_SIDE)
        order_result = self.read_order()
        if self.printing: print(f'Lickometer.set_side: {order_result}')

        # Parameter
        self.write_order(self.command[side])
        side_selected = self.read_order()
        side_result = self.read_order()
        if self.printing: print(f'Lickometer.set_side({side_selected}, {side_result})\n')

    def reward(self, side: str, size=-1):
        """
        Give reward by the requested pump. Up always rewarding but left & right use current size.
        If size specified that will be set (not current size).

        Parameters
        ----------
        side: str
            Where the reward must be given.
        size : int, optional
            If necessary user can specify the size.

        Returns
        -------

        """
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