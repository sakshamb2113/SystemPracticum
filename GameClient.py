import pygame
from NetworkAdapter import Network
from Player import Player
from time import sleep

pygame.init()

class ClientSocket:
    def __init__(self, ip, port):
        self.n = Network(ip, port)
        self.ip = ip
        self.port = port

        self.font = pygame.font.SysFont('Courier New', 40)
        self.window = pygame.display.set_mode((500, 500))
        self.clock = pygame.time.Clock()
        self.run = False

    def eventQueue(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.run = False

    def startRun(self):
        self.init_connection()
        while self.run:
            # run the game at 60 fps
            self.clock.tick(2000)

            # get all player states from the server
            players = self.n.get_players()
            eventList = pygame.event.get()
            mKeys = pygame.mouse.get_pressed()
            self.movement(mKeys)

            self.eventQueue(eventList)
            self.draw_screen(players)

        self.n.disconnect()
        pygame.quit()

    # initiate connection to the server
    def init_connection(self):
        self.draw_loading_screen()
        while not self.n.ready:
            self.n.connect()
            if self.n.fail:
                pygame.quit()
                break
            sleep(0.01)

        self.window.fill((33, 33, 33))
        self.run = not self.n.fail

    # draw the loading screen when connecting
    def draw_loading_screen(self):
        self.window.fill((33, 33, 33))
        surface = self.font.render("Connecting", False, (255,0,0))
        self.window.blit(surface, (0, 0))
        pygame.display.update()

    def draw_screen(self, player_data):
        # self.window.fill((33, 33, 33))

        for p in player_data:
            p.render(self.window)

        pygame.display.update()

    # process key press events
    def movement(self, mKeys):
        command = ""
        px, py = pygame.mouse.get_pos()

        if mKeys == (1, 0, 0):
            command = str(px)+';'+str(py)
    
        # pygame.draw.rect(screen, (128,128,128), (px,py,10,10))
        self.n.move(command)
