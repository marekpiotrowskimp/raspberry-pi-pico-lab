from consts import *
import random

class Ball:
    x = 160.0
    y = 210.0
    dx = 3.0
    dy = -2.3
    def __init__(self, ssd, buzzer):
        self.ssd = ssd
        self.buzzer = buzzer
        
    def changeDx(self):
        ranChange = (random.randint(0, 100) / 100)
        if self.dx > 2.7 or self.dx > -2.7:
            self.dx = self.dx - ranChange
        if self.dx < 2.7 or self.dx < -2.7:
            self.dx = self.dx + ranChange 
        self.dx = self.dx * -1
        self.x = self.x + self.dx
        
    def changeDy(self):
        ranChange = (random.randint(0, 100) / 100)
        if self.dy > 2.7 or self.dy > -2.7:
            self.dy = self.dy - ranChange
        if self.dy < 2.7 or self.dy < -2.7:
            self.dy = self.dy + ranChange 
        self.dy = self.dy * -1
        self.y = self.y + self.dy

    def update(self):
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.background)
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        self.buzzer.onOff(False)
        if self.x > 320 or self.x < 0:
            self.changeDx()
            self.buzzer.onOff(True)
        if self.y < 0:
            self.changeDy()
            self.buzzer.onOff(True)
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.ball)
        if self.y > 237:
            self.x = 160.0
            self.y = 210.0
            self.dx = 3.0
            self.dy = -2.3
            return True
        return False
        
    def playerColision(self):
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.background)
        self.dy = self.dy * -1
        self.y = self.y + self.dy
        self.buzzer.onOff(True)
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.ball)
        
    def brickColision(self, direction):
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.background)
        if direction:
            self.changeDx()
        else:
            self.changeDy()
        self.buzzer.onOff(True)
        self.ssd.fill_rect(int(self.x), int(self.y), 3, 3, Consts.ball)
        
        
        