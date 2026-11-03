from machine import I2C
import i2c_lcd_screen

class Display(object):
    screen = None

    def __init__(self, i2c, lcd_addr=0x27, rgb_addr=0x62):
        self.i2c = i2c
        self.screen = i2c_lcd_screen.Screen(i2c, lcd_addr)

    def write(self, text):
        self.screen.write(text)

    def cursor(self, state):
        self.screen.cursor(state)

    def blink(self, state):
        self.screen.blink(state)

    def autoscroll(self, state):
        self.screen.autoscroll(state)

    def display(self, state):
        self.screen.display(state)

    def clear(self):
        self.screen.clear()

    def home(self):
        self.screen.home()

    def move(self, col, row):
        self.screen.setCursor(col, row)
