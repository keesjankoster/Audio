import pygame
from pygame.locals import *
from mpd import MPDClient
from sys import exit
from time import sleep

# global variables
STATUS_SPLASH = 0
STATUS_PLAYLIST = 1
STATUS_PLAYING = 2

status = STATUS_SPLASH

# initialise pygame.
pygame.init()

# create the screen to draw the GUI on.
screen = pygame.display.set_mode((320, 240), 0, 32)
#screen = pygame.display.set_mode((1920, 1080), FULLSCREEN, 32)
pygame.display.set_caption("AUDIO")

# the main background for AUDIO is a grey surface
background = pygame.surface.Surface((320, 240))
pygame.draw.rect(background, (51, 51, 51), Rect(0, 0, 320, 240))
screen.blit(background, (0,0))
pygame.display.update()

# load the fonts in multiple sizes for AUDIO GUI
font_splash = pygame.font.Font("resources/OpenSans-Light.ttf", 40);
text_splash = font_splash.render("AUDIO", True, (255, 255, 255))

# print the splash screen AUDIO
screen.blit(text_splash, ((320/2)-(text_splash.get_width()/2),(240/2)-(text_splash.get_height()/2)))
pygame.display.update()

# load the other fonts
font_main = pygame.font.Font("resources/OpenSans-Light.ttf", 14);
font_icon = pygame.font.Font("resources/fontawesome-webfont.ttf", 20);

# create MPD client object and connect to the local MPD server
client = MPDClient()               
client.timeout = 10
client.idletimeout = None
client.connect("localhost", 6600)

# update the MDP database
client.update()






status = STATUS_PLAYLIST

# enter loop while drawing the AUDIO gui.
while True:
    # check for events.
    for event in pygame.event.get():
        if event.type == QUIT:
            # disconnect the MPD client
            client.stop()
            client.close()
            client.disconnect()             
            
            # exit the AUDIO gui
            pygame.quit()
            exit()

    # draw background
    screen.blit(background, (0,0))

    # check the status of AUDIO gui
    if status == STATUS_PLAYLIST:
        playlist = font_main.render("PLAYLIST", True, (255, 255, 255))
        screen.blit(playlist, ((320/2)-(playlist.get_width()/2),(240/2)-(playlist.get_height()/2)))

    #elif status == STATUS_PLAYING:

    
    # update the screen
    pygame.display.update()

    # pause updating the screen to preserve CPU
    sleep(0.05)



#pygame.draw.rect(background, (51, 51, 51), Rect(0, 0, 320, 240))

#font_main = pygame.font.Font("resources/OpenSans-Light.ttf", 40);
#text = font_main.render("AUDIO", True, (255, 255, 255))


#print(client.listplaylists())
#print(client.listplaylistinfo("Cracking Easter!"))

#client.single(1)
#client.clear()
#client.load("Cracking Easter!")
#client.play()