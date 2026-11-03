from machine import Pin, SPI, I2C, UART
import gc

gc.enable()

from st7789_4b import *
SSD = ST7789

pdc = Pin(LCD_DC, Pin.OUT, value=0)  
pcs = Pin(LCD_CS, Pin.OUT, value=1)
prst = Pin(LCD_RST, Pin.OUT, value=1)
pbl = Pin(LCD_BL, Pin.OUT, value=1)

def getSPI(fast):
    if fast:
        return SPI(1, 62_500_000, sck=Pin(LCD_SCK), mosi=Pin(LCD_MOSI), miso=Pin(LCD_MISO))
    else:
        return SPI(1, 5_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))

gc.collect()
gc.threshold(gc.mem_free())
micropython.mem_info()
spi = getSPI(True)
irq = Pin(TP_IRQ, Pin.IN, Pin.PULL_UP)
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, tp_cs = Pin(TP_CS, Pin.OUT), irq = irq, height=240, width=320, disp_mode=6)
ssd.show()
gc.collect()
micropython.mem_info()

import time
from buzzer import Buzzer
from screens import ScreensRpi
import micropython
from preasure import Preasure
from clock import Clock
from pms7003 import Pms7003
from dht import DHT11
from effect import Effect
from images import ImagesTool
from wifi import WIFI
import json

i2c = machine.I2C(1, scl=machine.Pin(27), sda=machine.Pin(26))
devices = i2c.scan()
if devices:
    for device in devices:
        print(hex(device))

clock = Clock(ssd, i2c)
#clock.setup(00, 55, 16, 0, 20, 03, 22)

preasure = Preasure(ssd, i2c)

def back_action():
    time.sleep(0.1)
    screens.initial_screen(image_action, buzzer_action)

def image_action():
    gc.collect()
    screens.image_screen(back_action)
    
def buzzer_action():
    buz.toggle()
    time.sleep(0.1)

buz = Buzzer(125)

icons = ImagesTool(ssd)
screens = ScreensRpi(ssd, icons)
screens.booting_screen()
ssd.show()

sensor = 2
if sensor == 1:
    baudrate = 115200
else:
    baudrate = 57600

uart = UART(1, baudrate=baudrate, tx=Pin(4), rx=Pin(5), bits=8, parity=None, stop=1)
wifi = WIFI(uart, ssd, screens.TERMINAL, screens.BLACK)

#icons.transform_icon("clock.data","clock64.data", 64, 64, 4)
icons.load_icon("humidity64.data", 64, 64, 0x0F)
icons.load_icon("temperature64.data", 64, 64, 0x0F)
icons.load_icon("barometer64.data", 64, 64, 0x0F)
icons.load_icon("pollution64.data", 64, 64, 0x0F)
icons.load_icon("pressure64.data", 64, 64, 0x0F)
icons.load_icon("sun64.data", 64, 64, 0x0F)
icons.load_icon("clock64.data", 64, 64, 0x0F)

screens.initial_screen(image_action, buzzer_action)

pms = Pms7003(uart=0)

pin = Pin(2, Pin.OUT, Pin.PULL_UP)

sensor = DHT11(pin)
effect = Effect(ssd, 5, 125, 70, 80, screens.PIXELS, screens.ICON, screens.BLACK)

gc.collect()
micropython.mem_info()

def get_json():
    obj = {"date": clock.formatter_date(clock.date_time), "time": clock.formatter_time(clock.date_time), "preasure": preasure.Preasure, "humidity": sensor.humidity, "temperature": sensor.temperature, "pms": pms.pms_data}
    return json.dumps(obj)

timestamp = time.ticks_ms()
frame = 0
while True:
    screens.update(getSPI)
    preasure.update(240, 70, screens.TERMINAL, screens.BLACK, screens.ICON)
    clock.update(0, 70, screens.TERMINAL, screens.BLACK, screens.ICON, screens.HOUR, screens.MINUTS)
    sensor.update(ssd, 80, 70, screens.TERMINAL, screens.BLACK, screens.ICON)
    #buz.update()
    pms.update(ssd, 160, 120, screens.TERMINAL, screens.BLACK)
    if pms.pms_data != None:
        effect.update(pms.pms_data['PM10_0'])
    ssd.show()
    wifi.receive(get_json())
    frame += 1
    if time.ticks_ms() - timestamp > 1000:
        timestamp = time.ticks_ms()
        ssd.fill_rect(270, 230 - 5, 70, 20, screens.BLACK)
        ssd.text(str(frame) + ' FPS', 270, 230, screens.TERMINAL)
        frame = 0
        gc.collect()
    
    
    




