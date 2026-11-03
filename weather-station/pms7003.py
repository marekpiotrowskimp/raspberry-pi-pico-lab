import machine
import struct
import time
from micropython import const


class UartError(Exception):
    pass


class Pms7003:

    START_BYTE_1 = const(0x42)
    START_BYTE_2 = const(0x4d)

    PMS_FRAME_LENGTH = const(0)
    PMS_PM1_0 = const(1)
    PMS_PM2_5 = const(2)
    PMS_PM10_0 = const(3)
    PMS_PM1_0_ATM = const(4)
    PMS_PM2_5_ATM = const(5)
    PMS_PM10_0_ATM = const(6)
    PMS_PCNT_0_3 = const(7)
    PMS_PCNT_0_5 = const(8)
    PMS_PCNT_1_0 = const(9)
    PMS_PCNT_2_5 = const(10)
    PMS_PCNT_5_0 = const(11)
    PMS_PCNT_10_0 = const(12)
    PMS_VERSION = const(13)
    PMS_ERROR = const(14)
    PMS_CHECKSUM = const(15)
    
    timestamp = 0

    def __init__(self, uart):
        self.pms_data = None
        self.uart = machine.UART(uart, baudrate=9600, bits=8, parity=None, stop=1)

    def __repr__(self):
        return "Pms7003({})".format(self.uart)

    @staticmethod
    def _assert_byte(byte, expected):
        if byte is None or len(byte) < 1 or ord(byte) != expected:
            return False
        return True

    @staticmethod
    def _format_bytearray(buffer):
        return "".join("0x{:02x} ".format(i) for i in buffer)

    def _send_cmd(self, request, response):

        nr_of_written_bytes = self.uart.write(request)

        if nr_of_written_bytes != len(request):
            raise UartError('Failed to write to UART')

        if response:
            time.sleep(2)
            buffer = self.uart.read(len(response))

            if buffer != response:
                raise UartError(
                    'Wrong UART response, expecting: {}, getting: {}'.format(
                        Pms7003._format_bytearray(response), Pms7003._format_bytearray(buffer)
                    )
                )

    def read(self):
        first_byte = self.uart.read(1)
        if not self._assert_byte(first_byte, Pms7003.START_BYTE_1):
            return None

        second_byte = self.uart.read(1)
        if not self._assert_byte(second_byte, Pms7003.START_BYTE_2):
            return None

        # we are reading 30 bytes left
        read_bytes = self.uart.read(30)
        if read_bytes == None or len(read_bytes) < 30:
            return None

        data = struct.unpack('!HHHHHHHHHHHHHBBH', read_bytes)

        checksum = Pms7003.START_BYTE_1 + Pms7003.START_BYTE_2
        checksum += sum(read_bytes[:28])

        if checksum != data[Pms7003.PMS_CHECKSUM]:
            return None

        return {
            'FRAME_LENGTH': data[Pms7003.PMS_FRAME_LENGTH],
            'PM1_0': data[Pms7003.PMS_PM1_0],
            'PM2_5': data[Pms7003.PMS_PM2_5],
            'PM10_0': data[Pms7003.PMS_PM10_0],
            'PM1_0_ATM': data[Pms7003.PMS_PM1_0_ATM],
            'PM2_5_ATM': data[Pms7003.PMS_PM2_5_ATM],
            'PM10_0_ATM': data[Pms7003.PMS_PM10_0_ATM],
            'PCNT_0_3': data[Pms7003.PMS_PCNT_0_3],
            'PCNT_0_5': data[Pms7003.PMS_PCNT_0_5],
            'PCNT_1_0': data[Pms7003.PMS_PCNT_1_0],
            'PCNT_2_5': data[Pms7003.PMS_PCNT_2_5],
            'PCNT_5_0': data[Pms7003.PMS_PCNT_5_0],
            'PCNT_10_0': data[Pms7003.PMS_PCNT_10_0],
            'VERSION': data[Pms7003.PMS_VERSION],
            'ERROR': data[Pms7003.PMS_ERROR],
            'CHECKSUM': data[Pms7003.PMS_CHECKSUM],
        }

    def update(self, ssd, x, y, color, background):
        if time.ticks_ms() - self.timestamp > 250:
            self.timestamp = time.ticks_ms()
            data = self.read()
            if data != None:
                self.pms_data = data
                ssd.fill_rect(x, y - 5, 160, 95, background)
                ssd.text("PM1_0  " + str(data['PM1_0']), x, y, color)
                ssd.text("PM2_5  " + str(data['PM2_5']), x, y + 10, color)
                ssd.text("PM10_0 " + str(data['PM10_0']), x, y + 20, color)
                ssd.text("PCNT_0_3  " + str(data['PCNT_0_3']), x, y + 30, color)
                ssd.text("PCNT_0_5  " + str(data['PCNT_0_5']), x, y + 40, color)
                ssd.text("PCNT_1_0  " + str(data['PCNT_1_0']), x, y + 50, color)
                ssd.text("PCNT_2_5  " + str(data['PCNT_2_5']), x, y + 60, color)
                ssd.text("PCNT_5_0  " + str(data['PCNT_5_0']), x, y + 70, color)
                ssd.text("PCNT_10_0 " + str(data['PCNT_10_0']), x, y + 80, color)
            
            
