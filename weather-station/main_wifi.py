from time import sleep, sleep_ms
from machine import Pin, PWM, I2C, UART
import screen
import wifi

sdaPIN = Pin(26)
sclPIN = Pin(27)

i2c = I2C(1, sda=sdaPIN, scl=sclPIN, freq=128000)
sleep(0.1)

devices = i2c.scan()
if devices:
    for d in devices:
        print(hex(d))

scr = screen.Screen(i2c, 0x27)
scr.position(0, 0)
scr.write_line('Server 1.0 - ')

led = PWM(Pin(25))

def ledon(brightness=65535):
    led.duty_u16(brightness)

uart = UART(0, 115200)
wifi = wifi.WIFI(uart)

scr.write_line('START')

while True:
    
    for a in range(0, 65000, 1000):
        wifi.receive()
        ledon(a)
        sleep(0.001)

    for a in range(65000, 0, -1000):
        wifi.receive()
        ledon(a)
        sleep(0.001)
