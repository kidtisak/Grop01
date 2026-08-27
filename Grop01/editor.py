import pygame
import json
import os
from settings import *

class Editor:
    def __init__(self, screen, map_folder):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.map_folder = map_folder
        self.map_file = os.path.join(map_folder, "map.json")
        self.audio_file = ""
        self.audio_path = None
        
        self.notes = [] # list of dicts: {'type': str, 'time': ms, 'lane': int, 'duration': ms}
        self.font = pygame.font.SysFont(None, 24)
        
        self.scroll_time = 0
        self.speed_px_per_ms = 0.5
        
        self.drag_start = None # (time, lane)
        
        self.is_playing = False
        self.play_start_time = 0
        self.scroll_at_play_start = 0
        
        self.load_map()

    def load_map(self):
        try:
            with open(self.map_file, 'r') as f:
                data = json.load(f)
                self.audio_file = data.get('audio', '')
                self.notes = data.get('notes', [])
                
                if self.audio_file:
                    audio_full_path = os.path.join(self.map_folder, self.audio_file)
                    if os.path.exists(audio_full_path):
                        self.audio_path = audio_full_path
                        pygame.mixer.music.load(self.audio_path)
        except Exception as e:
            print(f"Error loading map: {e}")
            self.notes = []

    def save_map(self):
        self.notes.sort(key=lambda n: n['time'])
        with open(self.map_file, 'w') as f:
            json.dump({'audio': self.audio_file, 'notes': self.notes}, f, indent=2)

    def toggle_playback(self):
        if not self.audio_path:
            return
            
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
        else:
            try:
                # play(loops, start_time_in_seconds)
                pygame.mixer.music.play(0, start=self.scroll_time / 1000.0)
                self.is_playing = True
                self.scroll_at_play_start = self.scroll_time
            except Exception as e:
                print(f"Error playing audio: {e}")

    def run(self):
        running = True
        
        while running:
            # Update scroll time if playing
            if self.is_playing:
                current_pos = pygame.mixer.music.get_pos()
                if current_pos == -1: # Music ended
                    self.is_playing = False
                else:
                    self.scroll_time = self.scroll_at_play_start + current_pos
                    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.is_playing:
                        pygame.mixer.music.stop()
                    return False
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.is_playing:
                            pygame.mixer.music.stop()
                        self.save_map()
                        return True
                        
                    elif event.key == pygame.K_SPACE:
                        self.toggle_playback()
                        
                    elif event.key == pygame.K_UP and not self.is_playing:
                        self.scroll_time += 1000
                    elif event.key == pygame.K_DOWN and not self.is_playing:
                        self.scroll_time = max(0, self.scroll_time - 1000)
                        
                    elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.save_map()
                        
                    # Live mapping using gameplay keys
                    elif self.is_playing:
                        for i, key in enumerate(KEYS):
                            if event.key == key:
                                # Snap to nearest 10ms instead of 50ms for live tapping precision
                                snap_time = round(self.scroll_time / 10) * 10
                                self.notes.append({'type': 'tap', 'time': snap_time, 'lane': i})
                        
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.is_playing:
                    if event.button == 1: # Left click
                        self.handle_mousedown(event.pos)
                    elif event.button == 4: # Scroll up
                        self.scroll_time += 100
                    elif event.button == 5: # Scroll down
                        self.scroll_time = max(0, self.scroll_time - 100)
                
                elif event.type == pygame.MOUSEBUTTONUP and not self.is_playing:
                    if event.button == 1: # Left release
                        self.handle_mouseup(event.pos)
                        
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
            
        return True

    def get_time_and_lane(self, pos):
        x, y = pos
        if LANE_START_X <= x <= LANE_START_X + NUM_LANES * LANE_WIDTH:
            lane = (x - LANE_START_X) // LANE_WIDTH
            time_clicked = self.scroll_time + (HIT_Y - y) / self.speed_px_per_ms
            time_snapped = round(time_clicked / 50) * 50
            return max(0, time_snapped), lane
        return None, None

    def handle_mousedown(self, pos):
        time, lane = self.get_time_and_lane(pos)
        if time is not None:
            for note in self.notes:
                start = note['time']
                end = start + note.get('duration', 0)
                if note['lane'] == lane and start - 50 <= time <= end + 50:
                    self.notes.remove(note)
                    return 
            self.drag_start = (time, lane)

    def handle_mouseup(self, pos):
        if self.drag_start:
            start_time, lane = self.drag_start
            end_time, end_lane = self.get_time_and_lane(pos)
            
            if end_time is not None and lane == end_lane:
                duration = abs(end_time - start_time)
                real_start = min(start_time, end_time)
                
                if duration > 100:
                    self.notes.append({'type': 'hold', 'time': real_start, 'lane': lane, 'duration': duration})
                else:
                    self.notes.append({'type': 'tap', 'time': real_start, 'lane': lane})
                    
            self.drag_start = None

    def draw(self):
        self.screen.fill((20, 20, 40))
        
        for i in range(NUM_LANES):
            x = LANE_START_X + i * LANE_WIDTH
            pygame.draw.rect(self.screen, GRAY, (x, 0, LANE_WIDTH, HEIGHT), 1)
            
        pygame.draw.line(self.screen, YELLOW, (LANE_START_X, HIT_Y), (LANE_START_X + NUM_LANES * LANE_WIDTH, HIT_Y), 2)
        
        for note in self.notes:
            time = note['time']
            lane = note['lane']
            duration = note.get('duration', 0)
            
            y_start = HIT_Y - (time - self.scroll_time) * self.speed_px_per_ms
            y_end = HIT_Y - (time + duration - self.scroll_time) * self.speed_px_per_ms
            
            x = LANE_START_X + lane * LANE_WIDTH
            color = LANE_COLORS[lane]
            
            if note.get('type') == 'hold':
                body_color = tuple(max(0, c - 100) for c in color)
                pygame.draw.rect(self.screen, body_color, (x + 10, y_end, LANE_WIDTH - 20, y_start - y_end))
                pygame.draw.rect(self.screen, color, (x + 5, y_end - NOTE_HEIGHT//2, LANE_WIDTH - 10, NOTE_HEIGHT))
            
            pygame.draw.rect(self.screen, color, (x + 5, y_start - NOTE_HEIGHT//2, LANE_WIDTH - 10, NOTE_HEIGHT))
            
        if self.drag_start:
            start_time, lane = self.drag_start
            pos = pygame.mouse.get_pos()
            end_time, end_lane = self.get_time_and_lane(pos)
            
            if end_time is not None and lane == end_lane:
                real_start = min(start_time, end_time)
                real_end = max(start_time, end_time)
                
                y_start = HIT_Y - (real_start - self.scroll_time) * self.speed_px_per_ms
                y_end = HIT_Y - (real_end - self.scroll_time) * self.speed_px_per_ms
                
                x = LANE_START_X + lane * LANE_WIDTH
                pygame.draw.rect(self.screen, (100, 100, 100), (x + 10, y_end, LANE_WIDTH - 20, y_start - y_end))

        start_time = max(0, self.scroll_time - HIT_Y / self.speed_px_per_ms)
        end_time = self.scroll_time + (HEIGHT - HIT_Y) / self.speed_px_per_ms
        for t in range(int(start_time // 1000) * 1000, int(end_time) + 1000, 1000):
            y = HIT_Y - (t - self.scroll_time) * self.speed_px_per_ms
            if 0 <= y <= HEIGHT:
                pygame.draw.line(self.screen, (100, 100, 150), (LANE_START_X, y), (LANE_START_X + NUM_LANES * LANE_WIDTH, y), 1)
                t_text = self.font.render(f"{t}ms", True, (150, 150, 200))
                self.screen.blit(t_text, (LANE_START_X - 60, y - 10))

        status_text = "PLAYING" if self.is_playing else "PAUSED"
        color_status = GREEN if self.is_playing else RED

        instructions = [
            f"Status: {status_text} (Time: {int(self.scroll_time)} ms)",
            "SPACE: Play / Pause Audio",
            "When Paused: Click to Add/Remove Notes, Scroll to move",
            "When Playing: Press S,D,F,J,K,L to tap map live!",
            "CTRL+S: Save Map | ESC: Exit"
        ]
        
        # Highlight status
        inst_text = self.font.render(instructions[0], True, color_status)
        self.screen.blit(inst_text, (10, 10))
        
        for i, text in enumerate(instructions[1:]):
            inst_text = self.font.render(text, True, WHITE)
            self.screen.blit(inst_text, (10, 10 + (i+1) * 30))
