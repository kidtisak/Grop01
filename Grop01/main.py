import pygame
import sys
import os
import shutil
import tkinter as tk
from tkinter import filedialog
from settings import *
from game import Game
from editor import Editor

pygame.init()
pygame.display.set_caption("Python Rhythm Game")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)
    return textrect

def add_new_song(maps_dir):
    # Setup Tkinter to hide main window and only show file dialog
    root = tk.Tk()
    root.withdraw()
    
    # Open File Dialog
    file_path = filedialog.askopenfilename(
        title="Select Audio File for New Song",
        filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")]
    )
    
    root.destroy()
    
    if file_path:
        # Get filename and song name (without extension)
        filename = os.path.basename(file_path)
        song_name, ext = os.path.splitext(filename)
        
        # Create a unique folder for the song
        new_folder = os.path.join(maps_dir, song_name)
        counter = 1
        while os.path.exists(new_folder):
            new_folder = os.path.join(maps_dir, f"{song_name}_{counter}")
            counter += 1
            
        os.makedirs(new_folder)
        
        # Copy audio file to the new folder
        dest_audio = os.path.join(new_folder, filename)
        shutil.copy(file_path, dest_audio)
        
        # Create basic map.json
        map_json_path = os.path.join(new_folder, "map.json")
        with open(map_json_path, 'w') as f:
            f.write(f'{{\n  "audio": "{filename}",\n  "notes": []\n}}')
            
        return True
    return False

def select_song_menu():
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)
    
    maps_dir = "maps"
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)
        
    def get_folders():
        return [f for f in os.listdir(maps_dir) if os.path.isdir(os.path.join(maps_dir, f))]
        
    folders = get_folders()
    
    while True:
        screen.fill(BLACK)
        draw_text('Select a Song', font, WHITE, screen, WIDTH // 2, 50)
        
        y_offset = 150
        rects = []
        for i, folder in enumerate(folders):
            rect = draw_text(f"{i+1}. {folder}", small_font, LIGHT_GRAY, screen, WIDTH // 2, y_offset)
            rects.append((rect, folder))
            y_offset += 50
            
        # Add new song button
        add_rect = draw_text('[+] Add New Song (Press A)', small_font, GREEN, screen, WIDTH // 2, y_offset + 50)
        cancel_rect = draw_text('Press ESC to Cancel', small_font, GRAY, screen, WIDTH // 2, HEIGHT - 50)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if add_rect.collidepoint(event.pos):
                    if add_new_song(maps_dir):
                        folders = get_folders() # Refresh list
                for rect, folder in rects:
                    if rect.collidepoint(event.pos):
                        return os.path.join(maps_dir, folder)
                        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_a:
                    if add_new_song(maps_dir):
                        folders = get_folders() # Refresh list
                # Check number keys
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(folders):
                        return os.path.join(maps_dir, folders[idx])
                        
        pygame.display.flip()
        clock.tick(FPS)

def main_menu():
    font = pygame.font.SysFont(None, 64)
    small_font = pygame.font.SysFont(None, 36)
    
    while True:
        screen.fill(BLACK)
        
        draw_text('Python Rhythm Game', font, WHITE, screen, WIDTH // 2, HEIGHT // 4)
        
        play_rect = draw_text('1. Play Game', small_font, LIGHT_GRAY, screen, WIDTH // 2, HEIGHT // 2)
        editor_rect = draw_text('2. Map Editor', small_font, LIGHT_GRAY, screen, WIDTH // 2, HEIGHT // 2 + 50)
        quit_rect = draw_text('3. Quit', small_font, LIGHT_GRAY, screen, WIDTH // 2, HEIGHT // 2 + 100)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    return 'game'
                if editor_rect.collidepoint(event.pos):
                    return 'editor'
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'game'
                if event.key == pygame.K_2:
                    return 'editor'
                if event.key == pygame.K_3 or event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
        pygame.display.flip()
        clock.tick(FPS)

def main():
    while True:
        choice = main_menu()
        
        if choice in ('game', 'editor'):
            map_folder = select_song_menu()
            if map_folder:
                if choice == 'game':
                    game = Game(screen, map_folder)
                    game.run()
                elif choice == 'editor':
                    editor = Editor(screen, map_folder)
                    editor.run()

if __name__ == "__main__":
    main()
    pygame.quit()
