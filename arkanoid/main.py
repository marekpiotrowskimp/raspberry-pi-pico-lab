from machine import Pin, SPI, I2C, UART
import gc
from st7789 import *

def getSPI(fast):
    if fast:
        return SPI(1, 62_500_000, sck=Pin(LCD_SCK), mosi=Pin(LCD_MOSI), miso=Pin(LCD_MISO))
    else:
        return SPI(1, 5_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))

gc.enable()
SSD = ST7789

pdc = Pin(LCD_DC, Pin.OUT, value=0)  
pcs = Pin(LCD_CS, Pin.OUT, value=1)
prst = Pin(LCD_RST, Pin.OUT, value=1)
pbl = Pin(LCD_BL, Pin.OUT, value=1)
gc.collect()
gc.threshold(gc.mem_free())
micropython.mem_info()
spi = getSPI(True)
irq = Pin(TP_IRQ, Pin.IN, Pin.PULL_UP)
ssd = SSD(spi, dc=pdc, cs=pcs, rst=prst, tp_cs = Pin(TP_CS, Pin.OUT), irq = irq, height=240, width=320, disp_mode=6)
gc.collect()

from images import ImagesTool
from consts import *
ssd.fill_rect(0, 0, 320, 240, Consts.background)
ssd.show()
image = ImagesTool(ssd)
#image.transform('arkanoid.data', 'arkanoid.rgb565', 4)
image.draw_data_fast('arkanoid.rgb565')
time.sleep_ms(4500)
del image

import time
import micropython
from buzzer import *
from ball import *
from player import *
from bricks import *

ssd.fill_rect(0, 0, 320, 240, Consts.background)
ssd.show()

timestamp = time.ticks_ms()
frame = 0
last_point_x = 0

buzzer = Buzzer(0)
ball = Ball(ssd, buzzer)
player = Player(ssd, buzzer, ball, getSPI)
bricks = Bricks(ssd, ball)

def endGame():
    ssd.show()
    buzzer.onOff(True)
    time.sleep_ms(500)
    buzzer.onOff(False)
    ssd.fill_rect(0, 0, 320, 240, Consts.background)
    bricks.addBricks()
    player.initialize()
    time.sleep(3)
    
points = 0
while True:
    if ball.update():
        ssd.text('G A M E  O V E R', 100, 122, Consts.fps)
        endGame()
    player.update()
    player.checkColision()
    result = bricks.colision()
    if result[0] == 0:
        ssd.text('G A M E  END', 110, 122, Consts.fps)
        endGame()
    if result[1] > 0:
        points = points + result[1]
        ssd.fill_rect(0, 230 - 3, 90, 20, Consts.background)
        ssd.text('Points: ' + str(points), 0, 230, Consts.fps)
    ssd.show()
    frame += 1
    if time.ticks_ms() - timestamp > 1000:
        timestamp = time.ticks_ms()
        ssd.fill_rect(270, 230 - 3, 70, 20, Consts.background)
        ssd.text(str(frame) + ' FPS', 270, 230, Consts.fps)
        frame = 0
        gc.collect()





