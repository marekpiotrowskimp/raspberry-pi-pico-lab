from consts import *
import time

class Player:
    width = 40
    height = 5
    level = 220
    last_point_x = 160
    def __init__(self, ssd, buzzer, ball, getSPI):
        self.ssd = ssd
        self.buzzer = buzzer
        self.getSPI = getSPI
        self.ball = ball
        self.redraw(self.last_point_x)
        self.timestamp = time.ticks_ms()
        
    def update(self):
        if time.ticks_ms() - self.timestamp > 30:
            self.timestamp = time.ticks_ms()
            position = self.ssd.touch_get(self.getSPI)
            if position != None:
                point_x = int((position[1]-430)*320/3270)
                if (point_x > 320):
                    point_x = 320
                elif point_x < 0:
                    point_x = 0
                point_y = 240-int((position[0]-430)*240/3270)
                self.redraw(point_x)
                self.last_point_x = point_x
    
    def initialize(self):
        self.last_point_x = 160
        self.redraw(self.last_point_x)
    
    def redraw(self, point_x):
        self.ssd.fill_rect(self.last_point_x - int(self.width / 2), self.level, self.width, self.height, Consts.background)
        self.ssd.fill_rect(point_x - int(self.width / 2), self.level, self.width, self.height, Consts.player)
    
    def checkColision(self):
        if self.last_point_x - self.width / 2 <= self.ball.x and self.last_point_x + self.width / 2 >= self.ball.x and self.ball.y >= self.level and self.ball.y <= self.level + self.height:
            self.ball.playerColision()
            self.redraw(self.last_point_x)
            
        
