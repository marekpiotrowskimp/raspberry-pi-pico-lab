from buttons import Buttons, Button
from images import ImagesTool

class ScreensRpi:

    def __init__(self, ssd, icons):
        self.ssd = ssd
        self.BLACK = 0 #ssd.rgb(0x00, 0x00, 0x00)
        self.GRAY = 1 # ssd.rgb(0x33, 0x33, 0x33)
        self.LIGHT_GRAY = 2 # ssd.rgb(0x55, 0x55, 0x55)
        self.PRIME = 3 # ssd.rgb(0xAA, 0x11, 0x11)
        self.TEXT = 4 # ssd.rgb(0xEE, 0xEE, 0xEE)
        self.TERMINAL = 5 # ssd.rgb(0x00, 0xFF, 0x00)
        self.PIXELS = 6
        self.MINUTS = 13
        self.HOUR = 14
        self.ICON = 15
        self.icons = icons
        
    def booting_screen(self):
        self.ssd.fill(self.BLACK)
        #self.ssd.fill_rect(10, 10, 300, 40, self.GRAY)
        #self.ssd.text('Raspberry PI Pico version 0.1', 20, 20, self.TEXT)
        self.ssd.text('Booting...', 0, 0, self.TERMINAL)
        self.buttons = Buttons(self.ssd)
        
    def initial_screen(self, image_action, buzzer_action):
        self.ssd.fill(self.BLACK)
        #self.ssd.fill_rect(10, 10, 300, 40, self.GRAY)
        #self.ssd.text('Raspberry PI Pico version 0.1', 20, 20, self.TEXT)
        #self.ssd.text('Marek Piotrowski (c)', 20, 33, self.TEXT)
        self.buttons = Buttons(self.ssd)
        self.icons.draw_icon(6, 0, 0, 64, 64)
        self.icons.draw_icon(0, 90, 0, 64, 64)
        self.icons.draw_icon(1, 160, 0, 64, 64)
        self.icons.draw_icon(2, 240, 0, 64, 64)
        self.icons.draw_icon(3, 90, 130, 64, 64)
        #self.buttons.add(Button(self.ssd, 10, 60, 100, 25, "Show Image", image_action, self.GRAY, self.TEXT, self.PRIME))
        #self.buttons.add(Button(self.ssd, 120, 60, 100, 25, "Buzzer", buzzer_action, self.GRAY, self.TEXT, self.PRIME))
        
    def image_screen(self, back_action):
        ImagesTool(self.ssd).draw_data_fast("tiger3.data")
        self.buttons = Buttons(self.ssd)
        self.buttons.add(Button(self.ssd, 5, 5, 50, 25, "<--", back_action, self.GRAY, self.TEXT, self.PRIME))
        
    def update(self, getSPI):
        self.buttons.check(getSPI)
        self.buttons.draw()