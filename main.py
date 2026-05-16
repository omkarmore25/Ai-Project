import pygame
import random
import time
import os
import math
from settings import *
from pathfinding import a_star, best_first_search, heuristic

# ─── Sound Manager ─────────────────────────────────────────────────────────────

class SoundManager:
    """Loads and plays all game sounds. Gracefully degrades if files are missing."""

    SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.mixer.init()
        self._sfx = {}
        self._load()
        self._footstep_timer = 0.0
        self._footstep_delay = 0.28   # seconds between footstep sounds

    def _load(self):
        files = {
            "menu_music":     "menu_music.wav",
            "player_won":     "player_won.wav",
            "player_caught":  "player_caught.wav",
            "time_up":        "time_up.wav",
            "footstep":       "footstep.wav",
            "countdown_tick": "countdown_tick.wav",
            "countdown_go":   "countdown_go.wav",
        }
        for key, fname in files.items():
            path = os.path.join(self.SOUNDS_DIR, fname)
            try:
                self._sfx[key] = pygame.mixer.Sound(path)
            except Exception:
                self._sfx[key] = None

    def play_menu_music(self):
        if self._sfx.get("menu_music"):
            pygame.mixer.stop()
            self._sfx["menu_music"].play(loops=-1)   # infinite loop

    def stop_music(self):
        pygame.mixer.stop()

    def play(self, key):
        snd = self._sfx.get(key)
        if snd:
            snd.play()

    def try_footstep(self, moved: bool):
        """Call every frame. Plays a footstep if the player just moved."""
        now = time.time()
        if moved and now - self._footstep_timer > self._footstep_delay:
            self.play("footstep")
            self._footstep_timer = now


# Global sound manager (created once)
_sound = SoundManager()

# ─── Animated Menu Background ──────────────────────────────────────────────────
 
class FloatingIcon:
    """A floating game icon (player/ai/goal) for the menu background."""
    def __init__(self, image, w, h):
        # Create a semi-transparent version for the background
        self.image = image.copy()
        self.image.set_alpha(140)
        self.w, self.h = w, h
        self.reset()
        # Start at random positions
        self.x = random.uniform(50, w - 50)
        self.y = random.uniform(50, h - 50)

    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.15, 0.4)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-0.3, 0.3)
        self.float_offset = random.uniform(0, 2 * math.pi)

    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed * dt * 60
        self.y += math.sin(self.angle) * self.speed * dt * 60
        self.rotation += self.rot_speed * dt * 60
        
        # Bounce off edges
        if self.x < 20 or self.x > self.w - 20:
            self.angle = math.pi - self.angle
        if self.y < 20 or self.y > self.h - 20:
            self.angle = -self.angle

    def draw(self, surface, t):
        # Subtle floating bobbing effect
        bob = math.sin(t * 1.5 + self.float_offset) * 8
        rot_image = pygame.transform.rotate(self.image, self.rotation)
        rect = rot_image.get_rect(center=(self.x, self.y + bob))
        surface.blit(rot_image, rect)


