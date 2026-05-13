import pygame
import random
import time
import os
from settings import *
from pathfinding import a_star, heuristic

class Game:
    def __init__(self, difficulty, grid_size):
        pygame.init()
        stats = DIFFICULTY_DATA[difficulty][grid_size]
        
        self.difficulty = difficulty
        self.grid_size = grid_size
        self.obs_count = stats["obs"]
        self.ai_interval = stats["speed"]
        self.time_limit = stats["time"]
        
        self.screen_dim = self.grid_size * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_dim, self.screen_dim + 70))
        pygame.display.set_caption(f"AI Chase Game: {difficulty} - Sector {grid_size}x{grid_size}")
        
        self.font = pygame.font.SysFont("Verdana", 18, bold=True)
        self.big_font = pygame.font.SysFont("Verdana", 24, bold=True)
        self.clock = pygame.time.Clock()
        
        self.running = True
        self.game_over = False
        self.result_text = ""
        self.result_color = WHITE
        
        self.load_assets()
        self.reset_game()

    def load_assets(self):
        self.use_assets = True
        try:
            path = "assets"
            self.img_player = pygame.image.load(os.path.join(path, "player.jpg")).convert_alpha()
            self.img_player = pygame.transform.scale(self.img_player, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_ai = pygame.image.load(os.path.join(path, "ai.jpg")).convert_alpha()
            self.img_ai = pygame.transform.scale(self.img_ai, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_goal = pygame.image.load(os.path.join(path, "goal.jpg")).convert_alpha()
            self.img_goal = pygame.transform.scale(self.img_goal, (CELL_SIZE - 8, CELL_SIZE - 8))
        except:
            self.use_assets = False

    def reset_game(self):
        self.start_time = time.time()
        self.last_ai_move = time.time()
        self.last_player_move = time.time()
        self.player_delay = 0.12
        self.game_over = False
        self.result_text = ""
        self.generate_valid_map()

    def generate_valid_map(self):
        while True:
            all_cells = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size)]
            self.player_pos = random.choice(all_cells)
            self.goal_pos = random.choice([c for c in all_cells if heuristic(c, self.player_pos) > 4])
            self.ai_pos = random.choice([c for c in all_cells if heuristic(c, self.player_pos) > 5 and c != self.goal_pos])
            
            occupied = {self.player_pos, self.goal_pos, self.ai_pos}
            available = [c for c in all_cells if c not in occupied]
            self.obstacles = set(random.sample(available, self.obs_count))

            if a_star(self.grid_size, self.ai_pos, self.player_pos, self.obstacles) and \
               a_star(self.grid_size, self.player_pos, self.goal_pos, self.obstacles):
                break

    def update(self):
        if self.game_over: return

        elapsed = time.time() - self.start_time
        self.time_left = max(0, self.time_limit - int(elapsed))
        
        if self.time_left <= 0: 
            self.end("Time Up (LOST)", RED)

        if time.time() - self.last_ai_move > self.ai_interval:
            path = a_star(self.grid_size, self.ai_pos, self.player_pos, self.obstacles)
            if path: self.ai_pos = path[0]
            self.last_ai_move = time.time()

        if self.player_pos == self.ai_pos: 
            self.end("Ai caught you (LOST)", RED)
        elif self.player_pos == self.goal_pos: 
            self.end("Player reached Goal (WON)", GREEN)

    def end(self, msg, color):
        self.game_over = True
        self.result_text = msg
        self.result_color = color

    def draw_message_box(self):
        overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))

        msg_surf = self.big_font.render(self.result_text, True, self.result_color)
        msg_rect = msg_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 - 20))
        sub_surf = self.font.render("R: Restart | M: Menu", True, WHITE)
        sub_rect = sub_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 + 30))
        
        box_rect = pygame.Rect(0, 0, max(msg_rect.width, sub_rect.width) + 40, 100)
        box_rect.center = (self.screen_dim // 2, self.screen_dim // 2)
        pygame.draw.rect(self.screen, (30, 30, 40), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.result_color, box_rect, 2, border_radius=10)

        self.screen.blit(msg_surf, msg_rect)
        self.screen.blit(sub_surf, sub_rect)

    def draw(self):
        self.screen.fill(WHITE)
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (220, 220, 220), rect, 1)
                if (r, c) in self.obstacles:
                    pygame.draw.rect(self.screen, (100, 100, 100), rect)

        if self.use_assets:
            self.screen.blit(self.img_goal, (self.goal_pos[1]*CELL_SIZE+4, self.goal_pos[0]*CELL_SIZE+4))
            self.screen.blit(self.img_player, (self.player_pos[1]*CELL_SIZE+4, self.player_pos[0]*CELL_SIZE+4))
            self.screen.blit(self.img_ai, (self.ai_pos[1]*CELL_SIZE+4, self.ai_pos[0]*CELL_SIZE+4))
        
        ui_rect = pygame.Rect(0, self.screen_dim, self.screen_dim, 70)
        pygame.draw.rect(self.screen, (240, 240, 240), ui_rect)
        pygame.draw.line(self.screen, BLACK, (0, self.screen_dim), (self.screen_dim, self.screen_dim), 2)
        status = self.font.render(f"TIME: {self.time_left}s | MODE: {self.difficulty}", True, BLACK)
        self.screen.blit(status, (20, self.screen_dim + 25))

        if self.game_over: self.draw_message_box()
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if self.game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: self.reset_game()
                    if event.key == pygame.K_m: return "MENU"

            if not self.game_over:
                keys = pygame.key.get_pressed()
                if time.time() - self.last_player_move > self.player_delay:
                    nr, nc = self.player_pos
                    if keys[pygame.K_UP] or keys[pygame.K_w]: nr -= 1
                    elif keys[pygame.K_DOWN] or keys[pygame.K_s]: nr += 1
                    elif keys[pygame.K_LEFT] or keys[pygame.K_a]: nc -= 1
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: nc += 1
                    if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                        if (nr, nc) not in self.obstacles:
                            self.player_pos = (nr, nc)
                            self.last_player_move = time.time()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

