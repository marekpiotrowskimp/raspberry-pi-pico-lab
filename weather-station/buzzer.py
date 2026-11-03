from machine import Pin
import time

class Buzzer:
    BUZZER = 28
    active = False
    state = 0
    start = time.ticks_ms()
    def __init__(self, threshold):
        self.buzzer = Pin(self.BUZZER, Pin.OUT)
        self.buzzer.value(self.state)
        self.threshold = threshold
        
    def activate(self, active):
        self.start = time.ticks_ms()
        self.active = active
        
    def toggle(self):
        if self.active:
            self.active = False
            self.state = 0
            self.buzzer.value(self.state)
        else:
            self.start = time.ticks_ms()
            self.active = True
        
    def update(self):
        if self.active:
            now = time.ticks_ms()
            if now - self.start > self.threshold:
                if self.state > 0:
                    self.state = 0
                else:
                    self.state = 1
                self.buzzer.value(self.state)
                self.start = now
