
class Button:
    delta = 5
    def __init__(self, ssd, x, y, width, height, text, handle, background, text_color, selected_color):
        self.ssd = ssd
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.handle = handle
        self.background = background
        self.text_color = text_color
        self.selected_color = selected_color
        self.selected = False
        
    def check(self, xPos, yPos):
        if xPos > self.x - self.delta and xPos < self.x + self.width + self.delta and yPos > self.y - self.delta and yPos < self.y + self.height + self.delta:
            self.selected = True
            self.draw()
            self.ssd.show()
            return self.handle
        return None
    
    def draw(self):
        color = self.background
        if self.selected:
            color = self.selected_color
        self.selected = False
        self.ssd.fill_rect(self.x, self.y, self.width, self.height, color)
        self.ssd.text(self.text, self.x + 10, self.y + 10, self.text_color)


class Buttons:
    def __init__(self, ssd):
        self.ssd = ssd
        self.buttons = []
        
    def add(self, button):
        self.buttons.append(button)
    
    def draw(self):
        for button in self.buttons:
            button.draw()
    
    def check(self, getSPI):
        get = self.ssd.touch_get(getSPI)
        if get != None: 
            X_Point = int((get[1]-430)*320/3270)
            if(X_Point>320):
                X_Point = 320
            elif X_Point<0:
                X_Point = 0
            Y_Point = 240-int((get[0]-430)*240/3270)
            for button in self.buttons:
                action = button.check(X_Point, Y_Point)
                if action is not None:
                    action()
