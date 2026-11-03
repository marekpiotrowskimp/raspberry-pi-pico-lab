import array
import micropython
import utime
from machine import Pin
from micropython import const
import time

MAX_UNCHANGED = const(100)
MIN_INTERVAL_US = const(2_000_000)
HIGH_LEVEL = const(50)
EXPECTED_PULSES = const(84)

class DHT11:
    _temperature: float
    _humidity: float
    timestamp = 0
    def __init__(self, pin):
        self._pin = pin
        self._last_measure = utime.ticks_us()
        self._temperature = -1
        self._humidity = -1

    def measure(self):
        current_ticks = utime.ticks_us()
        if current_ticks - self._last_measure < MIN_INTERVAL_US:
            return

        self._send_init_signal()
        pulses = self._capture_pulses()
        if pulses == None:
            return
        buffer = self._convert_pulses_to_buffer(pulses)
        if not self._verify_checksum(buffer):
            return

        self._humidity = buffer[0] + buffer[1] / 10
        self._temperature = buffer[2] + buffer[3] / 10
        self._last_measure = utime.ticks_us()

    @property
    def humidity(self):
        self.measure()
        return self._humidity

    @property
    def temperature(self):
        self.measure()
        return self._temperature

    def _send_init_signal(self):
        self._pin.init(Pin.OUT, Pin.PULL_DOWN)
        self._pin.value(1)
        utime.sleep_ms(50)
        self._pin.value(0)
        utime.sleep_ms(18)

    @micropython.native
    def _capture_pulses(self):
        pin = self._pin
        pin.init(Pin.IN, Pin.PULL_UP)

        val = 1
        idx = 0
        transitions = bytearray(EXPECTED_PULSES)
        unchanged = 0
        timestamp = utime.ticks_us()

        while unchanged < MAX_UNCHANGED:
            if val != pin.value():
                if idx >= EXPECTED_PULSES:
                    return None
                now = utime.ticks_us()
                transitions[idx] = now - timestamp
                timestamp = now
                idx += 1

                val = 1 - val
                unchanged = 0
            else:
                unchanged += 1
        pin.init(Pin.OUT, Pin.PULL_DOWN)
        if idx != EXPECTED_PULSES:
            return None
        return transitions[4:]

    def _convert_pulses_to_buffer(self, pulses):
        """Convert a list of 80 pulses into a 5 byte buffer
        The resulting 5 bytes in the buffer will be:
            0: Integral relative humidity data
            1: Decimal relative humidity data
            2: Integral temperature data
            3: Decimal temperature data
            4: Checksum
        """
        # Convert the pulses to 40 bits
        binary = 0
        for idx in range(0, len(pulses), 2):
            binary = binary << 1 | int(pulses[idx] > HIGH_LEVEL)

        # Split into 5 bytes
        buffer = array.array("B")
        for shift in range(4, -1, -1):
            buffer.append(binary >> shift * 8 & 0xFF)
        return buffer

    def _verify_checksum(self, buffer):
        # Calculate checksum
        checksum = 0
        for buf in buffer[0:4]:
            checksum += buf
        if checksum & 0xFF != buffer[4]:
            return False
        return True
    
    def draw(self, ssd, x, y, background, temperature_color):
        center_x = x + 32 + 92
        center_y = y - 38
        ssd.fill_rect(center_x - 16, center_y - 23, 8, 36, background)
        temp_div = 36 - int(((self.temperature + 10) / 50) * 36) # -10 : 40
        if temp_div > 36:
            temp_div = 36
        if temp_div < 0:
            temp_div = 0
        ssd.fill_rect(center_x - 14, center_y - 23 + temp_div, 4, 36 - temp_div, temperature_color)
    
    def update(self, ssd, x, y, color, background, temperature_color):
        if time.ticks_ms() - self.timestamp > 5000:
            self.timestamp = time.ticks_ms()
            humidity = self.humidity
            temperature = self.temperature
            ssd.fill_rect(x, y - 5, 150, 35, background)
            ssd.text(str(temperature) + "C", x + 92, y, color)
            ssd.text(str(int(humidity)) + "%", x + 31, y, color)
            self.draw(ssd, x, y, background, temperature_color)

