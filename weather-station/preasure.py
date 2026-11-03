from micropython import const
import time
import math

class Preasure:
    address = const(0x5d)
    def __init__(self, ssd, i2c):
        self.Preasure = 0
        self.ssd = ssd
        self.i2c = i2c      
        self.start_preasure()
        
    def start_preasure(self):
        msg = bytearray()
        msg.append(0x90)    
        self.i2c.writeto_mem(self.address, 0x20, msg)
        msg = bytearray()
        msg.append(0x01)    
        self.i2c.writeto_mem(self.address, 0x21, msg)
        self.start = time.ticks_ms()
        
    def draw(self, x, y, background, preasure_color):
        center_x = x + 32
        center_y = y - 38
        self.ssd.fill_rect(center_x - 16, center_y - 16, 33, 33, background)
        self.draw_hand(center_x, center_y, 16, self.Preasure, preasure_color)
        
    def draw_hand(self, center_x, center_y, arm, data, preasure_color):
        tick = int(((data - 970) / 60) * 30)
        angle = (math.pi / 30) * tick - math.pi
        cos = math.cos(angle)
        sin = math.sin(angle)
        cal_y = int(sin * arm + center_y)
        cal_x = int(cos * arm + center_x)
        self.ssd.line(center_x, center_y, cal_x, cal_y, preasure_color)
        self.ssd.line(center_x - 1, center_y, cal_x - 1, cal_y, preasure_color)
        self.ssd.line(center_x + 1, center_y, cal_x + 1, cal_y, preasure_color)
        
    def update(self, x, y, color, background, preasure_color):
        now = time.ticks_ms()
        if now - self.start > 3000:
            self.start = time.ticks_ms()
            #self.start_preasure()
            self.ssd.fill_rect(x, y - 5, 70, 25, background)
            Pressure_LSB = int.from_bytes(self.i2c.readfrom_mem(self.address, 0x29, 1), "big") 
            Pressure_MSB = int.from_bytes(self.i2c.readfrom_mem(self.address, 0x2A, 1), "big") 
            Pressure_XLB = int.from_bytes(self.i2c.readfrom_mem(self.address, 0x28, 1), "big") 
            count = (Pressure_MSB) << 16 | ( Pressure_LSB << 8 ) | Pressure_XLB
            self.Preasure = count/4096.0
            self.ssd.text(str(self.Preasure), x, y, color)
            self.draw(x, y, background, preasure_color)

            #Temp_LSB = int.from_bytes(self.i2c.readfrom_mem(self.address, 0x2B, 1), "big") 
            #Temp_MSB = int.from_bytes(self.i2c.readfrom_mem(self.address, 0x2C, 1), "big") 
            #count = (Temp_MSB << 8) | Temp_LSB
            #comp = count - (1 << 16)
            #Temp = 42.5 + (comp/480.0)
            #self.ssd.text(str(Temp), x, y + 10, color)
 
