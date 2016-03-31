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
SEPARATOR = 10

# Colors
COLOR_BACKGROUND = (51, 51, 51)
COLOR_LIGHT = (75, 75, 75)
COLOR_TEXT = (255, 255, 255)
COLOR_LINE = (17, 17, 17)
COLOR_HIGHLIGHT = (0, 127, 208)

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
font_small = pygame.font.Font("resources/OpenSans-Light.ttf", 12);
font_header = pygame.font.Font("resources/OpenSans-Light.ttf", 18);
font_icon = pygame.font.Font("resources/fontawesome-webfont.ttf", 18);

# create icon surfaces
ICON_MUSIC = font_icon.render("\uf001", True, COLOR_TEXT)
ICON_PLAYLIST = font_icon.render("\uf03a", True, COLOR_TEXT)
ICON_SONG = font_icon.render("\uf101", True, COLOR_TEXT)
ICON_CURRENT = font_icon.render("\uf0da", True, COLOR_TEXT)
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
# set MPD client to pause after playing a song
client.single(1)
# set maximum volume
#client.setvol(100)

# load list of available playlists
playlists = client.listplaylists()
songs = ()
playlist_page = 1
playing_page = 1

playing_rect = None

current_playlist = None
current_song = None

status = STATUS_PLAYLIST

# classes for buttons
class Button:
    def create_button(self, surface, x, y, width, height, title, subtitle, icon):
        # draw the button surface and outline
        surface = self.draw_button(surface, width, height, x, y)
        # draw the text and/or icon
        surface = self.draw_contents(surface, title, subtitle, icon, width, height, x, y)
        # store the rect of the button
        self.rect = pygame.Rect(x,y, width, height)
        # store text
        self.title = title
        return surface

    def draw_contents(self, surface, title, subtitle, icon, width, height, x, y):
        if subtitle != None:
            # render the text for the button and make sure it fits
            subtitle_surface = font_small.render(subtitle, True, COLOR_TEXT)
            subtitle_width = SEPARATOR + subtitle_surface.get_width()

            # draw subtitle on button
            surface.blit(subtitle_surface, (((x+width)-subtitle_width), y+(height/2) - subtitle_surface.get_height()/2))
        else:
            subtitle_width = 0
        
        if title != None:
            # render the title for the button and make sure it fits
            title_surface = font_main.render(title, True, COLOR_TEXT)
            while title_surface.get_width() > (width - subtitle_width):
                title_surface = font_main.render(title[:len(title)-4]+"...", True, COLOR_TEXT)

            # draw text on button
            surface.blit(title_surface, ((x+CONTROL_HEIGHT), y+(height/2) - title_surface.get_height()/2))

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
page_up = Button()
page_down = Button()
playlist_buttons = []

playing_play = Button()
playing_playlist = Button()
playing_buttons = []

# functions for drawing different bits
def draw_playlist():
    # draw playlist header
    playlist_header_text = font_header.render("Select Playlist", True, COLOR_TEXT)
    pygame.draw.rect(screen, COLOR_LINE, Rect(-1, -1, SIZE_SCREEN[0]+2, CONTROL_HEIGHT+2), 1)

    screen.blit(playlist_header_text, ((SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((ICON_MUSIC.get_width()+SEPARATOR)/2),(CONTROL_HEIGHT/2)-(playlist_header_text.get_height()/2)))
    screen.blit(ICON_MUSIC, ((SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+ICON_MUSIC.get_width()+SEPARATOR)/2),(CONTROL_HEIGHT/2)-(ICON_MUSIC.get_height()/2)))

    # page controls
    pygame.draw.rect(screen, COLOR_LINE, Rect(SIZE_SCREEN[0]-(CONTROL_HEIGHT+1), CONTROL_HEIGHT, CONTROL_HEIGHT+2, SIZE_SCREEN[1]-CONTROL_HEIGHT+2), 1)
    
    numpages = math.ceil(len(playlists)/5)
    indicator_height = int((CONTROL_HEIGHT * 3) / numpages)
    pygame.draw.rect(screen, COLOR_LIGHT, Rect(SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT*2+indicator_height*(playlist_page-1), CONTROL_HEIGHT, indicator_height), 0)

    # page up/down buttons
    page_up.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, ICON_UP)
    page_down.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), SIZE_SCREEN[1] - CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, ICON_DOWN)
    
    # clear existing the playlist buttons
    playlist_buttons.clear()

    count = 1
    for item in range((playlist_page - 1) * 5, min(((playlist_page - 1) * 5) + 5, len(playlists))):
        button = Button()
        button.create_button(screen, 0, count * CONTROL_HEIGHT, SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT+1, playlists[item]['playlist'], None, ICON_PLAYLIST)
        playlist_buttons.append(button)
        count += 1

