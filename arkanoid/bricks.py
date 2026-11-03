from consts import *
import array

class Brick:
    width = 20
    height = 10
    def __init__(self, ssd, ball, x, y, brickType):
        self.ssd = ssd
        self.ball = ball
        self.x = x
        self.y = y
        self.brickType = brickType
    
    def getColor(self):
        if self.brickType == 0:
            return Consts.brickRed
        elif self.brickType == 1:
            return Consts.brickGreen
        elif self.brickType == 2:
            return Consts.brickBlue
        return Consts.brickRed
    
    def remove(self):
        self.ssd.fill_rect(self.x, self.y, self.width, self.height, Consts.background)
    
    def draw(self):
        self.ssd.fill_rect(self.x, self.y, self.width, self.height, self.getColor())
        self.ssd.rect(self.x, self.y, self.width, self.height, Consts.gray)
    
    def direction(self):
        dx1 = self.ball.x - self.x
        dx2 = self.x + self.width - self.ball.x
        dy1 = self.ball.y - self.y
        dy2 = self.y + self.height - self.ball.y
        dy = min(dy1, dy2)
        dx = min(dx1, dx2)
        return dx < dy
        
    def colision(self):
        if self.x <= self.ball.x and self.x + self.width >= self.ball.x and self.y <= self.ball.y and self.y + self.height >= self.ball.y:
            self.remove()
            self.ball.brickColision(self.direction())
            return True
        return False
            
            
class Bricks:
    bricks = []
    space = 30
    def __init__(self, ssd, ball):
        self.ssd = ssd
        self.ball = ball
        self.addBricks()
    
    def addBricks(self):
        self.bricks = []
        for x in range(0, 16):
            for y in range(9, -1, -1):
                brick = Brick(self.ssd, self.ball, x * Brick.width, y * Brick.height + self.space, y % 3)
                brick.draw()
                self.bricks.append(brick)
    
    def colision(self):
        remove = []
        count = 0
        if self.ball.y > 130:
            return [1, 0]
        for brick in self.bricks:
            count = count + 1
            if brick.colision():
                remove.append(brick)
                break
        countRemoved = 0
        for brick in remove:
            self.bricks.remove(brick)
            countRemoved = countRemoved + 1
        return [count, countRemoved]
            
