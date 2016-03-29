import pygame
from pygame.locals import *
from mpd import MPDClient
import codecs
from sys import exit
from time import sleep

# global variables:

# Status
STATUS_SPLASH = 0
STATUS_PLAYLIST = 1
STATUS_PLAYING = 2

# Sizes
SIZE_SCREEN = (320, 240)
HEADER_HEIGHT = 40

# Colors
COLOR_BACKGROUND = (51, 51, 51)
COLOR_TEXT = (255, 255, 255)
COLOR_LINE = (17, 17, 17)


# initialise pygame.
pygame.init()

# create the screen to draw the GUI on.
screen = pygame.display.set_mode(SIZE_SCREEN, 0, 32)
#screen = pygame.display.set_mode(SIZE_SCREEN, FULLSCREEN, 32)
pygame.display.set_caption("AUDIO")

# Start with Splash Screen while loading
status = STATUS_SPLASH

# the main background for AUDIO is a grey surface
background = pygame.surface.Surface(SIZE_SCREEN)
pygame.draw.rect(background, COLOR_BACKGROUND, Rect((0, 0), SIZE_SCREEN))
screen.blit(background, (0,0))
pygame.display.update()

# load the fonts in multiple sizes for AUDIO GUI
font_splash = pygame.font.Font("resources/OpenSans-Light.ttf", 40);
text_splash = font_splash.render("AUDIO", True, COLOR_TEXT)

# print the splash screen AUDIO
screen.blit(text_splash, ((SIZE_SCREEN[0]/2)-(text_splash.get_width()/2),(SIZE_SCREEN[1]/2)-(text_splash.get_height()/2)))
pygame.display.update()

# load the other fonts
font_main = pygame.font.Font("resources/OpenSans-Light.ttf", 14);
font_header = pygame.font.Font("resources/OpenSans-Light.ttf", 18);
font_icon = pygame.font.Font("resources/fontawesome-webfont.ttf", 18);

# create icon surfaces
icon_playlist_header = font_icon.render("\uf001", True, COLOR_TEXT)
icon_playlist = font_icon.render("\uf00b", True, COLOR_TEXT)

# create MPD client object and connect to the local MPD server
client = MPDClient()               
client.timeout = 10
client.idletimeout = None
client.connect("localhost", 6600)

# update the MDP database
client.update()

# load list of available playlists
playlists = client.listplaylists()
playlist_page = 1
playlist_buttons = ()

status = STATUS_PLAYLIST

# functions for drawing different bits
def draw_playlist():
    # draw playlist header
    playlist_header_text = font_header.render("Select Playlist", True, COLOR_TEXT)
    playlist_header = pygame.surface.Surface((SIZE_SCREEN[0], HEADER_HEIGHT))
    pygame.draw.rect(playlist_header, COLOR_LINE, Rect(0, 0, SIZE_SCREEN[0], HEADER_HEIGHT), 1)

    screen.blit(playlist_header, (0, 0))
    screen.blit(playlist_header_text, ((SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((icon_playlist_header.get_width()+5)/2),(HEADER_HEIGHT/2)-(playlist_header_text.get_height()/2)))
    screen.blit(icon_playlist_header, ((SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+icon_playlist_header.get_width()+5)/2),(HEADER_HEIGHT/2)-(icon_playlist_header.get_height()/2)))


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
        draw_playlist()

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