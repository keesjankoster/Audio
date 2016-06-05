import ptvsd
ptvsd.enable_attach(secret='luketheatre')

import pygame
from pygame.locals import *
import codecs
from omxplayer import OMXPlayer
import math
from sys import exit
from time import sleep

from dbus import DBusException

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler 

from mutagen.mp3 import MP3

import os
os.environ["SDL_FBDEV"] = "/dev/fb0"
os.environ["SDL_MOUSEDRV"] = "TSLIB"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"

# initialise pygame.
pygame.init()

# global definitons:
class Settings:
    # Paths
    PATH_MUSIC = "/home/pi/audio/audio/music"
    PATH_PLAYLISTS = "/home/pi/audio/audio/playlists"

    # Status
    STATUS_SPLASH = 0
    STATUS_PLAYLIST = 1
    STATUS_PLAYING = 2

    # Button types
    BUTTON_TYPE_CATEGORY = 0
    BUTTON_TYPE_PLAYLIST = 1
    BUTTON_TYPE_SONG = 2

    # Sizes
    SIZE_SCREEN = (800, 480)
    CONTROL_HEIGHT = 60
    SEPARATOR = 10
    ITEMS = 7

    # Colors
    COLOR_BACKGROUND = (51, 51, 51)
    COLOR_LIGHT = (75, 75, 75)
    COLOR_TEXT = (255, 255, 255)
    COLOR_LINE = (17, 17, 17)
    COLOR_HIGHLIGHT = (0, 127, 208)

    # load the other fonts
    FONT_SPLASH = pygame.font.Font("resources/OpenSans-Light.ttf", 72);
    FONT_MAIN = pygame.font.Font("resources/OpenSans-Light.ttf", 22);
    FONT_SMALL = pygame.font.Font("resources/OpenSans-Light.ttf", 18);
    FONT_HEADER = pygame.font.Font("resources/OpenSans-Light.ttf", 24);
    FONT_ICON = pygame.font.Font("resources/fontawesome-webfont.ttf", 24);

    # create icon surfaces
    ICON_MUSIC = FONT_ICON.render("\uf001", True, COLOR_TEXT)
    ICON_PLAYLIST = FONT_ICON.render("\uf03a", True, COLOR_TEXT)
    ICON_FOLDER = FONT_ICON.render("\uf07b", True, COLOR_TEXT)
    ICON_ELIPSIS = FONT_ICON.render("\uf141", True, COLOR_TEXT)
    ICON_SONG = FONT_ICON.render("\uf101", True, COLOR_TEXT)
    ICON_CURRENT = FONT_ICON.render("\uf0da", True, COLOR_TEXT)
    ICON_PLAY = FONT_ICON.render("\uf04b", True, COLOR_TEXT)
    ICON_PAUSE = FONT_ICON.render("\uf04c", True, COLOR_TEXT)
    ICON_SHUTDOWN = FONT_ICON.render("\uf011", True, COLOR_TEXT)
    ICON_UP = FONT_ICON.render("\uf077", True, COLOR_TEXT)
    ICON_DOWN = FONT_ICON.render("\uf078", True, COLOR_TEXT)


