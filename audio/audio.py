import pygame
from pygame.locals import *
from sys import exit

pygame.init()

screen = pygame.display.set_mode((320, 240), 0, 32)
#screen = pygame.display.set_mode((1920, 1080), FULLSCREEN, 32)
pygame.display.set_caption("Audio")

background = pygame.surface.Surface((320, 240))
pygame.draw.rect(background, (51, 51, 51), Rect(0, 0, 320, 240))

font_main = pygame.font.Font("resources/OpenSans-Light.ttf", 40);
text = font_main.render("AUDIO", True, (255, 255, 255))

while True:

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()

        screen.blit(background, (0,0))
        screen.blit(text, ((320/2)-(text.get_width()/2),(240/2)-(text.get_height()/2)))

        pygame.display.update()
