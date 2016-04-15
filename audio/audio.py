import pygame
from pygame.locals import *
from mpd import MPDClient
import codecs
import math
from sys import exit
from time import sleep

# initialise pygame.
pygame.init()

# global definitons:
class Settings:
    # Status
    STATUS_SPLASH = 0
    STATUS_PLAYLIST = 1
    STATUS_PLAYING = 2

    # Sizes
    SIZE_SCREEN = (800, 480)
    CONTROL_HEIGHT = 40
    SEPARATOR = 10

    # Colors
    COLOR_BACKGROUND = (51, 51, 51)
    COLOR_LIGHT = (75, 75, 75)
    COLOR_TEXT = (255, 255, 255)
    COLOR_LINE = (17, 17, 17)
    COLOR_HIGHLIGHT = (0, 127, 208)

    # load the other fonts
    FONT_SPLASH = pygame.font.Font("resources/OpenSans-Light.ttf", 40);
    FONT_MAIN = pygame.font.Font("resources/OpenSans-Light.ttf", 14);
    FONT_SMALL = pygame.font.Font("resources/OpenSans-Light.ttf", 12);
    FONT_HEADER = pygame.font.Font("resources/OpenSans-Light.ttf", 18);
    FONT_ICON = pygame.font.Font("resources/fontawesome-webfont.ttf", 18);

    # create icon surfaces
    ICON_MUSIC = FONT_ICON.render("\uf001", True, COLOR_TEXT)
    ICON_PLAYLIST = FONT_ICON.render("\uf03a", True, COLOR_TEXT)
    ICON_SONG = FONT_ICON.render("\uf101", True, COLOR_TEXT)
    ICON_CURRENT = FONT_ICON.render("\uf0da", True, COLOR_TEXT)
    ICON_PLAY = FONT_ICON.render("\uf04b", True, COLOR_TEXT)
    ICON_PAUSE = FONT_ICON.render("\uf04c", True, COLOR_TEXT)
    ICON_SHUTDOWN = FONT_ICON.render("\uf011", True, COLOR_TEXT)
    ICON_UP = FONT_ICON.render("\uf077", True, COLOR_TEXT)
    ICON_DOWN = FONT_ICON.render("\uf078", True, COLOR_TEXT)


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
            subtitle_surface = Settings.FONT_SMALL.render(subtitle, True, Settings.COLOR_TEXT)
            subtitle_width = Settings.SEPARATOR + subtitle_surface.get_width()

            # draw subtitle on button
            surface.blit(subtitle_surface, (((x+width)-subtitle_width), y+(height/2) - subtitle_surface.get_height()/2))
        else:
            subtitle_width = 0
        
        if title != None:
            # render the title for the button and make sure it fits
            title_surface = Settings.FONT_MAIN.render(title, True, Settings.COLOR_TEXT)
            while title_surface.get_width() > (width - subtitle_width):
                title_surface = Settings.FONT_MAIN.render(title[:len(title)-4]+"...", True, Settings.COLOR_TEXT)

            # draw text on button
            surface.blit(title_surface, ((x+Settings.CONTROL_HEIGHT), y+(height/2) - title_surface.get_height()/2))

        # draw icon on button
        if icon != None:
            surface.blit(icon, (x+(Settings.CONTROL_HEIGHT/2)-(icon.get_width()/2), (y+height/2) - icon.get_height()/2))

        return surface

    def draw_button(self, surface, width, height, x, y):           
        # draw button background
        pygame.draw.rect(surface, Settings.COLOR_BACKGROUND, (x,y,width,height), 0)
        # draw button outline
        pygame.draw.rect(surface, Settings.COLOR_LINE, (x,y,width,height), 1)  
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

