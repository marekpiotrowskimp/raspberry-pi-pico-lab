from machine import Pin, PWM
from time import sleep

led = PWM(Pin(25))

def ledon(brightness=65535):
    led.duty_u16(brightness)


while True:
    for a in range(0, 65000, 1000):
        ledon(a)
        sleep(0.005)
    for a in range(65000, 0, -1000):
        ledon(a)
        sleep(0.005)