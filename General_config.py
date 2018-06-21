from colorama import init, Fore
init()

sensor_list = {'K': '\x00', 'J': '\x01', 'T': '\x02', 'E': '\x03', 'N': '\x04', 'R': '\x05', 'S': '\x06', 'B': '\x07',
              'L': '\x08', 'U': '\x09', 'TC_user': '\x0a',
              '600mv': '\x11', '150mv': '\x13', '28VDC': '\x21', '12VDC': '\x23', '300VDC': '\x25', '5A': '\x30',
              '25mA': '\x31',
              'PT100': '\x40', 'PT200': '\x41', 'PT1000': '\x42', 'PT120': '\43', 'CU10': '\44', 'RTD_user': '\45',
              '12kOhm': '\x51', '1k5Ohm': '\x54', '750Ohm': '\x55', 'Poti_1k': '\x60',
              '250VAC': '\x70', '1VAC': '\x74',
              }

Calibration_input_list = (
    ('Input 25mA', 0x31, 0.02),
    ('Input 5A', 0x30, 3),
    ('Input 150mV, 600 mV, TC ', 0x11, 0.15),
    ('Input 150mV, 600 mV, TC ', 0x13, 0.15),
    ('Input 12V, 28V', 0x21, 10),
    ('Input 12V, 28V', 0x23, 10),
    ('Input 300V High', 0x26, 200),
    ('Input 300V Low', 0x25, 10),
    ('Input 750Ohm, 1500 Ohm, PT100, PT200, Cu10, Ni120', 0x54, 750),
    ('Input 750Ohm, 1500 Ohm, PT100, PT200, Cu10, Ni120', 0x55, 750),
    ('Input 12KOhm, PT1000', 0x51, 10000),
    ('Input 250VAc High', 0x70, 250),
    ('Input 250VAc Low', 0x77, 1),
    ('Input 1VAc High', 0x74, 1),
    ('Input 1VAc Low', 0x7B, 0.1)
)

wire_option_list = {'3wire': '0001', '2wire': '0000'}
analog_burnout_list = {'reserved': '00', 'upscale': '01', 'downscale': '10'}
alarm_burnout_list = {'reserved': '00', 'alarm tripped': '01', 'alarm frozen': '10'}


# Big Endian Conversion
def str_to_int(strin='', byte_index = 4, endian='big'):
    if endian == 'small':
        if byte_index == 4:
            return ord(strin[3]) * 16777216 + ord(strin[2]) * 65536 + ord(strin[1]) * 256 + ord(strin[0])
        elif byte_index == 2:
            return ord(strin[1]) * 256 + ord(strin[0])
    elif endian == 'big':
        if byte_index == 4:
            return ord(strin[0]) * 16777216 + ord(strin[1]) * 65536 + ord(strin[2]) * 256 + ord(strin[3])
        elif byte_index == 2:
            return ord(strin[0]) * 256 + ord(strin[1])


def int_to_str(input_int=1, byte_index=2, endian='big'):
    if endian == 'big':
        if byte_index == 2:
            int_code_1 = input_int / 256
            int_code_2 = input_int % 256
            return chr(int_code_1) + chr(int_code_2)
        elif byte_index == 4:
            int_code_1 = input_int / 16777216
            int_code_2 = input_int % 16777216 / 65536
            int_code_3 = input_int % 16777216 % 65536 / 256
            int_code_4 = input_int % 16777216 % 65536 % 256
            return chr(int_code_1) + chr(int_code_2) + chr(int_code_3) + chr(int_code_4)
    elif endian == 'small':
        if byte_index == 2:
            int_code_1 = input_int / 256
            int_code_2 = input_int % 256
            return chr(int_code_2) + chr(int_code_1)
        elif byte_index == 4:
            int_code_1 = input_int / 16777216
            int_code_2 = input_int % 16777216 / 65536
            int_code_3 = input_int % 16777216 % 65536 / 256
            int_code_4 = input_int % 16777216 % 65536 % 256
            return chr(int_code_4) + chr(int_code_3) + chr(int_code_2) + chr(int_code_1)


def convert_to_binary8(n):
    """
    Function to print binary number
    for the input decimal using recursion
    """
    data = bin(n)[2:]
    blank_digit = 8 - len(data)
    # fill in zero to maintain 8 bits
    data_8_bits = '0' * blank_digit + data
    return data_8_bits


# Dictionary Operation
def search_dict_keybyvalue(dictionary, search_value):
    # for name, age in list.items():  (for Python 3.x)
    for key, value in dictionary.iteritems():
        if value == search_value:
            # print key
            return key
    # raise LookupError


# List OPeration
def search_list_value(list, search_value):
    for x1, x2 in enumerate(list):
        if x2[0] == search_value:
            return x2[1]


# print banner and status
def print_status_bar(input_str1, input_str2):
    total_len = 40
    blank_len = total_len - len(input_str1) - len(input_str2)
    print input_str1.title() + ':' + '.' * blank_len,
    print ('\33[92m' + input_str2 + Fore.RESET)