# open a playlist
def draw_player():
    global current_song
    global playing_page
    global playing_rect

    # get the current song and set the corresponding page
    if current_song['id'] != client.currentsong()['id']:
        playing_page = math.ceil((int(client.currentsong()['pos'])+1)/5)
        current_song = client.currentsong()
    
    # draw the play controls
    pygame.draw.rect(screen, COLOR_LINE, Rect(-1, SIZE_SCREEN[1]-CONTROL_HEIGHT, SIZE_SCREEN[0]+2, CONTROL_HEIGHT+2), 1)

    # play/pause button
    if client.status()['state'] == 'play':
        icon = ICON_PAUSE
    else:
        icon = ICON_PLAY

    playing_play.create_button(screen, 0, SIZE_SCREEN[1] - CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, icon)

    # get elapsed time in seconds
    elapsed_time = int(float(client.status()['elapsed']))
    
    # format subtitle as mm:ss
    minutes = math.floor(elapsed_time / 60)
    seconds = elapsed_time - (minutes * 60)
    elapsed = font_main.render("{:0>2d}:{:0>2d}".format(minutes, seconds), True, COLOR_TEXT)

    screen.blit(elapsed, (CONTROL_HEIGHT+SEPARATOR,(SIZE_SCREEN[1] - CONTROL_HEIGHT)+(CONTROL_HEIGHT/2-elapsed.get_height()/2)))

     # get length in seconds
    length_time = int(current_song['time'])
    
    # format subtitle as mm:ss
    minutes = math.floor(length_time / 60)
    seconds = length_time - (minutes * 60)
    length = font_main.render("{:0>2d}:{:0>2d}".format(minutes, seconds), True, COLOR_TEXT)

    screen.blit(length, (SIZE_SCREEN[0]-(CONTROL_HEIGHT+SEPARATOR+length.get_width()),(SIZE_SCREEN[1]-CONTROL_HEIGHT)+(CONTROL_HEIGHT/2-length.get_height()/2)))

    # set the playing rect
    width = SIZE_SCREEN[0]-(CONTROL_HEIGHT+SEPARATOR+elapsed.get_width()+SEPARATOR+SEPARATOR+length.get_width()+SEPARATOR+CONTROL_HEIGHT)
    playing_rect = Rect((CONTROL_HEIGHT+SEPARATOR+elapsed.get_width()+SEPARATOR), (SIZE_SCREEN[1]-CONTROL_HEIGHT+SEPARATOR),width,CONTROL_HEIGHT-2*SEPARATOR)
    pygame.draw.rect(screen, COLOR_LIGHT, playing_rect, 0)
    
    elapsed_rect = playing_rect.inflate(-((1-(elapsed_time/length_time))*width),0).move(-((1-(elapsed_time/length_time))*width)/2,0)
    pygame.draw.rect(screen, COLOR_HIGHLIGHT, elapsed_rect, 0)

    # return to playlist button
    playing_playlist.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), SIZE_SCREEN[1] - CONTROL_HEIGHT, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, ICON_PLAYLIST)

     # page controls
    pygame.draw.rect(screen, COLOR_LINE, Rect(SIZE_SCREEN[0]-(CONTROL_HEIGHT+1), -1, CONTROL_HEIGHT+2, SIZE_SCREEN[1]-CONTROL_HEIGHT+2), 1)
    
    numpages = math.ceil(len(songs)/5)
    indicator_height = int((CONTROL_HEIGHT * 3) / numpages)
    pygame.draw.rect(screen, COLOR_LIGHT, Rect(SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT+indicator_height*(playing_page-1), CONTROL_HEIGHT, indicator_height), 0)

    # page up/down buttons
    page_up.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), 0, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, ICON_UP)
    page_down.create_button(screen, SIZE_SCREEN[0] - (CONTROL_HEIGHT+1), SIZE_SCREEN[1] - CONTROL_HEIGHT*2, CONTROL_HEIGHT+2, CONTROL_HEIGHT+1, None, None, ICON_DOWN)
    
     # clear existing the song buttons
    playing_buttons.clear()

    count = 0
    for item in range((playing_page - 1) * 5, min(((playing_page - 1) * 5) + 5, len(songs))):
        # get lenght of song in seconds
        time = songs[item]['time']

        # format subtitle as mm:ss
        minutes = math.floor(int(time) / 60)
        seconds = int(time) - (minutes * 60)
        subtitle = "{:0>2d}:{:0>2d}".format(minutes, seconds)

        # check if this is the current song
        if current_song['id'] == songs[item]['id']:
            icon = ICON_CURRENT
        else:
            icon = ICON_SONG

        button = Button()
        button.create_button(screen, 0, count * CONTROL_HEIGHT, SIZE_SCREEN[0] - CONTROL_HEIGHT, CONTROL_HEIGHT+1, songs[item]['title'], subtitle, icon)
        playing_buttons.append(button)
        count += 1



