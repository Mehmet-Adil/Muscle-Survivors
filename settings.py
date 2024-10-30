import pygame
from os.path import join as path_join

WINDOW_LOGO = pygame.image.load(path_join("Images", "Muscle Survivors Logo.png"))
WINDOW_SIZE = (0, 0)
WINDOW_CAPTION = "Muscle Survivors"
FPS = 60

game_state = "SIGN IN"
SCREEN = pygame.Surface((0, 0))

user = None
user_password = None
