# game.py — Endless runner / shooter game for Galactic Unicorn (53x11)
#
# Layout:
#   Row 0   = ceiling (white line)
#   Row 10  = floor (white line)
#   Rows 1-9 = play area (9 rows)
#
# Ship: 2 wide x 3 tall, fixed at x=2, y=ship_y (ship_y range 1..7)
# Enemies: 2x2, spawn at x=52, move left each frame
# Bullets: 1x1, move right 2px/frame
# Score: kills, shown top-right corner (small digits)

import gc
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY
from galactic import GalacticUnicorn
from utime import ticks_ms, ticks_diff, sleep_ms

W = GalacticUnicorn.WIDTH   # 53
H = GalacticUnicorn.HEIGHT  # 11

# Colors (R,G,B)
_BLACK   = (0,   0,   0)
_WHITE   = (200, 200, 200)
_GREEN   = (0,   200, 50)
_RED     = (200, 30,  0)
_YELLOW  = (200, 180, 0)
_CYAN    = (0,   180, 200)
_MAGENTA = (180, 0,   180)

# Game constants
_SHIP_X        = 1       # ship left edge
_SHIP_W        = 2       # ship width
_SHIP_H        = 3       # ship height
_SHIP_Y_MIN    = 1       # min ship top y
_SHIP_Y_MAX    = H - 1 - _SHIP_H  # max ship top y = 7
_ENEMY_W       = 2
_ENEMY_H       = 2
_BULLET_SPEED  = 2       # px per frame
_FRAME_MS      = 50      # ~20fps
_FIRE_COOLDOWN = 200     # ms between shots
_SPEED_INIT    = 1.0     # enemy px per frame
_SPEED_INC     = 0.3     # speed increase per 5 kills
_MAX_ENEMIES   = 4
_MAX_BULLETS   = 3
_SPAWN_INTERVAL_INIT = 40   # frames between enemy spawns
_SPAWN_INTERVAL_MIN  = 15

