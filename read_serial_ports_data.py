import serial
import serial.tools.list_ports as list_ports

fixed_length = 15


def main():
    com_port = list_ports.comports()
    for i, ind in enumerate(com_port):
        print(f'\nUSB device {i}:')
        print(f'> {"device":<{fixed_length}}: {ind.device}')
        print(f'> {"name":<{fixed_length}}: {ind.name}')
        print(f'> {"description":<{fixed_length}}: {ind.description}')
        print(f'> {"hwid":<{fixed_length}}: {ind.hwid}')
        print(f'> {"vid":<{fixed_length}}: {ind.vid}')
        print(f'> {"pid":<{fixed_length}}: {ind.pid}')
        print(f'> {"serial_number":<{fixed_length}}: {ind.serial_number}')
        print(f'> {"location":<{fixed_length}}: {ind.location}')
        print(f'> {"manufacturer":<{fixed_length}}: {ind.manufacturer}')
        print(f'> {"product":<{fixed_length}}: {ind.product}')
        print(f'> {"interface":<{fixed_length}}: {ind.interface}')


if __name__ == '__main__':
    main()
