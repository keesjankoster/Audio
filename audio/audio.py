import pygame
from pygame.locals import *
from mpd import MPDClient
import codecs
import math
from sys import exit
from time import sleep

# global variables:

# Status
STATUS_SPLASH = 0
STATUS_PLAYLIST = 1
STATUS_PLAYING = 2

# Sizes
SIZE_SCREEN = (320, 240)
CONTROL_HEIGHT = 40
SEPERATOR = 10

# Colors
COLOR_BACKGROUND = (51, 51, 51)
COLOR_LIGHT = (75, 75, 75)
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
ICON_MUSIC = font_icon.render("\uf001", True, COLOR_TEXT)
ICON_PLAYLIST = font_icon.render("\uf03a", True, COLOR_TEXT)
ICON_PLAY = font_icon.render("\uf04b", True, COLOR_TEXT)
ICON_PAUSE = font_icon.render("\uf04c", True, COLOR_TEXT)
ICON_SHUTDOWN = font_icon.render("\uf011", True, COLOR_TEXT)
ICON_UP = font_icon.render("\uf077", True, COLOR_TEXT)
ICON_DOWN = font_icon.render("\uf078", True, COLOR_TEXT)

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
playlist_buttons = []

status = STATUS_PLAYLIST

# classes for buttons
class Button:
    def create_button(self, surface, x, y, width, height, text, icon):
        # draw the button surface and outline
        surface = self.draw_button(surface, width, height, x, y)
        # draw the text and/or icon
        surface = self.draw_contents(surface, text, icon, width, height, x, y)
        # store the rect of the button
        self.rect = pygame.Rect(x,y, width, height)
        return surface

    def draw_contents(self, surface, text, icon, width, height, x, y):
        if text != None:
            # render the text for the button and make sure it fits
            text_surface = font_main.render(text, True, COLOR_TEXT)
            while text_surface.get_width() > width:
                text_surface = font_main.render(text[:len(text)-4]+"...", True, COLOR_TEXT)

            # draw text on button
            surface.blit(text_surface, ((x+CONTROL_HEIGHT), y+(height/2) - text_surface.get_height()/2))

        # draw icon on button
        if icon != None:
            surface.blit(icon, (x+(CONTROL_HEIGHT/2)-(icon.get_width()/2), (y+height/2) - icon.get_height()/2))

        return surface

    def draw_button(self, surface, width, height, x, y):           
        # draw button background
        pygame.draw.rect(surface, COLOR_BACKGROUND, (x,y,width,height), 0)
        # draw button outline
        pygame.draw.rect(surface, COLOR_LINE, (x,y,width,height), 1)  
        return surface

    def clicked(self, mouse):
        if mouse[0] > self.rect.topleft[0]:
            if mouse[1] > self.rect.topleft[1]:
                if mouse[0] < self.rect.bottomright[0]:
                    if mouse[1] < self.rect.bottomright[1]:
                        return True
                    else: return False
                else: return False
            else: return False
        else: return False


# Global Button variables
playlist_up = Button()
playlist_down = Button()


# functions for drawing different bits
def draw_playlist():
    # draw playlist header
    playlist_header_text = font_header.render("Select Playlist", True, COLOR_TEXT)
    pygame.draw.rect(screen, COLOR_LINE, Rect(-1, -1, SIZE_SCREEN[0]+2, CONTROL_HEIGHT+2), 1)

    screen.blit(playlist_header_text, ((SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((ICON_MUSIC.get_width()+SEPERATOR)/2),(CONTROL_HEIGHT/2)-(playlist_header_text.get_height()/2)))
    screen.blit(ICON_MUSIC, ((SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+ICON_MUSIC.get_width()+SEPERATOR)/2),(CONTROL_HEIGHT/2)-(ICON_MUSIC.get_height()/2)))

    # page controls
    pygame.draw.rect(screen, COLOR_LINE, Rect(SIZE_SCREEN[0]-(CONTROL_HEIGHT+1), CONTROL_HEIGHT, CONTROL_HEIGHT+2, SIZE_SCREEN[1]-CONTROL_HEIGHT+2), 1)
    
    numpages = math.ceil(len(playlists)/5)
    indicator_height = int((CONTROL_HEIGHT * 3) / numpages)
    pygame.draw.rect(screen, COLOR_LIGHT, Rect(SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT*2+indicator_height*(playlist_page-1), CONTROL_HEIGHT, indicator_height), 0)

    # page up/down buttons
    playlist_up.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, ICON_UP)
    playlist_down.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), SIZE_SCREEN[1] - CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, ICON_DOWN)
    


    # clear existing the playlist buttons
    if len(playlist_buttons) > 0:
        for item in range(len(playlist_buttons)-1,0):
            del playlist_buttons[item]
    
    count = 1
    for item in range((playlist_page - 1) * 5, min(((playlist_page - 1) * 5) + 5, len(playlists))):
        button = Button()
        button.create_button(screen, 0, count * CONTROL_HEIGHT, SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT+1, playlists[item]['playlist'], ICON_PLAYLIST)
        playlist_buttons.append(button)
        count += 1

   


# enter loop while drawing the AUDIO gui
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
        elif event.type == MOUSEBUTTONDOWN:
            if status == STATUS_PLAYLIST:
                if playlist_up.clicked(pygame.mouse.get_pos()):
                    if playlist_page > 1:
                        playlist_page -= 1
                elif playlist_down.clicked(pygame.mouse.get_pos()):
                    if playlist_page < math.ceil(len(playlists)/5):
                        playlist_page += 1
                

                    
            

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