class Game:
    def __init__(self, galactic, graphics, sounds):
        self.galactic = galactic
        self.graphics = graphics
        self.sounds = sounds
        self._pens = {}
        self._mk_pens()
        self.reset()

    def _mk_pens(self):
        g = self.graphics
        for name, rgb in [
            ('black',   _BLACK),
            ('white',   _WHITE),
            ('green',   _GREEN),
            ('red',     _RED),
            ('yellow',  _YELLOW),
            ('cyan',    _CYAN),
            ('magenta', _MAGENTA),
        ]:
            self._pens[name] = g.create_pen(*rgb)

    def _pen(self, name):
        self.graphics.set_pen(self._pens[name])

    def reset(self):
        self.ship_y    = 4      # top of ship (1..7)
        self.enemies   = []     # list of [x, y, alive]
        self.bullets   = []     # list of [x, y]
        self.score     = 0
        self.alive     = True
        self.over_text_done = False
        self.enemy_speed    = _SPEED_INIT
        self.enemy_frac     = 0.0   # fractional accumulator for sub-pixel movement
        self.spawn_timer    = 0
        self.spawn_interval = _SPAWN_INTERVAL_INIT
        self.frame_count    = 0
        self.last_fire_ms   = 0
        self.game_over_ms   = 0
        self._last_frame_ms = 0     # frame rate limiter
        gc.collect()

    # ------------------------------------------------------------------ #
    def update(self, pad):
        """Advance game state by one frame. pad = DualSense instance."""
        if not self.alive:
            # restart on cross press
            if pad.cross:
                self.reset()
            return

        self.frame_count += 1
        now = ticks_ms()

        # --- Ship movement ---
        if pad.dy == -1:
            self.ship_y = max(_SHIP_Y_MIN, self.ship_y - 1)
        elif pad.dy == 1:
            self.ship_y = min(_SHIP_Y_MAX, self.ship_y + 1)

        # --- Fire ---
        if pad.cross and ticks_diff(now, self.last_fire_ms) >= _FIRE_COOLDOWN:
            if len(self.bullets) < _MAX_BULLETS:
                self.bullets.append([_SHIP_X + _SHIP_W, self.ship_y + 1])
                self.last_fire_ms = now

        # --- Move bullets ---
        new_bullets = []
        for b in self.bullets:
            b[0] += _BULLET_SPEED
            if b[0] < W:
                new_bullets.append(b)
        self.bullets = new_bullets

        # --- Spawn enemies ---
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval and len(self.enemies) < _MAX_ENEMIES:
            import urandom
            ey = urandom.randint(_SHIP_Y_MIN, H - 1 - _ENEMY_H)
            self.enemies.append([W - 1, ey, True])
            self.spawn_timer = 0

        # --- Move enemies ---
        self.enemy_frac += self.enemy_speed
        steps = int(self.enemy_frac)
        self.enemy_frac -= steps

        surviving = []
        for e in self.enemies:
            e[0] -= steps
            if e[0] + _ENEMY_W > 0:
                surviving.append(e)
        self.enemies = surviving

        # --- Bullet-enemy collisions ---
        hits = set()
        killed = []
        for bi, b in enumerate(self.bullets):
            for ei, e in enumerate(self.enemies):
                if (e[0] <= b[0] < e[0] + _ENEMY_W and
                        e[1] <= b[1] < e[1] + _ENEMY_H):
                    hits.add(bi)
                    killed.append(ei)

        self.bullets = [b for i,b in enumerate(self.bullets) if i not in hits]
        for ei in sorted(set(killed), reverse=True):
            self.enemies.pop(ei)
            self.score += 1

        # Increase difficulty every 5 kills
        lvl = self.score // 5
        self.enemy_speed    = min(_SPEED_INIT + lvl * _SPEED_INC, 4.0)
        self.spawn_interval = max(_SPAWN_INTERVAL_MIN,
                                  _SPAWN_INTERVAL_INIT - lvl * 3)

        # --- Ship-enemy collision (game over) ---
        for e in self.enemies:
            if (e[0] < _SHIP_X + _SHIP_W and e[0] + _ENEMY_W > _SHIP_X and
                    e[1] < self.ship_y + _SHIP_H and e[1] + _ENEMY_H > self.ship_y):
                self.alive = False
                self.game_over_ms = now
                if hasattr(self.sounds, 'sad') and self.sounds.sad:
                    self.sounds.sad.play()
                break

    # ------------------------------------------------------------------ #
    def draw(self, pad):
        """Update game state and render one frame — rate limited to ~20fps."""
        now = ticks_ms()
        if ticks_diff(now, self._last_frame_ms) < _FRAME_MS:
            return
        self._last_frame_ms = now

        self.update(pad)

        g = self.graphics
        self._pen('black')
        g.clear()

        # Ceiling & floor
        self._pen('white')
        g.line(0, 0, W - 1, 0)
        g.line(0, H - 1, W - 1, H - 1)

        if not self.alive:
            self._draw_game_over()
        else:
            self._draw_play()

        self.galactic.update(g)

    def _draw_play(self):
        g = self.graphics

        # Ship (green, 3 rows)
        self._pen('green')
        # Draw ship as:  .X
        #                XX
        #                .X
        g.pixel(_SHIP_X + 1, self.ship_y)
        g.pixel(_SHIP_X,     self.ship_y + 1)
        g.pixel(_SHIP_X + 1, self.ship_y + 1)
        g.pixel(_SHIP_X + 1, self.ship_y + 2)

        # Bullets (yellow)
        self._pen('yellow')
        for b in self.bullets:
            g.pixel(b[0], b[1])

        # Enemies (red, 2x2)
        self._pen('red')
        for e in self.enemies:
            for dx in range(_ENEMY_W):
                for dy in range(_ENEMY_H):
                    ex = e[0] + dx
                    ey = e[1] + dy
                    if 0 <= ex < W and 0 < ey < H - 1:
                        g.pixel(ex, ey)

        # Score (top-right, small white digits using bitmap6)
        self._pen('white')
        g.set_font("bitmap6")
        score_str = str(self.score)
        sw = g.measure_text(score_str, 1)
        g.text(score_str, W - sw - 1, 1, -1, 1)

    def _draw_game_over(self):
        g = self.graphics
        g.set_font("bitmap6")
        self._pen('red')
        msg = "GAME OVER"
        w = g.measure_text(msg, 1)
        g.text(msg, (W - w) // 2, 2, -1, 1)
        self._pen('white')
        sc = f"WYNIK:{self.score}"
        w2 = g.measure_text(sc, 1)
        g.text(sc, (W - w2) // 2, 6, -1, 1)
