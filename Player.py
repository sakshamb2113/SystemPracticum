import pygame


class Player(pygame.sprite.Sprite):
    """
    Using the pygame sprite as the parent object, store the state of the
    current player.
    """
    def __init__(self, x, y, width, height, color):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.color = color

        # how far each player moves each frame
        self.x_vel = 10
        self.y_vel = 10

    def get_rectangle(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


    def render(self, window):
        #pygame.draw.rect(window, self.color, self.get_rectangle())
        pygame.draw.rect(window, self.color, (self.x,self.y,10,10))


    # data received from the server to move
    def move(self, direction, bounds):
        # python does not support switch case
        l = direction.split(";")
        if len(l)==2:
            self.x,self.y = l[0],l[1]
        if self.x!="" and self.y != "":
            self.x,self.y = int(self.x),int(self.y)
       