# classes for buttons
class Button:
    def create_button(self, item, surface, x, y, width, height, title, subtitle, icon):
        # draw the button surface and outline
        surface = self.draw_button(surface, width, height, x, y)
        # draw the text and/or icon
        surface = self.draw_contents(surface, title, subtitle, icon, width, height, x, y)
        # store the rect of the button
        self.rect = pygame.Rect(x,y, width, height)
        # store text
        self.title = title
        # store item
        self.item = item
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
class Audio(FileSystemEventHandler):
    def __init__(self):
        self.init()
        self.main()

    def init(self):
        # hide mouse
        pygame.mouse.set_visible(False)

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

        self.playlist_items = []
        self.songs = []

        self.playlist_path = Settings.PATH_PLAYLISTS
        
        self.playlist_page = 1
        self.playing_page = 1

        self.playing_rect = None

        self.current_song = None
        
        self.shutdown = Button()
        self.page_up = Button()
        self.page_down = Button()
        self.playlist_buttons = []

        self.playing_play = Button()
        self.playing_playlist = Button()
        self.playing_buttons = []

        self.player = None

    # reload playlists on filesystem change
    def on_any_event(self, event):
        self.load_playlist_items(self.playlist_path)

    # check if song position is clicked
    def song_position_clicked(self, mouse):
        if mouse[0] > self.playing_rect.topleft[0]:
            if mouse[1] > self.playing_rect.topleft[1]:
                if mouse[0] < self.playing_rect.bottomright[0]:
                    if mouse[1] < self.playing_rect.bottomright[1]:
                        return True
                    else: return False
                else: return False
            else: return False
        else: return False

    # set new song position
    def set_song_position(self, mouse):
        duration = self.player.duration()
        relative_position = (mouse[0] - self.playing_rect.topleft[0]) / (self.playing_rect.width)
        self.player.set_position(relative_position * duration)

    # function for drawing playlist
    def draw_playlist(self):
        # draw playlist header
        playlist_header_text = Settings.FONT_HEADER.render("Select Playlist", True, Settings.COLOR_TEXT)
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(-1, -1, Settings.SIZE_SCREEN[0]+2, Settings.CONTROL_HEIGHT+2), 1)

        self.screen.blit(playlist_header_text, ((Settings.SIZE_SCREEN[0]/2)-(playlist_header_text.get_width()/2)+((Settings.ICON_MUSIC.get_width()+Settings.SEPARATOR)/2),(Settings.CONTROL_HEIGHT/2)-(playlist_header_text.get_height()/2)))
        self.screen.blit(Settings.ICON_MUSIC, ((Settings.SIZE_SCREEN[0]/2)-((playlist_header_text.get_width()+Settings.ICON_MUSIC.get_width()+Settings.SEPARATOR)/2),(Settings.CONTROL_HEIGHT/2)-(Settings.ICON_MUSIC.get_height()/2)))

        # shutdown button
        if self.playlist_path == Settings.PATH_PLAYLISTS:
            self.shutdown.create_button('SHUTDOWN', self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), 0, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_SHUTDOWN)

        # clear existing the playlist buttons
        self.playlist_buttons.clear()

        count = 1
        # create a button to go one directory up
        if self.playlist_page == 1:
            if self.playlist_path != Settings.PATH_PLAYLISTS:
                button = Button()
                button.create_button('UP', self.screen, 0, count * Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_ELIPSIS)
                self.playlist_buttons.append(button)
                count += 1

        for item in range(((self.playlist_page - 1) * Settings.ITEMS)-(self.playlist_page > 1 if 1 else 0), min(((self.playlist_page - 1) * Settings.ITEMS) + (Settings.ITEMS - (self.playlist_page == 1 if 1 else 0)), len(self.playlist_items))):
            button = Button()
            
            if self.playlist_items[item][1] == Settings.BUTTON_TYPE_CATEGORY:
                icon = Settings.ICON_FOLDER
                title = self.playlist_items[item][0]
            elif self.playlist_items[item][1] == Settings.BUTTON_TYPE_PLAYLIST:
                icon = Settings.ICON_PLAYLIST
                title = os.path.splitext(self.playlist_items[item][0])[0]

            button.create_button(self.playlist_items[item], self.screen, 0, count * Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+1, title, None, icon)
            self.playlist_buttons.append(button)
            count += 1

        # page controls
        pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+1), Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+2), 1)
    
        numpages = math.ceil((len(self.playlist_items)+1)/Settings.ITEMS)
        indicator_height = int((Settings.CONTROL_HEIGHT * (Settings.ITEMS-2)) / numpages)
        pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, Rect(Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT*2+indicator_height*(self.playlist_page-1), Settings.CONTROL_HEIGHT, indicator_height), 0)

        # page up/down buttons
        self.page_up.create_button((), self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_UP)
        self.page_down.create_button((), self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_DOWN)
    
    
    # draw songs of a playlist
    def draw_player(self):
        try:
            # return to playlist button
            self.playing_playlist.create_button('PLAYLIST', self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_PLAYLIST)

             # page controls
            pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+1), -1, Settings.CONTROL_HEIGHT+2, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+2), 1)
    
            numpages = math.ceil(len(self.songs)/Settings.ITEMS)
            indicator_height = int((Settings.CONTROL_HEIGHT * (Settings.ITEMS-2)) / numpages)
            pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, Rect(Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+indicator_height*(self.playing_page-1), Settings.CONTROL_HEIGHT, indicator_height), 0)

            # page up/down buttons
            self.page_up.create_button('UP', self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), 0, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_UP)
            self.page_down.create_button('DOWN', self.screen, Settings.SIZE_SCREEN[0] - (Settings.CONTROL_HEIGHT+1), Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT*2, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, Settings.ICON_DOWN)
    
             # clear existing the song buttons
            self.playing_buttons.clear()

            count = 0
            for item in range((self.playing_page - 1) * Settings.ITEMS, min(((self.playing_page - 1) * Settings.ITEMS) + Settings.ITEMS, len(self.songs))):
                # get meta data from song
                audio = MP3(os.path.join(Settings.PATH_MUSIC, self.songs[item][0]))
                time = audio.info.length
                        
                # format subtitle as mm:ss
                minutes = math.floor(int(time) / 60)
                seconds = int(time) - (minutes * 60)
                subtitle = "{:0>2d}:{:0>2d}".format(minutes, seconds)

                title = os.path.splitext(os.path.basename(self.songs[item][0]))[0]

                # check if this is the current song
                if self.current_song[1] == self.songs[item][1]:
                    icon = Settings.ICON_CURRENT
                else:
                    icon = Settings.ICON_SONG

                button = Button()
                button.create_button(self.songs[item], self.screen, 0, count * Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+1, title, subtitle, icon)
                self.playing_buttons.append(button)
                count += 1

            # draw the play controls
            pygame.draw.rect(self.screen, Settings.COLOR_LINE, Rect(-1, Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT, Settings.SIZE_SCREEN[0]+2, Settings.CONTROL_HEIGHT+2), 1)

            # play/pause button
            if self.player.is_playing():
                icon = Settings.ICON_PAUSE
            else:
                icon = Settings.ICON_PLAY

            self.playing_play.create_button('PLAY', self.screen, 0, Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT, Settings.CONTROL_HEIGHT+2, Settings.CONTROL_HEIGHT+1, None, None, icon)

             # get elapsed time in seconds
            elapsed_time = self.player.position()
            if elapsed_time < 0:
                elapsed_time = 0
    
            # format subtitle as mm:ss
            minutes = math.floor(elapsed_time / 60)
            seconds = elapsed_time - (minutes * 60)
            elapsed = Settings.FONT_MAIN.render("{:02.0f}:{:02.0f}".format(minutes, seconds), True, Settings.COLOR_TEXT)

            self.screen.blit(elapsed, (Settings.CONTROL_HEIGHT+Settings.SEPARATOR,(Settings.SIZE_SCREEN[1] - Settings.CONTROL_HEIGHT)+(Settings.CONTROL_HEIGHT/2-elapsed.get_height()/2)))

             # get length in seconds
            length_time = self.player.duration()
    
            # format subtitle as mm:ss
            minutes = math.floor(length_time / 60)
            seconds = length_time - (minutes * 60)
            length = Settings.FONT_MAIN.render("{:02.0f}:{:02.0f}".format(minutes, seconds), True, Settings.COLOR_TEXT)

            self.screen.blit(length, (Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+Settings.SEPARATOR+length.get_width()),(Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT)+(Settings.CONTROL_HEIGHT/2-length.get_height()/2)))

            # set the playing rect
            width = Settings.SIZE_SCREEN[0]-(Settings.CONTROL_HEIGHT+Settings.SEPARATOR+elapsed.get_width()+Settings.SEPARATOR+Settings.SEPARATOR+length.get_width()+Settings.SEPARATOR+Settings.CONTROL_HEIGHT)
            self.playing_rect = Rect((Settings.CONTROL_HEIGHT+Settings.SEPARATOR+elapsed.get_width()+Settings.SEPARATOR), (Settings.SIZE_SCREEN[1]-Settings.CONTROL_HEIGHT+Settings.SEPARATOR),width,Settings.CONTROL_HEIGHT-2*Settings.SEPARATOR)
            pygame.draw.rect(self.screen, Settings.COLOR_LIGHT, self.playing_rect, 0)
    
            elapsed_rect = self.playing_rect.inflate(-((1-(elapsed_time/length_time))*width),0).move(-((1-(elapsed_time/length_time))*width)/2,0)
            pygame.draw.rect(self.screen, Settings.COLOR_HIGHLIGHT, elapsed_rect, 0)
        
        except:
            # find next song
            item = 0
            for song in self.songs:
                item += 1
                
                if song[1] == self.current_song[1]:
                    if item == len(self.songs):
                        item = 0
                    
                    self.current_song = self.songs[item]
                    self.player = OMXPlayer(os.path.join(Settings.PATH_MUSIC, self.current_song[0]),['--no-osd'])

                    self.playing_page = math.ceil((item + 1) / Settings.ITEMS)

                    break


    def load_playlist_items(self, path):
        self.playlist_items.clear()
        self.playlist_path = path

        # get all items in path
        items =  os.listdir(path)
        items.sort()

        # load all directories as categories
        for item in items:
            dir = os.path.join(path, item)
            if os.path.isdir(dir):
                self.playlist_items.append((item, Settings.BUTTON_TYPE_CATEGORY))

        # load all *.m3u files as playlists
        for item in items:
            if item.endswith('.m3u'):
                self.playlist_items.append((item, Settings.BUTTON_TYPE_PLAYLIST))
    
    def load_songs(self, playlist):
        self.songs.clear()

        count = 0
        with open(playlist) as file:
            for song in file:
                self.songs.append((song.rstrip(), count, Settings.BUTTON_TYPE_SONG))
                count += 1

        self.current_song = self.songs[0]
        self.player = OMXPlayer(os.path.join(Settings.PATH_MUSIC, self.current_song[0]),['--no-osd'])

    def main(self):
        self.status = Settings.STATUS_PLAYLIST
        
        # load the first level of playlist items (either categories or actual playlists)
        self.load_playlist_items(Settings.PATH_PLAYLISTS)

        # setup watchdog to watch for filesystem changes
        observer = Observer()
        observer.schedule(self, Settings.PATH_PLAYLISTS, recursive=True)
        observer.start()

        # enter loop for drawing the AUDIO gui
        while True:
            # check for events.
            for event in pygame.event.get():
                if event.type == QUIT:
                    # close omxplayer
                    if self.player:
                        self.player.quit()
                    # exit the AUDIO gui
                    observer.stop()
                    pygame.quit()
                    exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if self.status == Settings.STATUS_PLAYLIST:
                        if self.page_up.clicked(pygame.mouse.get_pos()):
                            if self.playlist_page > 1:
                                self.playlist_page -= 1
                        elif self.page_down.clicked(pygame.mouse.get_pos()):
                            if self.playlist_page < math.ceil(len(self.playlist_items)/(Settings.ITEMS-(self.playlist_page > 1 if 0 else 1))):
                                self.playlist_page += 1
                        elif self.shutdown.clicked(pygame.mouse.get_pos()):
                            # close omxplayer
                            if self.player:
                                self.player.quit()
                            # exit the AUDIO gui
                            observer.stop()
                            pygame.quit()

                            # Shutdown
                            os.system('shutdown now -h')
                        else:
                            for btn in self.playlist_buttons:
                                if btn.clicked(pygame.mouse.get_pos()):
                                    # category up
                                    if btn.item == 'UP':
                                        self.load_playlist_items(os.path.dirname(self.playlist_path))
                                    # category down
                                    elif btn.item[1] == Settings.BUTTON_TYPE_CATEGORY:
                                        self.load_playlist_items(os.path.join(self.playlist_path,btn.item[0]))
                                    # open playlist
                                    elif btn.item[1] == Settings.BUTTON_TYPE_PLAYLIST:
                                        self.load_songs(os.path.join(self.playlist_path,btn.item[0]))
                                        # set the status
                                        self.status = Settings.STATUS_PLAYING

                    elif self.status == Settings.STATUS_PLAYING:
                        if self.page_up.clicked(pygame.mouse.get_pos()):
                            if self.playing_page > 1:
                                self.playing_page -= 1
                        elif self.page_down.clicked(pygame.mouse.get_pos()):
                            test = math.ceil(len(self.songs)/Settings.ITEMS)
                            if self.playing_page < math.ceil(len(self.songs)/Settings.ITEMS):
                                self.playing_page += 1
                        elif self.song_position_clicked(pygame.mouse.get_pos()):
                            self.set_song_position(pygame.mouse.get_pos())
                        elif self.playing_playlist.clicked(pygame.mouse.get_pos()):
                            self.player.quit()
                            self.playing_page = 1
                            self.status = Settings.STATUS_PLAYLIST
                        elif self.playing_play.clicked(pygame.mouse.get_pos()):
                            if self.player.is_playing():
                                self.player.pause()
                            else:
                                self.player.play()

                            # move to the page that has this song on it
                            self.playing_page = math.ceil((self.current_song[1]+1)/Settings.ITEMS)
                        else:
                            item = 0
                            for btn in self.playing_buttons:
                                if btn.clicked(pygame.mouse.get_pos()):
                                    # close omxplayer
                                    if self.player:
                                        self.player.quit()
                                    # select the song
                                    self.current_song = self.songs[(self.playing_page-1)*Settings.ITEMS+item]
                                    self.player = OMXPlayer(os.path.join(Settings.PATH_MUSIC, self.current_song[0]),['--no-osd'])
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
            sleep(0.1)



if __name__ == '__main__':
    obj = Audio()