import pygame
from NetworkAdapter import Network
from Player import Player

pygame.init()
n = Network("127.0.0.1", 5003)

font = pygame.font.SysFont('Courier New', 40)
window = pygame.display.set_mode((1000, 1000))
clock = pygame.time.Clock()
run = False


def eventQueue(events):
    global run
    for event in events:
        if event.type == pygame.QUIT:
            run = False


# draw the loading screen when connecting
def draw_loading_screen():
    window.fill((33, 33, 33))
    surface = font.render("Connecting", False, (255,0,0))
    window.blit(surface, (0, 0))
    pygame.display.update()

def draw_screen(player_data):
    # window.fill((33, 33, 33))

    for p in player_data:
        p.render(window)

    pygame.display.update()


# process key press events
def movement(mKeys):
    command = ""
    px, py = pygame.mouse.get_pos()
    if mKeys == (1,0,0):
        command = str(px)+';'+str(py)
            #pygame.draw.rect(screen, (128,128,128), (px,py,10,10))
    n.move(command)



# initiate connection to the server
def init_connection():
    global run
    draw_loading_screen()
    while not n.ready:
        n.connect()
        if n.fail:
            pygame.quit()
            break
    run = not n.fail


def main():
    init_connection()
    while run:
        # run the game at 60 fps
        clock.tick(2000)

        # get all player states from the server
        players = n.get_players()
        eventList = pygame.event.get()
        mKeys = pygame.mouse.get_pressed()
        movement(mKeys)

        eventQueue(eventList)
        draw_screen(players)

    n.disconnect()
    pygame.quit()

main()