# class for the Audio GUI
class Audio:
    def __init__(self):
        self.init()
        self.main()

    def init(self):
        # create the screen to draw the GUI on.
        self.screen = pygame.display.set_mode(Settings.SIZE_SCREEN, 0, 32)
        #self.screen = pygame.display.set_mode(Settings.SIZE_SCREEN, FULLSCREEN, 32)
        pygame.display.set_caption("AUDIO")

        # Start with Splash Screen while loading
        self.status = Settings.STATUS_SPLASH

        # the main background for AUDIO is a grey surface
        self.background = pygame.surface.Surface(Settings.SIZE_SCREEN)
        pygame.draw.rect(self.background, Settings.COLOR_BACKGROUND, Rect((0, 0), Settings.SIZE_SCREEN))
        self.screen.blit(self.background, (0,0))
        pygame.display.update()

        # load the fonts in multiple sizes for AUDIO GUI
        text_splash = Settings.FONT_SPLASH.render("AUDIO", True, Settings.COLOR_TEXT)

        # print the splash screen AUDIO
        self.screen.blit(text_splash, ((Settings.SIZE_SCREEN[0]/2)-(text_splash.get_width()/2),(Settings.SIZE_SCREEN[1]/2)-(text_splash.get_height()/2)))
        pygame.display.update()

        # create MPD client object and connect to the local MPD server
        self.client = MPDClient()               
        self.client.timeout = 10
        self.client.idletimeout = None
        self.client.connect("localhost", 6600)

        # update the MDP database
        self.client.update()
        # set MPD client to pause after playing a song
        self.client.single(1)
        # set maximum volume
        #self.client.setvol(100)

        # load list of available playlists
        self.playlists = self.client.listplaylists()
        self.songs = ()
        self.playlist_page = 1
        self.playing_page = 1

        self.playing_rect = None

        self.current_playlist = None
        self.current_song = None
               
        self.page_up = Button()
        self.page_down = Button()
        self.playlist_buttons = []

        self.playing_play = Button()
        self.playing_playlist = Button()
        self.playing_buttons = []

    # function for drawing playlist
    def draw_playlist(self):
        # draw playlist header
        playlist_header_text = Settings.FONT_HEADER.render("Select Playlist", True, Settings.COLOR_TEXT)
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(-1, -1, Settings.SIZE_SCREEN[0]+2, Settings.CONTROL_HEIGHT+2), 1)

        self.screen.blit(playlist_header_text, ((Settings.SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((Settings.ICON_MUSIC.get_width()+Settings.SEPARATOR)/2),(Settings.CONTROL_HEIGHT/2)-(playlist_header_text.get_height()/2)))
        self.screen.blit(Settings.ICON_MUSIC, ((Settings.SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+Settings.ICON_MUSIC.get_width()+Settings.SEPARATOR)/2),(Settings.CONTROL_HEIGHT/2)-(Settings.ICON_MUSIC.get_height()/2)))

        # page controls
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+1), Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+2), 1)
    
        numpages = math.ceil(len(self.playlists)/5)
        indicator_height = int((Settings.CONTROL_HEIGHT * 3) / numpages)
        pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, Rect(Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT*2+indicator_height*(self.playlist_page-1), Settings.CONTROL_HEIGHT, indicator_height), 0)

        # page up/down buttons
        self.page_up.create_button(self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_UP)
        self.page_down.create_button(self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_DOWN)
    
        # clear existing the playlist buttons
        self.playlist_buttons.clear()

        count = 1
        for item in range((self.playlist_page - 1) * 5, min(((self.playlist_page - 1) * 5) + 5, len(self.playlists))):
            button = Button()
            button.create_button(self.screen, 0, count * Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+1, self.playlists[item]['playlist'], None, Settings.ICON_PLAYLIST)
            self.playlist_buttons.append(button)
            count += 1
    
    # draw songs of a playlist
    def draw_player(self):
        # get the current song and set the corresponding page
        if self.current_song['id'] != self.client.currentsong()['id']:
            self.playing_page = math.ceil((int(self.client.currentsong()['pos'])+1)/5)
            self.current_song = self.client.currentsong()
    
        # draw the play controls
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(-1, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0]+2, Settings.CONTROL_HEIGHT+2), 1)

        # play/pause button
        if self.client.status()['state'] == 'play':
            icon = Settings.ICON_PAUSE
        else:
            icon = Settings.ICON_PLAY

        self.playing_play.create_button(self.screen, 0, Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, icon)

        # get elapsed time in seconds
        elapsed_time = int(float(self.client.status()['elapsed']))
    
        # format subtitle as mm:ss
        minutes = math.floor(elapsed_time / 60)
        seconds = elapsed_time - (minutes * 60)
        elapsed = Settings.FONT_MAIN.render("{:0>2d}:{:0>2d}".format(minutes, seconds), True, Settings.COLOR_TEXT)

        self.screen.blit(elapsed, (Settings.CONTROL_HEIGHT+Settings.SEPARATOR,(Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT)+(Settings.CONTROL_HEIGHT/2-elapsed.get_height()/2)))

         # get length in seconds
        length_time = int(self.current_song['time'])
    
        # format subtitle as mm:ss
        minutes = math.floor(length_time / 60)
        seconds = length_time - (minutes * 60)
        length = Settings.FONT_MAIN.render("{:0>2d}:{:0>2d}".format(minutes, seconds), True, Settings.COLOR_TEXT)

        self.screen.blit(length, (Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+Settings.SEPARATOR+length.get_width()),(Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT)+(Settings.CONTROL_HEIGHT/2-length.get_height()/2)))

        # set the playing rect
        width = Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+Settings.SEPARATOR+elapsed.get_width()+Settings.SEPARATOR+Settings.SEPARATOR+length.get_width()+Settings.SEPARATOR+Settings.CONTROL_HEIGHT)
        self.playing_rect = Rect((Settings.CONTROL_HEIGHT+Settings.SEPARATOR+elapsed.get_width()+Settings.SEPARATOR), (Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+Settings.SEPARATOR),width,Settings.CONTROL_HEIGHT-2*Settings.SEPARATOR)
        pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, self.playing_rect, 0)
    
        elapsed_rect = self.playing_rect.inflate(-((1-(elapsed_time/length_time))*width),0).move(-((1-(elapsed_time/length_time))*width)/2,0)
        pygame.draw.rect(self.screen, Settings.COLOR_HIGHLIGHT, elapsed_rect, 0)

        # return to playlist button
        self.playing_playlist.create_button(self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_PLAYLIST)

         # page controls
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+1), -1, Settings.CONTROL_HEIGHT+2, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+2), 1)
    
        numpages = math.ceil(len(self.songs)/5)
        indicator_height = int((Settings.CONTROL_HEIGHT * 3) / numpages)
        pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, Rect(Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+indicator_height*(self.playing_page-1), Settings.CONTROL_HEIGHT, indicator_height), 0)

        # page up/down buttons
        self.page_up.create_button(self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), 0, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_UP)
        self.page_down.create_button(self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT*2, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_DOWN)
    
         # clear existing the song buttons
        self.playing_buttons.clear()

        count = 0
        for item in range((self.playing_page - 1) * 5, min(((self.playing_page - 1) * 5) + 5, len(self.songs))):
            # get lenght of song in seconds
            time = self.songs[item]['time']

            # format subtitle as mm:ss
            minutes = math.floor(int(time) / 60)
            seconds = int(time) - (minutes * 60)
            subtitle = "{:0>2d}:{:0>2d}".format(minutes, seconds)

            # check if this is the current song
            if self.current_song['id'] == self.songs[item]['id']:
                icon = Settings.ICON_CURRENT
            else:
                icon = Settings.ICON_SONG

            button = Button()
            button.create_button(self.screen, 0, count * Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+1, self.songs[item]['title'], subtitle, icon)
            self.playing_buttons.append(button)
            count += 1 

    def main(self):
        self.status = Settings.STATUS_PLAYLIST

        # enter loop for drawing the AUDIO gui
        while True:
            # check for events.
            for event in pygame.event.get():
                if event.type == QUIT:
                    # disconnect the MPD client
                    self.client.stop()
                    self.client.close()
                    self.client.disconnect()             
            
                    # exit the AUDIO gui
                    pygame.quit()
                    exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if self.status == Settings.STATUS_PLAYLIST:
                        if self.page_up.clicked(pygame.mouse.get_pos()):
                            if self.playlist_page > 1:
                                self.playlist_page -= 1
                        elif self.page_down.clicked(pygame.mouse.get_pos()):
                            if self.playlist_page < math.ceil(len(self.playlists)/5):
                                self.playlist_page += 1
                        else:
                            for btn in self.playlist_buttons:
                                if btn.clicked(pygame.mouse.get_pos()):
                                    self.current_playlist = btn.title

                                    # set page to 1
                                    self.playing_page = 1

                                    # clear the current list
                                    self.client.clear()
                                    # load the playlist
                                    self.client.load(self.current_playlist)

                                    # get songs in playlist
                                    self.songs = self.client.playlistinfo()
                            
                                    # load the first song by playing and immediatly pausing it
                                    self.client.play()
                                    self.client.pause()

                                    self.current_song = self.client.currentsong()
                           
                                    # set the status
                                    self.status = Settings.STATUS_PLAYING

                    elif self.status == Settings.STATUS_PLAYING:
                        if self.page_up.clicked(pygame.mouse.get_pos()):
                            if self.playing_page > 1:
                                self.playing_page -= 1
                        elif self.page_down.clicked(pygame.mouse.get_pos()):
                            if self.playing_page < math.ceil(len(self.songs)/5):
                                self.playing_page += 1
                        elif self.playing_playlist.clicked(pygame.mouse.get_pos()):
                            self.client.clear()
                            self.playing_page = 1
                            self.status = STATUS_PLAYLIST
                        elif self.playing_play.clicked(pygame.mouse.get_pos()):
                            if self.client.status()['state'] == 'play':
                                self.client.pause()
                            else:
                                self.client.play()

                            # move to the page that has this song on it
                            self.playing_page = math.ceil((int(self.client.currentsong()['pos'])+1)/5)
                        else:
                            item = 0
                            for btn in self.playing_buttons:
                                if btn.clicked(pygame.mouse.get_pos()):
                                    # select the song
                                    self.client.playid(self.songs[(self.playing_page-1)*5+item]['id'])
                                    self.current_song = self.client.currentsong()
                                    self.client.pause()
                                item +=1
                        
            # draw background
            self.screen.blit(self.background, (0,0))

            # check the status of AUDIO gui
            if self.status == Settings.STATUS_PLAYLIST:
                self.draw_playlist()

            elif self.status == Settings.STATUS_PLAYING:
                self.draw_player()
    
            # update the screen
            pygame.display.update()

            # pause updating the screen to preserve CPU
            sleep(0.05)



if __name__ == '__main__':
    obj = Audio()