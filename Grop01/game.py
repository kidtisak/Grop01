import pygame
import json
import os
from settings import *

class Note:
    def __init__(self, type, time, lane, duration=0):
        self.type = type # 'tap' or 'hold'
        self.time = time
        self.lane = lane
        self.duration = duration
        self.hit = False
        self.missed = False
        self.holding = False
        self.released = False

class Game:
    def __init__(self, screen, map_folder):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.notes = []
        self.map_folder = map_folder
        self.audio_path = None
        
        self.start_time = 0
        self.raw_score = 0
        self.combo = 0
        self.max_combo = 0
        
        self.stats = {
            "PERFECT": 0,
            "GREAT": 0,
            "GOOD": 0,
            "MISS": 0
        }
        
        self.font = pygame.font.SysFont(None, 36)
        self.large_font = pygame.font.SysFont(None, 72)
        
        self.speed_px_per_ms = 0.5
        
        self.feedback = ""
        self.feedback_time = 0
        self.feedback_color = WHITE
        
        self.has_music = False
        self.music_started = False
        
        self.state = 'PLAYING' # 'PLAYING' or 'RESULTS'
        
        self.load_map(os.path.join(map_folder, "map.json"))
        
        # Calculate max possible raw score
        # Tap = 300
        # Hold = 300 (head) + 300 (tail) = 600
        self.max_raw_score = sum(600 if n.type == 'hold' else 300 for n in self.notes)
        if self.max_raw_score == 0:
            self.max_raw_score = 1 # Prevent division by zero

    def get_display_score(self):
        return int((self.raw_score / self.max_raw_score) * 100000)

    def load_map(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
                if 'audio' in data and data['audio']:
                    audio_file = os.path.join(self.map_folder, data['audio'])
                    if os.path.exists(audio_file):
                        self.audio_path = audio_file
                        pygame.mixer.music.load(self.audio_path)
                        self.has_music = True
                        
                for n in data['notes']:
                    ntype = n.get('type', 'tap')
                    time = n['time']
                    lane = n['lane']
                    duration = n.get('duration', 0)
                    self.notes.append(Note(ntype, time, lane, duration))
                    
                self.notes.sort(key=lambda n: n.time)
        except Exception as e:
            print(f"Failed to load map: {e}")
            self.notes = []

    def get_time(self):
        if self.has_music and self.music_started:
            pos = pygame.mixer.music.get_pos()
            if pos != -1:
                return pos
            return pygame.time.get_ticks() - self.start_time
        else:
            return pygame.time.get_ticks() - self.start_time

    def run(self):
        self.start_time = pygame.time.get_ticks() + 1000 # Delay
        running = True
        
        while running:
            current_time = pygame.time.get_ticks()
            
            if self.state == 'PLAYING':
                # Start music after delay
                if current_time >= self.start_time and not self.music_started:
                    self.start_time = current_time
                    if self.has_music:
                        pygame.mixer.music.play()
                    self.music_started = True
                
                elapsed_time = self.get_time() if self.music_started else (current_time - self.start_time)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        if self.has_music:
                            pygame.mixer.music.stop()
                        return False
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.has_music:
                                pygame.mixer.music.stop()
                            return True
                        for i, key in enumerate(KEYS):
                            if event.key == key:
                                self.handle_keydown(i, elapsed_time)
                                
                    if event.type == pygame.KEYUP:
                        for i, key in enumerate(KEYS):
                            if event.key == key:
                                self.handle_keyup(i, elapsed_time)
                                
                self.update(elapsed_time)
                self.draw_playing(elapsed_time)
                
            elif self.state == 'RESULTS':
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                            return True
                self.draw_results()
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
        return True

    def update_combo(self):
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo

    def handle_keydown(self, lane, current_time):
        perfect_ms = PERFECT_WINDOW / self.speed_px_per_ms
        great_ms = GREAT_WINDOW / self.speed_px_per_ms
        good_ms = GOOD_WINDOW / self.speed_px_per_ms
        miss_ms = MISS_WINDOW / self.speed_px_per_ms

        for note in self.notes:
            if note.lane == lane and not note.hit and not note.missed:
                time_diff = abs(note.time - current_time)
                
                if time_diff <= miss_ms:
                    if time_diff <= perfect_ms:
                        self.register_hit(note, "PERFECT", CYAN, 300)
                    elif time_diff <= great_ms:
                        self.register_hit(note, "GREAT", GREEN, 100)
                    elif time_diff <= good_ms:
                        self.register_hit(note, "GOOD", YELLOW, 50)
                    else:
                        self.register_miss(note)
                    return

    def register_hit(self, note, text, color, score):
        note.hit = True
        self.raw_score += score
        self.stats[text] += 1
        
        if note.type == 'hold':
            note.holding = True
        else:
            self.update_combo()
            
        self.set_feedback(text, color)

    def register_miss(self, note):
        note.missed = True
        note.holding = False
        self.combo = 0
        self.stats["MISS"] += 1
        self.set_feedback("MISS", RED)

    def handle_keyup(self, lane, current_time):
        miss_ms = MISS_WINDOW / self.speed_px_per_ms
        
        for note in self.notes:
            if note.lane == lane and note.holding and not note.released:
                note.holding = False
                end_time = note.time + note.duration
                time_diff = abs(end_time - current_time)
                
                if time_diff <= miss_ms:
                    note.released = True
                    self.update_combo()
                    self.raw_score += 300 # Add score for completing hold
                    self.set_feedback("PERFECT", CYAN)
                else:
                    self.register_miss(note)
                return

    def set_feedback(self, text, color):
        self.feedback = text
        self.feedback_color = color
        self.feedback_time = pygame.time.get_ticks()

    def update(self, elapsed_time):
        miss_ms = MISS_WINDOW / self.speed_px_per_ms
        all_done = True
        
        for note in self.notes:
            # Check misses
            if not note.hit and not note.missed:
                if elapsed_time - note.time > miss_ms:
                    self.register_miss(note)
            
            if note.type == 'hold' and note.holding:
                if elapsed_time - (note.time + note.duration) > miss_ms:
                    self.register_miss(note)
                    
            # Check if finished
            if note.type == 'tap':
                if not (note.hit or note.missed):
                    all_done = False
            elif note.type == 'hold':
                if not (note.released or note.missed):
                    all_done = False
                    
        # Change state if all notes are processed and a little time has passed
        if all_done and len(self.notes) > 0:
            last_time = max((n.time + n.duration) for n in self.notes)
            if elapsed_time > last_time + 1500: # Wait 1.5s after last note
                self.state = 'RESULTS'

    def draw_playing(self, elapsed_time):
        self.screen.fill(BLACK)
        
        for i in range(NUM_LANES):
            x = LANE_START_X + i * LANE_WIDTH
            pygame.draw.rect(self.screen, GRAY, (x, 0, LANE_WIDTH, HEIGHT), 1)
            key_text = self.font.render(KEY_NAMES[i], True, LIGHT_GRAY)
            self.screen.blit(key_text, (x + LANE_WIDTH//2 - key_text.get_width()//2, HIT_Y + 30))
            
        pygame.draw.line(self.screen, WHITE, (LANE_START_X, HIT_Y), (LANE_START_X + NUM_LANES * LANE_WIDTH, HIT_Y), 3)
        
        for note in reversed(self.notes): # Draw hold tails first
            if not note.missed and not (note.type == 'tap' and note.hit) and not (note.type == 'hold' and note.released):
                x = LANE_START_X + note.lane * LANE_WIDTH
                color = LANE_COLORS[note.lane]
                
                y = HIT_Y - (note.time - elapsed_time) * self.speed_px_per_ms
                
                if note.type == 'tap':
                    if -100 < y < HEIGHT + 100:
                        pygame.draw.rect(self.screen, color, (x + 5, y - NOTE_HEIGHT//2, LANE_WIDTH - 10, NOTE_HEIGHT))
                elif note.type == 'hold':
                    end_y = HIT_Y - (note.time + note.duration - elapsed_time) * self.speed_px_per_ms
                    
                    if note.holding:
                        y = HIT_Y
                        
                    if end_y < HEIGHT and y > 0:
                        body_color = tuple(max(0, c - 100) for c in color)
                        pygame.draw.rect(self.screen, body_color, (x + 10, end_y, LANE_WIDTH - 20, y - end_y))
                        pygame.draw.rect(self.screen, color, (x + 5, end_y - NOTE_HEIGHT//2, LANE_WIDTH - 10, NOTE_HEIGHT))
                        if not note.holding:
                            pygame.draw.rect(self.screen, color, (x + 5, y - NOTE_HEIGHT//2, LANE_WIDTH - 10, NOTE_HEIGHT))
                            
        # Draw Score scaled to 100,000
        score_text = self.font.render(f"Score: {self.get_display_score():06d}", True, WHITE)
        combo_text = self.font.render(f"Combo: {self.combo}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(combo_text, (10, 50))
        
        if pygame.time.get_ticks() - self.feedback_time < 500:
            feedback_text = self.large_font.render(self.feedback, True, self.feedback_color)
            fw = feedback_text.get_width()
            self.screen.blit(feedback_text, (WIDTH//2 - fw//2, HEIGHT//2 - 100))
            
        inst_text = self.font.render("Press ESC to exit", True, LIGHT_GRAY)
        self.screen.blit(inst_text, (WIDTH - 200, 10))

    def draw_results(self):
        self.screen.fill((20, 20, 40))
        
        title = self.large_font.render("SONG CLEARED", True, YELLOW)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
        
        score_txt = self.large_font.render(f"Score: {self.get_display_score():06d}", True, WHITE)
        self.screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 160))
        
        # Stats
        y_offset = 260
        stats_labels = [
            ("PERFECT", CYAN, self.stats["PERFECT"]),
            ("GREAT", GREEN, self.stats["GREAT"]),
            ("GOOD", YELLOW, self.stats["GOOD"]),
            ("MISS", RED, self.stats["MISS"]),
            ("MAX COMBO", WHITE, self.max_combo)
        ]
        
        for label, color, value in stats_labels:
            txt = self.font.render(f"{label}: {value}", True, color)
            self.screen.blit(txt, (WIDTH//2 - 100, y_offset))
            y_offset += 40
            
        inst = self.font.render("Press ESC or ENTER to return to menu", True, LIGHT_GRAY)
        self.screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 80))
