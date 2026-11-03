from micropython import const
import time
import math

class Clock:
    address = const(0x68)
    second = const(0x00)
    minutes = const(0x01)
    hours = const(0x02)
    day_of_week = const(0x03)
    day = const(0x04)
    month = const(0x05)
    year = const(0x06)
    control = const(0x07)
    date_time = bytearray(7)
    time_format = '{}:{}.{}'
    date_format = '{}/{}/{}'
    timestamp = 0
    
    def __init__(self, ssd, i2c):
        self.ssd = ssd
        self.i2c = i2c
    
    def write(self, data, registry):
        msg = bytearray()
        msg.append(data)
        print(hex(data), hex(registry))
        self.i2c.writeto_mem(self.address, registry, msg)
        
    def prepare_data(self, data, hours24 = False, ch_bit = False):
        data10 = int(data / 10)
        data = data - data10 * 10
        data_byte = data10 << 4 | data
        if hours24:
            data_byte = data_byte & 0xBF
        if ch_bit:
            data_byte = data_byte | 0x80
        return data_byte
    
    def bcd_to_int(self, data):
        data10 = data >> 4 & 0x0F
        data = data & 0x0F
        return data10 * 10 + data
    
    def control(self, is_run):
        if is_run:
            data = 0x00
        else:
            data = 0x80
        self.write(data, self.second)
    
    def setup(self, second_c, minutes_c, hours_c, day_of_week_c, day_c, month_c, year_c):
        self.control(False)
        self.write(self.prepare_data(year_c), self.year)
        self.write(self.prepare_data(month_c), self.month)
        self.write(self.prepare_data(day_c), self.day)
        self.write(self.prepare_data(day_of_week_c), self.day_of_week)
        self.write(self.prepare_data(hours_c, True), self.hours)
        self.write(self.prepare_data(minutes_c), self.minutes)
        self.write(self.prepare_data(second_c), self.second)
    
    def read(self):
        self.date_time = self.i2c.readfrom_mem(self.address, 0x00, 7)
        
    def str2digits(self, data):
        str_data = str(self.bcd_to_int(data))
        if len(str_data) == 1:
            return '0' + str_data
        return str_data
        
    def formatter_time(self, date_time):
        return self.time_format.format(self.str2digits(date_time[2]), self.str2digits(date_time[1]), self.str2digits(date_time[0]))
    
    def formatter_date(self, date_time):
        return self.date_format.format(self.str2digits(date_time[4]), self.str2digits(date_time[5]), self.str2digits(date_time[6]))
    
    def clock_tick(self, x, y, background, clock_color, hour_color, minuts_color):
        center_x = x + 32
        center_y = y - 38
        self.ssd.fill_rect(center_x - 16, center_y - 16, 33, 33, background)
        self.draw_hand(center_x, center_y, 15, self.date_time[0], clock_color)
        self.draw_hand(center_x, center_y, 13, self.date_time[1], minuts_color)
        self.draw_hand(center_x, center_y, 10, self.date_time[2], hour_color, self.date_time[1])
        
    def draw_hand(self, center_x, center_y, arm, data, clock_color, div=-1):
        tick = self.bcd_to_int(data)
        if div >= 0:
            tick = tick * 5 + self.bcd_to_int(div) / 24
        angle = (math.pi / 30) * tick - math.pi / 2
        cal_x = int(math.cos(angle) * arm + center_x)
        cal_y = int(math.sin(angle) * arm + center_y)
        self.ssd.line(center_x, center_y, cal_x, cal_y, clock_color)
        self.ssd.line(center_x - 1, center_y, cal_x - 1, cal_y, clock_color)
        
    def update(self,  x, y, color, background, clock_color, hour_color, minuts_color):
        if time.ticks_ms() - self.timestamp > 250:
            self.timestamp = time.ticks_ms()
            self.read()
            self.ssd.fill_rect(x, y - 5, 70, 25, background)
            self.ssd.text(self.formatter_date(self.date_time), x, y, color)
            self.ssd.text(str(self.formatter_time(self.date_time)), x, y + 10, color)
            self.clock_tick(x, y, background, clock_color, hour_color, minuts_color)
            
            
