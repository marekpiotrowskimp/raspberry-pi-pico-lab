import time
import array
import random
from micropython import const

class Effect:
    MAX_PIXELS = const(100)
    pixels = []
    def __init__(self, ssd, x, y, width, height, color, frame, background):
        self.ssd = ssd
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.frame = frame
        self.background = background
        for idx in range(MAX_PIXELS):
            pixel = bytearray(4)
            pixel[0] = int(random.uniform(x, x + width))
            pixel[1] = int(random.uniform(y, y + height))
            pixel[2] = int(random.uniform(0, 6)) - 3
            if pixel[2] != 0:
                pixel[2] = 1
            pixel[3] = int(random.uniform(0, 6)) - 3
            if pixel[3] != 0:
                pixel[3] = 1
            self.pixels.append(pixel)
    
    def update(self, count_pixels):
        index = 0
        for pixel in self.pixels:
            self.ssd.pixel(pixel[0], pixel[1], self.background)
            pixel[0] += pixel[2]
            pixel[1] += pixel[3]
            if pixel[0] > self.x + self.width or pixel[0] < self.x:
                pixel[2] *= -1
            if pixel[1] > self.y + self.height or pixel[1] < self.y:
                pixel[3] *= -1
            if index < count_pixels:
                self.ssd.pixel(pixel[0], pixel[1], self.color)
            index += 1
        self.ssd.rect(self.x - 5, self.y -5, self.width + 15, self.height + 10, self.frame)
        

