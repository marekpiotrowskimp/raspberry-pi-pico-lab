from machine import I2C
import time

class Screen(object):
    LCD_CLEAR = 0x01
    LCD_CURSOR_MOVE = 0x14
    LCD_CURSOR_BLINKING = 0x0F
    LCD_CURSOR_OFF = 0x0C
    LCD_CURSOR_ON = 0x0E
    LCD_CURSOR_HOME = 0x02
    LCD_INIT_4BITS = 0x28
    LCD_ENTRY_MODE = 0x06
    LCD_CLEARDISPLAY = 0x01

    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address
        buf = bytearray([0x00])
        self.i2c.writeto(self.address, buf) 
        time.sleep_ms(50)

        self.lcd_write_raw(0x2, False, False, False)
        self.cmd(self.LCD_INIT_4BITS)
        self.cmd(self.LCD_INIT_4BITS)
        time.sleep_ms(10)
        self.cmd(self.LCD_CURSOR_BLINKING)
        time.sleep_ms(10)
        self.cmd(self.LCD_ENTRY_MODE)
        time.sleep_ms(10)
        self.cmd(self.LCD_CURSOR_HOME)
        time.sleep_ms(50)
        self.cmd(self.LCD_CURSOR_OFF)
        time.sleep_ms(50)
        self.cmd(self.LCD_CLEARDISPLAY)
        time.sleep_ms(50)
        
        
    def lcd_write_raw(self, data, rs, rw, light):
        data = (data << 4) & 0xF0
        if rw:
            data |= 0x02
        else:
            data &= 0xFC
            
        if light:
            data |= 0x08
        else:
            data &= 0xF7

        if rs: 
            data |= 0x01
        else:
            data &= 0xFE

        data1 = data & 0xFB
        data2 = data | 0x04
        data3 = data & 0xFB
        buf = bytearray([data1, data2, data3])
        self.i2c.writeto(self.address, buf) 


    def lcd_write(self, data, rs, rw, light):
        self.lcd_write_raw((data >> 4) & 0x0F, rs, rw, light)
        self.lcd_write_raw(data & 0x0F, rs, rw, light)
        
    def cmd(self, command):
        self.lcd_write(command, False, False, True)
        
    def write(self, char):
        self.lcd_write(char, True, False, True)
        
    def position(self, line, position):
        if line == 1:
                position += 0x40
        if line == 2:
                position += 0x14
        if line == 3:
                position += 0x54
        self.cmd(position)
        
    def write_line(self, text):
        for char in text:
            self.write(ord(char))
    
