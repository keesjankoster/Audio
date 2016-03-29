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
CONTROL_HEIGHT = 40

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
playlist_buttons = []

status = STATUS_PLAYLIST

# classes for buttons
class Button:
    def create_button(self, surface, color, x, y, length, height, width, text, text_color):
        surface = self.draw_button(surface, color, length, height, x, y, width)
        surface = self.write_text(surface, text, text_color, length, height, x, y)
        self.rect = pygame.Rect(x,y, length, height)
        return surface

    def write_text(self, surface, text, text_color, length, height, x, y):
        font_size = int(length//len(text))
        myFont = pygame.font.SysFont("Calibri", font_size)
        myText = myFont.render(text, 1, text_color)
        surface.blit(myText, ((x+length/2) - myText.get_width()/2, (y+height/2) - myText.get_height()/2))
        return surface

    def draw_button(self, surface, color, length, height, x, y, width):           
        for i in range(1,10):
            s = pygame.Surface((length+(i*2),height+(i*2)))
            s.fill(color)
            alpha = (255/(i+2))
            if alpha <= 0:
                alpha = 1
            s.set_alpha(alpha)
            pygame.draw.rect(s, color, (x-i,y-i,length+i,height+i), width)
            surface.blit(s, (x-i,y-i))
        pygame.draw.rect(surface, color, (x,y,length,height), 0)
        pygame.draw.rect(surface, (190,190,190), (x,y,length,height), 1)  
        return surface

    def clicked(self, mouse):
        if mouse[0] > self.rect.topleft[0]:
            if mouse[1] > self.rect.topleft[1]:
                if mouse[0] < self.rect.bottomright[0]:
                    if mouse[1] < self.rect.bottomright[1]:
                        print("Some button was pressed!")
                        return True
                    else: return False
                else: return False
            else: return False
        else: return False



# functions for drawing different bits
def draw_playlist():
    # draw playlist header
    playlist_header_text = font_header.render("Select Playlist", True, COLOR_TEXT)
    pygame.draw.rect(screen, COLOR_LINE, Rect(-1, -1, SIZE_SCREEN[0]+2, CONTROL_HEIGHT+2), 1)

    screen.blit(playlist_header_text, ((SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((icon_playlist_header.get_width()+10)/2),(CONTROL_HEIGHT/2)-(playlist_header_text.get_height()/2)))
    screen.blit(icon_playlist_header, ((SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+icon_playlist_header.get_width()+10)/2),(CONTROL_HEIGHT/2)-(icon_playlist_header.get_height()/2)))

    # clear existing the playlist buttons
    if len(playlist_buttons) > 0:
        for item in range(len(playlist_buttons)-1,0):
            del playlist_buttons[item]
    
    count = 1
    for item in range((playlist_page - 1) * 5, min(((playlist_page - 1) * 5) + 5, len(playlists))):
        button = Button()
        button.create_button(screen, COLOR_BACKGROUND, 0, count * CONTROL_HEIGHT, SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT, 1, playlists[item]['playlist'], COLOR_TEXT)
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