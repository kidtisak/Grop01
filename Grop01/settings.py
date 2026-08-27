import pygame

# Screen settings
WIDTH = 800
HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
LANE_COLORS = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA]

# Gameplay settings
KEYS = [pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k, pygame.K_l]
KEY_NAMES = ['S', 'D', 'F', 'J', 'K', 'L']
NUM_LANES = 6
LANE_WIDTH = 80
LANE_START_X = (WIDTH - (NUM_LANES * LANE_WIDTH)) // 2

# Note settings
NOTE_HEIGHT = 20
NOTE_SPEED = 5 # pixels per frame
HIT_Y = HEIGHT - 100 # The Y position where the notes should be hit

# Timing and scoring windows (in pixels for simplicity, based on distance from HIT_Y)
PERFECT_WINDOW = 20
GREAT_WINDOW = 45
GOOD_WINDOW = 70
MISS_WINDOW = 100