# enter loop for drawing the AUDIO gui
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
                if page_up.clicked(pygame.mouse.get_pos()):
                    if playlist_page > 1:
                        playlist_page -= 1
                elif page_down.clicked(pygame.mouse.get_pos()):
                    if playlist_page < math.ceil(len(playlists)/5):
                        playlist_page += 1
                else:
                    for btn in playlist_buttons:
                        if btn.clicked(pygame.mouse.get_pos()):
                            current_playlist = btn.title

                            # set page to 1
                            playing_page = 1

                            # clear the current list
                            client.clear()
                            # load the playlist
                            client.load(current_playlist)

                            # get songs in playlist
                            songs = client.playlistinfo()
                            
                            # load the first song by playing and immediatly pausing it
                            client.play()
                            client.pause()

                            current_song = client.currentsong()
                           
                            # set the status
                            status = STATUS_PLAYING

            elif status == STATUS_PLAYING:
                if page_up.clicked(pygame.mouse.get_pos()):
                    if playing_page > 1:
                        playing_page -= 1
                elif page_down.clicked(pygame.mouse.get_pos()):
                    if playing_page < math.ceil(len(songs)/5):
                        playing_page += 1
                elif playing_playlist.clicked(pygame.mouse.get_pos()):
                    client.clear()
                    playing_page = 1
                    status = STATUS_PLAYLIST
                elif playing_play.clicked(pygame.mouse.get_pos()):
                    if client.status()['state'] == 'play':
                        client.pause()
                    else:
                        client.play()

                    # move to the page that has this song on it
                    playing_page = math.ceil((int(client.currentsong()['pos'])+1)/5)
                else:
                    item = 0
                    for btn in playing_buttons:
                        if btn.clicked(pygame.mouse.get_pos()):
                            # select the song
                            client.playid(songs[(playing_page-1)*5+item]['id'])
                            current_song = client.currentsong()
                            client.pause()
                        item +=1
                        


                    
            

    # draw background
    screen.blit(background, (0,0))

    # check the status of AUDIO gui
    if status == STATUS_PLAYLIST:
        draw_playlist()

    elif status == STATUS_PLAYING:
        draw_player()
    
    # update the screen
    pygame.display.update()

    # pause updating the screen to preserve CPU
    sleep(0.05)