def draw_menu_background(surface, bg_image=None, decorations=None, t=0, dt=0):
    """Render the static background with optional floating decorations."""
    w, h = surface.get_size()

    surface.fill((10, 10, 20)) # Dark background fallback

    if bg_image:
        surface.blit(bg_image, (0, 0))
        
        # Add a dark semi-transparent overlay to make text pop out
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

    # Draw floating decorations
    if decorations:
        for d in decorations:
            d.update(dt)
            d.draw(surface, t)

    # Subtle vignette at corners
    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    for corner in [(0, 0), (w, 0), (0, h), (w, h)]:
        cx, cy = corner
        for rad in range(min(w, h) // 2, 0, -8):
            a = max(0, int(60 * (1 - rad / (min(w, h) / 2))))
            pygame.draw.circle(vignette, (0, 0, 0, a), (cx, cy), rad)
    surface.blit(vignette, (0, 0))


# ─── Menu ──────────────────────────────────────────────────────────────────────

def draw_glowing_text(surface, font, text, color, pos, glow_color=None, glow_radius=3):
    """Render text with a soft glow halo."""
    if glow_color is None:
        glow_color = tuple(min(255, c + 100) for c in color)
    cx, cy = pos
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if abs(dx) + abs(dy) <= glow_radius + 1:
                s = font.render(text, True, glow_color)
                s.set_alpha(40)
                r = s.get_rect(center=(cx + dx, cy + dy))
                surface.blit(s, r)
    main_s = font.render(text, True, color)
    r = main_s.get_rect(center=(cx, cy))
    surface.blit(main_s, r)


def draw_button(surface, rect, text, font, text_color, border_color, hover=False, t=0):
    """Draw a glassmorphism-style button with optional hover glow."""
    x, y, w, h = rect

    # Glass fill
    glass = pygame.Surface((w, h), pygame.SRCALPHA)
    glass.fill((255, 255, 255, 18 if not hover else 35))
    surface.blit(glass, (x, y))

    # Animated glow border when hovered
    pulse = 1.0 + 0.15 * math.sin(t * 4) if hover else 1.0
    border_w = int(2 * pulse)
    pygame.draw.rect(surface, border_color, rect, border_w, border_radius=12)

    # Subtle inner highlight
    highlight = pygame.Surface((w - 4, 2), pygame.SRCALPHA)
    highlight.fill((255, 255, 255, 40))
    surface.blit(highlight, (x + 2, y + 2))

    # Text
    txt = font.render(text, True, text_color)
    surface.blit(txt, txt.get_rect(center=(x + w // 2, y + h // 2)))


def show_menu():
    pygame.init()
    W, H = 560, 500
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("AI Chase Game - Menu")

    f_title  = pygame.font.SysFont("Verdana", 28, bold=True)
    f_sub    = pygame.font.SysFont("Verdana", 16, bold=True)
    f_small  = pygame.font.SysFont("Verdana", 13)
    clock    = pygame.time.Clock()

    # Background element
    bg_image = None
    try:
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "menu_bg.png")
        bg_image = pygame.image.load(bg_path).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (W, H))
        # Keep image fully opaque now that particles are gone
    except Exception:
        pass

    # Load and prepare floating decorations
    decorations = []
    try:
        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        icon_size = 45
        img_p = pygame.image.load(os.path.join(asset_path, "player.jpg")).convert_alpha()
        img_p = pygame.transform.smoothscale(img_p, (icon_size, icon_size))
        img_a = pygame.image.load(os.path.join(asset_path, "ai.jpg")).convert_alpha()
        img_a = pygame.transform.smoothscale(img_a, (icon_size, icon_size))
        img_g = pygame.image.load(os.path.join(asset_path, "goal.jpg")).convert_alpha()
        img_g = pygame.transform.smoothscale(img_g, (icon_size, icon_size))
        
        # Create a few instances of each
        for img in [img_p, img_a, img_g]:
            for _ in range(2): # 2 of each
                decorations.append(FloatingIcon(img, W, H))
    except Exception:
        pass

    # Start menu music
    _sound.play_menu_music()

    # ── Difficulty selection ──────────────────────────────────────────────────
    diff = None
    prev_time = time.time()
    while not diff:
        now = time.time()
        dt = now - prev_time
        prev_time = now
        t = now

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: diff = "Easy"
                if event.key == pygame.K_2: diff = "Hard"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if easy_rect.collidepoint(mx, my):  diff = "Easy"
                if hard_rect.collidepoint(mx, my):  diff = "Hard"

        mx, my = pygame.mouse.get_pos()

        # Button rects
        btn_w, btn_h = 420, 58
        bx = (W - btn_w) // 2
        easy_rect = pygame.Rect(bx, 210, btn_w, btn_h)
        hard_rect = pygame.Rect(bx, 295, btn_w, btn_h)

        # Draw
        draw_menu_background(screen, bg_image, decorations, t, dt)

        # Title banner
        banner = pygame.Surface((W, 70), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 80))
        screen.blit(banner, (0, 55))

        # Pulsing title glow
        glow_alpha = int(160 + 80 * math.sin(t * 2))
        draw_glowing_text(screen, f_title, "⚡ AI CHASE GAME ⚡",
                          (255, 255, 255), (W // 2, 90),
                          glow_color=(80, 180, 255))
        draw_glowing_text(screen, f_sub, "SELECT DIFFICULTY",
                          (180, 220, 255), (W // 2, 160),
                          glow_color=(60, 140, 255))

        # Easy button
        hover_easy = easy_rect.collidepoint(mx, my)
        draw_button(screen, easy_rect, "1.  Easy Mode", f_sub,
                    (200, 255, 200), (0, 230, 80), hover_easy, t)

        # Hard button
        hover_hard = hard_rect.collidepoint(mx, my)
        draw_button(screen, hard_rect, "2.  Hard Mode", f_sub,
                    (255, 200, 200), (230, 60, 60), hover_hard, t)

        # Keyboard hint
        hint = f_small.render("Press 1 / 2  or  click to choose", True, (120, 140, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, 395)))

        # Footer
        footer = f_small.render("Navigate with WASD or Arrow Keys", True, (80, 100, 140))
        screen.blit(footer, footer.get_rect(center=(W // 2, 460)))

        pygame.display.flip()
        clock.tick(60)

    # ── Sector selection ──────────────────────────────────────────────────────
    size = None
    prev_time = time.time()
    while not size:
        now = time.time()
        dt = now - prev_time
        prev_time = now
        t = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: size = 10
                if event.key == pygame.K_2: size = 15
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if s1_rect.collidepoint(mx, my): size = 10
                if s2_rect.collidepoint(mx, my): size = 15

        mx, my = pygame.mouse.get_pos()

        btn_w, btn_h = 420, 58
        bx = (W - btn_w) // 2
        s1_rect = pygame.Rect(bx, 220, btn_w, btn_h)
        s2_rect = pygame.Rect(bx, 305, btn_w, btn_h)

        draw_menu_background(screen, bg_image, decorations, t, dt)

        diff_color = (100, 255, 120) if diff == "Easy" else (255, 100, 100)
        label_text = f"DIFFICULTY : {diff.upper()}"

        # Measure text to size the backing pill
        title_surf_w = f_title.render(label_text, True, (255, 255, 255))
        tw, th = title_surf_w.get_size()
        pad_x, pad_y = 32, 14
        pill_rect = pygame.Rect(0, 0, tw + pad_x * 2, th + pad_y * 2)
        pill_rect.center = (W // 2, 95)

        # Fully opaque solid black pill — nothing bleeds through
        pygame.draw.rect(screen, (5, 5, 15), pill_rect, border_radius=12)
        pygame.draw.rect(screen, diff_color, pill_rect, 3, border_radius=12)

        # 8-direction black shadow for contrast, then bright white text on top
        cx, cy = W // 2, 95
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,-2),(-2,2),(2,2)]:
            sh = f_title.render(label_text, True, (0, 0, 0))
            screen.blit(sh, sh.get_rect(center=(cx + ox, cy + oy)))
        screen.blit(title_surf_w, title_surf_w.get_rect(center=(cx, cy)))

        draw_glowing_text(screen, f_sub, "SELECT SECTOR",
                          (180, 220, 255), (W // 2, 155), glow_color=(60, 140, 255))

        hover_s1 = s1_rect.collidepoint(mx, my)
        draw_button(screen, s1_rect, "1.  Sector 1  ( 10 × 10 )", f_sub,
                    (200, 230, 255), (60, 180, 255), hover_s1, t)

        hover_s2 = s2_rect.collidepoint(mx, my)
        draw_button(screen, s2_rect, "2.  Sector 2  ( 15 × 15 )", f_sub,
                    (220, 200, 255), (160, 80, 255), hover_s2, t)

        hint = f_small.render("Press 1 / 2  or  click to choose", True, (120, 140, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, 405)))

        pygame.display.flip()
        clock.tick(60)

    _sound.stop_music()
    return diff, size


# ─── Game ──────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self, difficulty, grid_size):
        pygame.init()
        stats = DIFFICULTY_DATA[difficulty][grid_size]

        self.difficulty = difficulty
        self.grid_size  = grid_size
        self.obs_count  = stats["obs"]
        self.ai_interval = stats["speed"]
        self.time_limit  = stats["time"]

        self.screen_dim = self.grid_size * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_dim, self.screen_dim + 70))
        pygame.display.set_caption(f"AI Chase Game: {difficulty} – Sector {grid_size}×{grid_size}")

        # Scale fonts so they fit on small (10x10=400px) and large (15x15=600px) screens
        hud_size = 14 if self.screen_dim <= 400 else 18
        msg_size = 18 if self.screen_dim <= 400 else 24
        self.font     = pygame.font.SysFont("Verdana", hud_size, bold=True)
        self.big_font = pygame.font.SysFont("Verdana", msg_size, bold=True)
        self.clock    = pygame.time.Clock()

        self.running     = True
        self.game_over   = False
        self.result_text  = ""
        self.result_color = WHITE

        # Sound flags to avoid repeated triggers
        self._end_sound_played = False

        self.load_assets()
        self.reset_game()

    # ── Asset loading ─────────────────────────────────────────────────────────

    def load_assets(self):
        self.use_assets = True
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
            self.img_player = pygame.image.load(os.path.join(path, "player.jpg")).convert_alpha()
            self.img_player = pygame.transform.scale(self.img_player, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_ai     = pygame.image.load(os.path.join(path, "ai.jpg")).convert_alpha()
            self.img_ai     = pygame.transform.scale(self.img_ai, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_goal   = pygame.image.load(os.path.join(path, "goal.jpg")).convert_alpha()
            self.img_goal   = pygame.transform.scale(self.img_goal, (CELL_SIZE - 8, CELL_SIZE - 8))
        except Exception:
            self.use_assets = False

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset_game(self):
        now = time.time()
        self.reset_time       = now
        self.start_time       = now + 3.99  # 3s countdown + 1s for "GO!"
        self.last_ai_move     = self.start_time
        self.last_player_move = self.start_time
        self.player_delay     = 0.12
        self.game_over        = False
        self.result_text      = ""
        self._end_sound_played = False
        self._prev_player_pos  = None
        self._time_warning_played = False
        self.time_left         = self.time_limit
        self._last_countdown_sec = 4 # Track seconds to play beep once per sec
        self.generate_valid_map()

    def generate_valid_map(self):
        # Choose pathfinding algorithm based on difficulty
        path_fn = a_star if self.difficulty == "Hard" else best_first_search
        while True:
            all_cells = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size)]
            self.player_pos = random.choice(all_cells)
            self.goal_pos   = random.choice([c for c in all_cells if heuristic(c, self.player_pos) > 4])
            self.ai_pos     = random.choice([c for c in all_cells
                                             if heuristic(c, self.player_pos) > 5 and c != self.goal_pos])
            occupied  = {self.player_pos, self.goal_pos, self.ai_pos}
            available = [c for c in all_cells if c not in occupied]
            self.obstacles = set(random.sample(available, self.obs_count))
            if (path_fn(self.grid_size, self.ai_pos, self.player_pos, self.obstacles) and
                    a_star(self.grid_size, self.player_pos, self.goal_pos, self.obstacles)):
                break

    # ── Update logic ──────────────────────────────────────────────────────────

    def update(self, player_moved: bool):
        if self.game_over:
            return

        now = time.time()
        if now < self.start_time:
            return  # Freeze game during countdown

        # Footstep sound
        _sound.try_footstep(player_moved)

        elapsed = now - self.start_time
        self.time_left = max(0, self.time_limit - int(elapsed))

        if self.time_left <= 0:
            self.end("Time Up! (LOST)", RED, "time_up")

        if time.time() - self.last_ai_move > self.ai_interval:
            # Easy → Greedy Best First Search  |  Hard → A*
            if self.difficulty == "Hard":
                path = a_star(self.grid_size, self.ai_pos, self.player_pos, self.obstacles)
            else:
                path = best_first_search(self.grid_size, self.ai_pos, self.player_pos, self.obstacles)
            if path:
                self.ai_pos = path[0]
            self.last_ai_move = time.time()

        if self.player_pos == self.ai_pos:
            self.end("AI Caught You! (LOST)", RED, "player_caught")
        elif self.player_pos == self.goal_pos:
            score = self.time_left * 10
            self.end(f"You Won! Score: {score}", (0, 220, 80), "player_won")

    def end(self, msg, color, sound_key):
        self.game_over    = True
        self.result_text  = msg
        self.result_color = color
        if not self._end_sound_played:
            _sound.play(sound_key)
            self._end_sound_played = True

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_grid(self):
        self.screen.fill((255, 255, 255))   # white game background
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (200, 200, 210), rect, 1)   # light grid lines
                if (r, c) in self.obstacles:
                    pygame.draw.rect(self.screen, (100, 100, 120), rect)  # dark obstacles
                    pygame.draw.rect(self.screen, (70, 70, 90), rect, 1)

    def draw_hud(self):
        ui_y   = self.screen_dim
        ui_rect = pygame.Rect(0, ui_y, self.screen_dim, 70)
        pygame.draw.rect(self.screen, (20, 20, 35), ui_rect)
        pygame.draw.line(self.screen, (60, 80, 180), (0, ui_y), (self.screen_dim, ui_y), 2)

        time_color = (255, 80, 80) if self.time_left <= 5 else (200, 220, 255)
        # Short label for narrow screens (10x10 = 400px), full label for wider ones
        if self.screen_dim <= 400:
            label = f"TIME: {self.time_left}s  |  {self.difficulty}"
        else:
            label = f"TIME: {self.time_left}s   |   MODE: {self.difficulty}"
        status = self.font.render(label, True, time_color)
        self.screen.blit(status, (14, ui_y + 24))

    def draw_message_box(self):
        overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        # Auto-shrink message font until it fits within the screen width
        font_size = 18 if self.screen_dim <= 400 else 24
        while font_size >= 10:
            mf = pygame.font.SysFont("Verdana", font_size, bold=True)
            msg_surf = mf.render(self.result_text, True, self.result_color)
            if msg_surf.get_width() <= self.screen_dim - 20:
                break
            font_size -= 1

        sf = pygame.font.SysFont("Verdana", max(10, font_size - 4), bold=True)
        sub_text = "R: Restart  |  M: Menu" if self.screen_dim <= 400 else "R: Restart  |  M: Back to Menu"
        sub_surf = sf.render(sub_text, True, (200, 200, 220))

        # Clamp box width to screen
        box_w = min(max(msg_surf.get_width(), sub_surf.get_width()) + 40, self.screen_dim - 10)
        box_rect = pygame.Rect(0, 0, box_w, 110)
        box_rect.center = (self.screen_dim // 2, self.screen_dim // 2)

        box_surf = pygame.Surface((box_w, 110), pygame.SRCALPHA)
        box_surf.fill((20, 20, 40, 220))
        self.screen.blit(box_surf, box_rect.topleft)
        pygame.draw.rect(self.screen, self.result_color, box_rect, 2, border_radius=12)

        msg_rect = msg_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 - 18))
        sub_rect = sub_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 + 28))
        self.screen.blit(msg_surf, msg_rect)
        self.screen.blit(sub_surf, sub_rect)

    def draw_countdown(self):
        now = time.time()
        if now >= self.start_time: return
        
        rem = self.start_time - now
        current_sec = int(math.ceil(rem))
        
        # Play sound once per countdown step
        if current_sec != self._last_countdown_sec:
            if current_sec > 0:
                _sound.play("countdown_tick")
            else:
                _sound.play("countdown_go")
            self._last_countdown_sec = current_sec

        if rem > 1.0:
            text = str(int(rem))
            color = (255, 200, 50)
            scale = 1.0 + (rem % 1.0) * 0.5  # Pop effect on each second
        else:
            text = "GO!"
            color = (50, 255, 100)
            scale = 1.0 + (rem % 1.0) * 1.5  # Fast zoom for GO!
            
        overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # Render and scale text
        surf = self.big_font.render(text, True, color)
        w, h = surf.get_size()
        scaled_surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
        rect = scaled_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2))
        
        # Glow
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
            sh = self.big_font.render(text, True, (0, 0, 0))
            sh = pygame.transform.scale(sh, (int(w * scale), int(h * scale)))
            self.screen.blit(sh, sh.get_rect(center=(self.screen_dim // 2 + ox, self.screen_dim // 2 + oy)))
            
        self.screen.blit(scaled_surf, rect)

    def draw_danger_zone(self):
        dist = heuristic(self.player_pos, self.ai_pos)
        if dist <= 3 and not self.game_over and time.time() >= self.start_time:
            # Pulse intensity based on how close AI is
            intensity = int((4 - dist) * 20 + 20 * math.sin(time.time() * 10))
            intensity = max(0, min(120, intensity))
            
            overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
            # Red vignette around screen edges
            pygame.draw.rect(overlay, (255, 0, 0, intensity), overlay.get_rect(), width=15)
            self.screen.blit(overlay, (0, 0))

    def draw(self):
        self.draw_grid()
        if self.use_assets:
            self.screen.blit(self.img_goal,   (self.goal_pos[1]   * CELL_SIZE + 4, self.goal_pos[0]   * CELL_SIZE + 4))
            self.screen.blit(self.img_player, (self.player_pos[1] * CELL_SIZE + 4, self.player_pos[0] * CELL_SIZE + 4))
            self.screen.blit(self.img_ai,     (self.ai_pos[1]     * CELL_SIZE + 4, self.ai_pos[0]     * CELL_SIZE + 4))
        else:
            pygame.draw.rect(self.screen, (255, 215, 0), (self.goal_pos[1]   * CELL_SIZE + 4, self.goal_pos[0]   * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
            pygame.draw.rect(self.screen, GREEN,         (self.player_pos[1] * CELL_SIZE + 4, self.player_pos[0] * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
            pygame.draw.rect(self.screen, RED,           (self.ai_pos[1]     * CELL_SIZE + 4, self.ai_pos[0]     * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
        
        self.draw_danger_zone()
        self.draw_hud()
        
        if time.time() < self.start_time:
            self.draw_countdown()
        elif self.game_over:
            self.draw_message_box()
            
        pygame.display.flip()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            player_moved = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_m:
                        return "MENU"

            if not self.game_over and time.time() >= self.start_time:
                keys = pygame.key.get_pressed()
                if time.time() - self.last_player_move > self.player_delay:
                    nr, nc = self.player_pos
                    if   keys[pygame.K_UP]    or keys[pygame.K_w]: nr -= 1
                    elif keys[pygame.K_DOWN]  or keys[pygame.K_s]: nr += 1
                    elif keys[pygame.K_LEFT]  or keys[pygame.K_a]: nc -= 1
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: nc += 1

                    if (nr, nc) != self.player_pos:
                        if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                            if (nr, nc) not in self.obstacles:
                                self.player_pos = (nr, nc)
                                self.last_player_move = time.time()
                                player_moved = True

            self.update(player_moved)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    while True:
        d, s = show_menu()
        if d and s:
            game = Game(d, s)
            result = game.run()
            if result != "MENU":
                break
        else:
            break