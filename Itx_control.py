import time
import minimalmodbus
import serial
from General_config import *
from PyCRC.CRC16 import *

# Minial Modbus Setting
minimalmodbus.BAUDRATE = 9600
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1
minimalmodbus.TIMEOUT = 1

# LTX_Password
Itx_config_password = 100
Itx_calibration_password = 101

# CRC check method
def crc_check(string=''):
    result = CRC16(modbus_flag=True).calculate(string)
    code = chr(result % 256) + chr(result / 256)
    return code


# Scaling Function
def parameter_scaling_up(mode, input_value):
    if mode == '5A':
        return input_value * 10000
    elif mode == '12kOhm':
        return input_value * 1000000
    elif mode == '1VAC':
        return input_value * 1000000
    else:
        return input_value * 1000


def parameter_scaling_down(mode, input_value):
    if mode == '5A':
        return input_value / 10000.0
    elif mode == '12kOhm':
        return input_value / 1000000.0
    elif mode == '1VAC':
        return input_value / 1000000.0
    else:
        return input_value / 1000.0


class ItxDriver:
    def __init__(self):
        self.itx = minimalmodbus.Instrument('com29', 1, mode='rtu')  # port name, slave address (in decimal)
        self.engineering_units = {'A': '\x00\x41', 'DegC': '\xA7\x43', 'DegF': '\xA7\x46', 'Kohm': '\x00\x3f',
                                  'mA': 'mA', 'mV': 'mV', '%': '\x00' + "%", 'V': '\x00' + 'V', 'ohm': '\x00\x3f'}
        self.sinc_filter = {'Fast settling': 0, 'Sinc2': 1, 'Sinc3': 2, 'Auto': 3}
        self.calibration_usage = {'Factory': 1, 'User defined': 0}
        self.cjc_unit = {'f': 1, 'c': 0}
        self.transfer_function = {'user': 0, 'sqrt': 5, 'linear': 10, 'square': 20}
        self.alarm_type = {'low': 4, 'window': 2, 'high': 8}
        self.alarm_energisation = {'Normal Energised': 1, 'Normal deEnergised': 0}
        self.ip_buffer = {'on (default)': 1, 'off': 0}
        self.output_action = {'Direct (default)': 0, 'Reverse': 1}
        self.config_info = []

        self.calibration_data_list = (('Output mA', '\x01'), ('Input mV', '\x11'), ('Input V', '\x12'),
                                      ('Input mA', '\x13'), ('Input RES', '\x14'), ('Input Vac', '\x17'))

    def close(self):
        if self.itx.serial.isOpen():
            self.itx.serial.close()
            print ("Port Closed")

    def read_holding_registers(self, address, length):
        if type(address) != int or type(length) != int:
            print 'Please input correct argument type (int)'
        else:
            return self.itx.read_string(address - 1, length, 3)

    def read_input_register(self, address, length):
        if type(address) != int or type(length) != int:
            print 'Please input correct argument type (int)'
        else:
            return self.itx.read_string(address - 1, length, 4)

    def write_holding_register(self, address=1, value='\x11\x40'):
        if len(value) == 2:
            int_value = str_to_int(value, byte_index=2, endian='big')
            self.itx.write_register(address - 1, int_value, functioncode=6)
        else:
            no_regs = len(value) / 2
            self.itx.write_string(address - 1, value, no_regs)

            # print 'Write ', value.encode('hex'),
            # print ' into Register {0}'.format(address + 40000)

    def start_config_mode(self, password):
        if type(password) == str:
            pass
        else:
            password = str(password)
        request_payload = '\x01\x46\x06\x01\x04\x06\x07\xE2' + '\x20' * 2 * 16 + '\x20' * 2 * 4 + password + '\x20' * 5
        request = request_payload + crc_check(request_payload)

        self.itx.serial.write(request)
        time.sleep(0.2)
        response = self.itx.serial.read(7)
        if response == '\x01\x46\x06\x01\x05\x2d\x1a':
            pass
            # print 'ITX device configuration mode starts!'
        else:
            print 'ITX device configuration mode start Failed!'
            print response.encode('hex')

    def end_config_mode(self, password):
        if type(password) == str:
            pass
        else:
            password = str(password)
        request_payload = '\x01\x46\x06\x00\x04\x06\x07\xE2' + '\x20' * 2 * 16 + '\x20' * 2 * 4 + password + '\x20' * 5
        request = request_payload + crc_check(request_payload)

        self.itx.serial.write(request)
        time.sleep(0.2)
        response = self.itx.serial.read(7)
        if response == '\x01\x46\x06\x00\x05\x2c\x8a':
            pass
            # print 'ITX device configuration mode ends!'
        else:
            print 'ITX device configuration mode ends Failed'
            print response.encode('hex')

    '''
    Setting Section
    
    
    '''

    def set_sensor_selection(self, sensor='K', wire_option='3wire', burnout='downscale', alarm_burnout='alarm frozen'):
        register_address = 1
        # Input selection check
        if sensor not in sensor_list.keys():
            print 'Please enter valid sensor selection: ', sensor_list.keys()
        elif wire_option not in wire_option_list.keys():
            print 'Please enter valid wire selection: ', wire_option_list.keys()
        elif burnout not in analog_burnout_list.keys() and alarm_burnout not in alarm_burnout_list.keys():
            print 'Please enter valid burn selection: '
        else:
            # Request value Generation
            # alarm_burnout_bit = burnout_bit = wire_bit = '00'
            high_byte_raw = alarm_burnout_list[alarm_burnout] + analog_burnout_list[burnout] + \
                            wire_option_list[wire_option]
            high_byte = chr(int(high_byte_raw, 2))
            low_byte = sensor_list[sensor]

            self.start_config_mode(Itx_password)
            self.write_holding_register(register_address, high_byte + low_byte)

            print 'Input configuration done'

    def set_engineering_unit(self, unit_value='DegC'):
        register_address = 2
        if unit_value not in self.engineering_units.keys():
            print 'Please enter valid engineering unit selection: ', self.engineering_units.keys()
        else:
            self.write_holding_register(register_address, self.engineering_units[unit_value])
            print 'Input engineering unit has been set to: ', unit_value

    def set_input_low(self, value=0):
        register_address = 3
        if type(value) == int:
            self.write_holding_register(register_address, int_to_str(value, byte_index=4))
            print 'Input low has been set to: ', value
        else:
            print 'Please enter argument in integer format'

    def set_input_high(self, value=0):
        register_address = 5
        if type(value) == int:
            self.write_holding_register(register_address, int_to_str(value, byte_index=4))
            print 'Input high has been set to: ', value
        else:
            print 'Please enter argument in integer format'

    def set_sinc_filter_adc(self, value=0):
        register_address = 7
        if type(value) == int and search_dict_keybyvalue(self.sinc_filter, value):
            self.write_holding_register(register_address, int_to_str(value))
            print 'Sinc filter ADC has been set to ', search_dict_keybyvalue(self.sinc_filter, value)
        else:
            print 'Please enter argument in integer format (0, 1, 2,3)'

    def set_decimation_adc(self, value=660):
        register_address = 8
        if type(value) == int and 2000 >= value >= 100:
            self.write_holding_register(register_address, int_to_str(value))
            print 'ADC Decimation adc has been set to: ', value
        else:
            print 'Please enter argument in integer format (100-2000)'

    def set_ip_buffer_adc(self, value=0):
        register_address = 9
        if value in [0, 1]:
            self.write_holding_register(register_address, int_to_str(value))
            print 'ADC IP buffer has been set to: ', value, ' (1: on, 0: off)'
        else:
            print 'Please enter argument in integer format (0, 1)'

    def set_damping_factor(self, value=1):
        register_address = 10
        if type(value) == int and 100 >= value >= 1:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Damping factor has been set to: ', value
        else:
            print 'Please enter argument in integer format (1-100)'

    def set_output_low(self, value=4000):
        register_address = 11
        if type(value) == int and 20000 >= value >= 3500:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Output low has been set to: ', value / 1000
        else:
            print 'Please enter argument in integer format (3500-20000)'

    def set_output_high(self, value=20000):
        register_address = 12
        if type(value) == int and 20000 >= value >= 4000:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Output high has been set to: ', value / 1000
        else:
            print 'Please enter argument in integer format (4000-20000)'

    def set_output_action(self, value=0):
        register_address = 13
        if value in [0, 1]:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Output action has been set to: ', value, ' (1: reverse, 0: direct)'
        else:
            print 'Please enter argument in integer format (0, 1)'

    def set_calibration_usage(self, input_cal='Factory', output_cal='Factory'):
        register_address = 14
        if input_cal in self.calibration_usage.keys() and output_cal in self.calibration_usage.keys():
            value = self.calibration_usage[input_cal] + self.calibration_usage[output_cal] * 2
            self.write_holding_register(register_address, int_to_str(value))
            print 'Input Calibration Usage has been set to: ', input_cal
            print 'Output Calibration Usage has been set to: ', output_cal
        else:
            print 'Please enter argument in integer format (Factory , User Defined)'

    def set_cjc_unit(self, value='c'):
        register_address = 15
        if value in self.cjc_unit.keys():
            self.write_holding_register(register_address, int_to_str(self.cjc_unit[value]))
            print 'CJC temperature unit has been set to: ', value
        else:
            print 'Please enter argument in correct format (c or f)'

    def set_output_low_clamp(self, value=3500):
        register_address = 16
        if type(value) == int and 20000 >= value >= 3500:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Output Low Clamp has been set to: ', value / 1000
        else:
            print 'Please enter argument in integer format (3500-20000)'

    def set_output_high_clamp(self, value=23000):
        register_address = 17
        if type(value) == int and 23000 >= value >= 4000:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Output high clamp has been set to: ', value / 1000
        else:
            print 'Please enter argument in integer format (4000-23000)'

    def set_transfer_function(self, value):
        register_address = 18
        tf_type = search_dict_keybyvalue(self.transfer_function, value)
        if tf_type:
            self.write_holding_register(register_address, int_to_str(value))
            print 'Transfer Function has been set to: ', tf_type
        else:
            print 'Please enter argument in correct format ', self.transfer_function.iterkeys()

    def set_alarm_trip_regs(self, value):
        register_address = 19
        if type(value) == int:
            self.write_holding_register(register_address, int_to_str(value, byte_index=4))
            print 'Alarm Trip Registers has been set to: ', value
        else:
            print 'Please enter argument in integer format'

    def set_alarm_db_regs(self, value):
        register_address = 21
        if type(value) == int:
            self.write_holding_register(register_address, int_to_str(value, byte_index=4))
            print 'Alarm DB Registers has been set to: ', value
        else:
            print 'Please enter argument in integer format'

    def set_alarm_window_regs(self, value):
        register_address = 23
        if type(value) == int:
            self.write_holding_register(register_address, int_to_str(value, byte_index=4))
            print 'Alarm Windows Registers has been set to: ', value
        else:
            print 'Please enter argument in integer format'

    def set_alarm_action(self, alarm_type='low', energised='e', level_1=20000, db=500, level_2=10000):
        register_address = 25
        if alarm_type in self.alarm_type.keys():
            if energised == 'e':
                value = self.alarm_type[alarm_type] + 1
            else:
                value = self.alarm_type[alarm_type]
            self.write_holding_register(register_address, int_to_str(value))
            print 'Alarm has been set to: {0} type, normally {1}'.format(alarm_type, energised)
        else:
            print 'Please enter argument in correect for Alarm type and energised'

        if alarm_type == 'window':
            self.set_alarm_trip_regs((level_1 + level_2) / 2)
            self.set_alarm_window_regs((level_1 - level_2) / 2)
            self.set_alarm_db_regs(db)
        elif alarm_type == 'low' or alarm_type == 'high':
            self.set_alarm_trip_regs(level_1)
            self.set_alarm_db_regs(db)

    # Reading Section
    def get_input_config(self):
        register_address = 1
        register_length = 10
        response = self.read_holding_registers(register_address, register_length)

        sensor_setting = convert_to_binary8(ord(response[0]))
        wire_option = search_dict_keybyvalue(wire_option_list, sensor_setting[4:])
        analog_burnout = search_dict_keybyvalue(analog_burnout_list, sensor_setting[2:4])
        alarm_burnout = search_dict_keybyvalue(alarm_burnout_list, sensor_setting[:2])
        sensor_type = search_dict_keybyvalue(sensor_list, response[1])
        engineering_unit = response[2:4]
        input_low_raw = str_to_int(strin=response[4:8], byte_index=4, endian='big')
        input_low = parameter_scaling_down(sensor_type, input_low_raw)
        input_high_raw = str_to_int(strin=response[8:12], byte_index=4, endian='big')
        input_high = parameter_scaling_down(sensor_type, input_high_raw)

        sinc_filter_adc_value = str_to_int(response[12:14], byte_index=2, endian='big')
        sinc_filter_adc = search_dict_keybyvalue(self.sinc_filter, sinc_filter_adc_value)
        decimation_adc = str_to_int(response[14:16], byte_index=2, endian='big')
        ip_buffer_adc = str_to_int(response[16:18], byte_index=2, endian='big')
        damping_factor = str_to_int(response[18:20], byte_index=2, endian='big')

        self.config_info.append(('Input Sensor Type', sensor_type))
        self.config_info.append(('Input Eng Unit', engineering_unit))
        self.config_info.append(('Input Wire Option', wire_option))
        self.config_info.append(('Input Analog Burnout', analog_burnout))
        self.config_info.append(('Input Alarm Burnout', alarm_burnout))
        self.config_info.append(('Input Input Low limit', str(input_low)))
        self.config_info.append(('Input Input High Limit', str(input_high)))
        self.config_info.append(('Input Sinc Filter', sinc_filter_adc))
        self.config_info.append(('Input Decimaiton ADC', str(decimation_adc)))
        self.config_info.append(('Input IP Buffer ADC', search_dict_keybyvalue(self.ip_buffer, ip_buffer_adc)))
        self.config_info.append(('Input Damping ADC', str(damping_factor)))

    def get_analog_output_config(self):
        register_address1 = 11
        register_length1 = 3
        response1 = self.read_holding_registers(register_address1, register_length1)

        register_address2 = 16
        register_length2 = 2
        response2 = self.read_holding_registers(register_address2, register_length2)

        output_low = round(str_to_int(response1[0:2], byte_index=2, endian='big') / 1000.0, 2)
        output_high = round(str_to_int(response1[2:4], byte_index=2, endian='big') / 1000.0, 2)
        output_action = str_to_int(response1[4:6], byte_index=2, endian='big')

        output_clamp_low = round(str_to_int(response2[0:2], byte_index=2, endian='big') / 1000.0, 2)
        output_clamp_high = round(str_to_int(response2[2:4], byte_index=2, endian='big') / 1000.0, 2)

        self.config_info.append(('Output Low Limit', str(output_low)))
        self.config_info.append(('Output High Limit', str(output_high)))
        self.config_info.append(('Output Action', search_dict_keybyvalue(self.output_action, output_action)))
        self.config_info.append(('Output Low Clamp', str(output_clamp_low)))
        self.config_info.append(('Output High Clamp', str(output_clamp_high)))

    def get_calibration_config(self):
        register_address = 14
        register_length = 1
        response = self.read_holding_registers(register_address, register_length)

        calibration = convert_to_binary8(ord(response[1]))
        input_calibration = search_dict_keybyvalue(self.calibration_usage, int(calibration[-2]))
        output_calibration = search_dict_keybyvalue(self.calibration_usage, int(calibration[-1]))

        self.config_info.append(('Input Calibration', input_calibration))
        self.config_info.append(('Output Calibration', output_calibration))

    def get_cjc_unit(self):
        register_address = 15
        register_length = 1
        response = self.read_holding_registers(register_address, register_length)

        cjc_unit = search_dict_keybyvalue(self.cjc_unit, ord(response[1]))
        self.config_info.append(('Input CJC Unit', cjc_unit))

    def get_tranfer_function(self):
        register_address = 18
        register_length = 1
        response = self.read_holding_registers(register_address, register_length)

        transfer_funciton = str_to_int(response, byte_index=2, endian='big')

        self.config_info.append(('Transfer Function', search_dict_keybyvalue(self.transfer_function,
                                                                             transfer_funciton)))

    def get_alarm_config(self):
        register_address = 19
        register_length = 8
        response = self.read_holding_registers(register_address, register_length)

        sensor_type = search_list_value(itx.config_info, 'Input Sensor Type')

        alarm_trip_raw = str_to_int(strin=response[:4], byte_index=4, endian='big')
        alarm_db_raw = str_to_int(strin=response[4:8], byte_index=4, endian='big')
        alarm_window_raw = str_to_int(strin=response[8:12], byte_index=4, endian='big')
        alarm_trip = parameter_scaling_down(sensor_type, alarm_trip_raw)
        alarm_db = parameter_scaling_down(sensor_type, alarm_db_raw)
        alarm_window = parameter_scaling_down(sensor_type, alarm_window_raw)
        alarm_action = ord(response[13])
        alarm_energization = search_dict_keybyvalue(self.alarm_energisation, alarm_action % 2)
        alarm_type = search_dict_keybyvalue(self.alarm_type, alarm_action-alarm_action%2)
        alarm_trip_delay = ord(response[14])
        alarm_reset_delay = ord(response[15])

        self.config_info.append(('Alarm Type', alarm_type))
        self.config_info.append(('Alarm Energization', alarm_energization))
        self.config_info.append(('Alarm Trip Delay', str(alarm_trip_delay)))
        self.config_info.append(('Alarm Reset Delay', str(alarm_reset_delay)))
        if alarm_type == 'window':
            level1 = (alarm_trip + alarm_window) / 2
            level2 = (alarm_trip - alarm_window) / 2
            self.config_info.append(('Alarm Trip Level 1', str(level1)))
            self.config_info.append(('Alarm Trip Level 2', str(level2)))
        else:
            self.config_info.append(('Alarm Trip Level', str(alarm_trip)))
            self.config_info.append(('Alarm db', str(alarm_db)))

    def read_config(self):
        self.config_info = []
        self.get_input_config()
        self.get_cjc_unit()
        self.get_analog_output_config()
        self.get_calibration_config()
        self.get_tranfer_function()
        self.get_alarm_config()

        print '*' * 45
        for _, info in enumerate(self.config_info):
            print_status_bar(info[0], info[1])
        print '*' * 45

    '''
    Calibration Area
    
    
    '''
    def read_user_calibration_data(self):
        for calibration_data in self.calibration_data_list:
            request_payload = '\x01\x46\x01' + calibration_data[1]
            request = request_payload + crc_check(request_payload)
            # print request.encode('hex')
            self.itx.serial.write(request)
            time.sleep(0.2)

            response_length = self.itx.serial.inWaiting()
            # print response_length
            response = self.itx.serial.read(response_length)
            if response[:3] == '\x01\x46\x01':
                print calibration_data[0], response[:-2].encode('hex')

    def enable_user_calibration(self, password = Itx_calibration_password):
        if type(password) == str:
            pass
        else:
            password = str(password)
        request_payload = '\x01\x46\x00\x04\x06\x07\xE2' + '\x20' * 2 * 4 + password + '\x20' * 5
        request = request_payload + crc_check(request_payload)

        # print request.encode('hex')
        self.itx.serial.write(request)
        time.sleep(0.2)
        response = self.itx.serial.read(7)
        if response == '\x01\x46\x00\x05' + crc_check('\x01\x46\x00\x05'):
            print_status_bar('ITX device Encable User calibration mode', 'Done')
            pass
            # print 'ITX device configuration mode starts!'
        else:
            print_status_bar('ITX device Encable User calibration mode', 'Fail')
            print response.encode('hex')

    def calibrate_input(self, calibrate_cmd=Calibration_input_list[0]):

        request_payload = '\x01\x46\x03' + calibrate_cmd[1]
        request = request_payload + crc_check(request_payload)

        # print request.encode('hex')
        self.itx.serial.write(request)
        time.sleep(0.2)
        response = self.itx.serial.read(7)
        if response == request_payload + '\x05' + crc_check(request_payload + '\x05'):
            print_status_bar('Set Calibration mode' + calibrate_cmd[0], 'Done')
            pass
            # print 'ITX device configuration mode starts!'
        else:
            print_status_bar('Set Calibration mode' + calibrate_cmd[0], 'Fail')
            print response.encode('hex')

if __name__ == '__main__':
    itx = ItxDriver()
    '''
    itx.set_sensor_selection(sensor='L', burnout='downscale')
    print itx.read_holding_registers(1, 1).encode('hex')
    itx.set_sensor_selection(sensor='25mA', burnout='upscale')
    print itx.read_holding_registers(1, 1).encode('hex')
    itx.set_cjc_unit() 

    itx.set_sensor_selection(sensor='K', wire_option='2wire', burnout='upscale', alarm_burnout='alarm tripped')
    itx.set_input_low(value=500)
    itx.set_input_high(value=1000)
    itx.set_output_high_clamp(value=23000)
    itx.set_output_low_clamp(value=3500)
    itx.set_decimation_adc(value=660)
    itx.set_ip_buffer_adc(1)
    itx.set_damping_factor(2)
    itx.set_alarm_action(alarm_type='high')
    itx.set_calibration_usage()
    '''
    itx.enable_user_calibration()
    # itx.read_config()

    itx.close()