def show_menu():
    pygame.init()
    screen = pygame.display.set_mode((500, 450))
    pygame.display.set_caption("AI Chase Game - Menu")
    f_title = pygame.font.SysFont("Verdana", 24, bold=True)
    f_sub = pygame.font.SysFont("Verdana", 18)
    
    diff = None
    while not diff:
        screen.fill((15, 15, 25))
        screen.blit(f_title.render("SELECT DIFFICULTY", True, WHITE), (120, 80))
        opts = [("1. Easy Mode", GREEN, pygame.K_1), ("2. Hard Mode", RED, pygame.K_2)]
        for i, (t, c, k) in enumerate(opts):
            pygame.draw.rect(screen, (30, 30, 45), (50, 180 + i*100, 400, 60), border_radius=10)
            pygame.draw.rect(screen, c, (50, 180 + i*100, 400, 60), 2, border_radius=10)
            screen.blit(f_sub.render(t, True, WHITE), (180, 195 + i*100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: diff = "Easy"
                if event.key == pygame.K_2: diff = "Hard"

    size = None
    while not size:
        screen.fill((15, 15, 25))
        screen.blit(f_title.render(f"DIFFICULTY: {diff}", True, WHITE), (120, 50))
        screen.blit(f_title.render("SELECT SECTOR", True, WHITE), (140, 100))
        opts = [("1. Sector 1 (10 x 10)", WHITE, pygame.K_1), ("2. Sector 2 (15 x 15)", WHITE, pygame.K_2)]
        for i, (t, c, k) in enumerate(opts):
            pygame.draw.rect(screen, (30, 30, 45), (50, 180 + i*100, 400, 60), border_radius=10)
            pygame.draw.rect(screen, WHITE, (50, 180 + i*100, 400, 60), 2, border_radius=10)
            screen.blit(f_sub.render(t, True, WHITE), (150, 195 + i*100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: size = 10
                if event.key == pygame.K_2: size = 15
    return diff, size

if __name__ == "__main__":
    while True:
        d, s = show_menu()
        if d and s:
            game = Game(d, s)
            if game.run() != "MENU": break
        else: break