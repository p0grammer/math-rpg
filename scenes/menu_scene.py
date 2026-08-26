"""
Mathpal — Main Menu Scene
==========================
The first screen the player sees.  Features:

* **Animated title** — "MATHPAL" with a rainbow color-wave and pulsing glow.
* **Scrolling grid + starfield** — subtle cyber/space background.
* **Chunky retro buttons** — PLAY, SETTINGS, EXIT with 3D bevels.
* **Procedural chiptune SFX** — hover blip and select arpeggio.

All rendering targets the internal 480 × 360 surface; the renderer handles
nearest-neighbor upscaling to the display window.
"""

import math
import random

import pygame

from config import (
    Colors,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING,
    FONT_SIZE_TITLE, FONT_SIZE_SMALL, FONT_SIZE_MEDIUM,
    TITLE,
)
from core.states import State
from engine.audio import AudioManager
from engine.ui_components import RetroButton, get_font


# ======================================================================
# Starfield particle
# ======================================================================

class _Star:
    """A single background star that drifts downward."""

    __slots__ = ("x", "y", "speed", "brightness")

    def __init__(self):
        self.x = random.randint(0, INTERNAL_WIDTH)
        self.y = random.randint(0, INTERNAL_HEIGHT)
        self.speed = random.uniform(12, 55)
        self.brightness = random.randint(50, 210)

    def update(self, dt):
        self.y += self.speed * dt
        if self.y >= INTERNAL_HEIGHT:
            self.y = 0
            self.x = random.randint(0, INTERNAL_WIDTH)
            self.speed = random.uniform(12, 55)
            self.brightness = random.randint(50, 210)

    def draw(self, surface):
        c = self.brightness
        # Stars are slightly blue-white
        color = (c, c, min(255, c + 45))
        surface.set_at((int(self.x), int(self.y)), color)


# ======================================================================
# Menu Scene
# ======================================================================

class MenuScene(State):
    """Main menu — animated title, starfield background, three buttons."""

    def __init__(self, game):
        super().__init__(game)
        self.audio = AudioManager()
        self.time = 0.0

        # --- Stars -------------------------------------------------------
        self.stars = [_Star() for _ in range(90)]

        # --- Fonts -------------------------------------------------------
        self.title_font    = get_font(FONT_SIZE_TITLE, bold=True)
        self.subtitle_font = get_font(FONT_SIZE_SMALL)
        self.button_font   = get_font(FONT_SIZE_MEDIUM, bold=True)
        self.small_font    = get_font(FONT_SIZE_SMALL)

        # --- Buttons (vertically centered below title) -------------------
        btn_x = (INTERNAL_WIDTH - BUTTON_WIDTH) // 2
        btn_start_y = 185

        button_defs = [
            ("\u25B6  PLAY",     self._on_play),
            ("\u2699  SETTINGS", self._on_settings),
            ("\u2716  EXIT",     self._on_exit),
        ]
        self.buttons: list[RetroButton] = []
        for i, (label, callback) in enumerate(button_defs):
            btn = RetroButton(
                btn_x,
                btn_start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                label,
            )
            btn.on_click = callback
            self.buttons.append(btn)

        # Track previous hover state for SFX edge detection
        self._prev_hovered = [False] * len(self.buttons)

        # --- Pre-render individual title characters for rainbow effect ---
        self._title_chars = list(TITLE)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def enter(self):
        self.audio.play_bgm("village")

    def exit(self):
        pass

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        converter = self.game.renderer.screen_to_internal
        for i, btn in enumerate(self.buttons):
            btn.handle_event(event, converter)
            # Play hover SFX on rising edge only
            if btn.hovered and not self._prev_hovered[i]:
                self.audio.play_sfx("hover")
            self._prev_hovered[i] = btn.hovered

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        self.time += dt
        for star in self.stars:
            star.update(dt)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        # --- Background --------------------------------------------------
        surface.fill(Colors.DARK_NAVY)
        self._draw_grid(surface)
        for star in self.stars:
            star.draw(surface)

        # --- Title -------------------------------------------------------
        self._draw_title(surface)

        # --- Decorative line ---------------------------------------------
        pulse = 0.5 + 0.5 * math.sin(self.time * 3.0)
        line_y = 130
        line_half = int(80 + 20 * pulse)
        cx = INTERNAL_WIDTH // 2
        pygame.draw.line(
            surface, Colors.NEON_CYAN,
            (cx - line_half, line_y), (cx + line_half, line_y), 2,
        )

        # --- Subtitle ----------------------------------------------------
        sub = self.subtitle_font.render(
            "LEARN MATH.  LEVEL UP.", False, Colors.TEXT_SECONDARY,
        )
        surface.blit(sub, (cx - sub.get_width() // 2, line_y + 8))

        # --- Decorative diamonds -----------------------------------------
        diamond_y = line_y + 8 + sub.get_height() // 2
        for dx in (-sub.get_width() // 2 - 14, sub.get_width() // 2 + 10):
            self._draw_diamond(surface, cx + dx, diamond_y, 4, Colors.NEON_CYAN)

        # --- Buttons -----------------------------------------------------
        for btn in self.buttons:
            btn.draw(surface, self.button_font)

        # --- Footer ------------------------------------------------------
        ver = self.small_font.render(
            "v0.1.0  //  A RETRO MATH ADVENTURE", False, Colors.TEXT_DIM,
        )
        surface.blit(ver, (cx - ver.get_width() // 2, INTERNAL_HEIGHT - 20))

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_grid(self, surface):
        """Slowly scrolling perspective grid (Tron vibes)."""
        spacing = 20
        offset = int(self.time * 18) % spacing
        grid_color = (18, 18, 55)
        for x in range(0, INTERNAL_WIDTH + spacing, spacing):
            pygame.draw.line(surface, grid_color, (x, 0), (x, INTERNAL_HEIGHT))
        for y in range(-spacing + offset, INTERNAL_HEIGHT + spacing, spacing):
            pygame.draw.line(surface, grid_color, (0, y), (INTERNAL_WIDTH, y))

    def _draw_title(self, surface):
        """
        Render each character of 'MATHPAL' with a per-letter rainbow phase
        shift and a gentle vertical bob.
        """
        # Rainbow hue cycle: each letter is 40° apart, cycling over time
        char_surfaces = []
        total_width = 0
        for i, ch in enumerate(self._title_chars):
            # HSV → RGB with shifting hue
            hue = (self.time * 60 + i * 40) % 360
            color = self._hsv_to_rgb(hue, 0.7, 1.0)
            char_surf = self.title_font.render(ch, False, color)
            char_surfaces.append(char_surf)
            total_width += char_surf.get_width()

        # Center the whole title string
        start_x = (INTERNAL_WIDTH - total_width) // 2
        base_y = 68
        cursor_x = start_x

        for i, char_surf in enumerate(char_surfaces):
            # Each letter bobs on a sine wave, phase-shifted
            bob = int(3 * math.sin(self.time * 4.0 + i * 0.6))
            surface.blit(char_surf, (cursor_x, base_y + bob))
            cursor_x += char_surf.get_width()

        # Drop shadow rendered first (underneath) — draw again shifted
        cursor_x = start_x
        for i, ch in enumerate(self._title_chars):
            char_surf = self.title_font.render(ch, False, Colors.DEEP_BLUE)
            bob = int(3 * math.sin(self.time * 4.0 + i * 0.6))
            surface.blit(char_surf, (cursor_x + 2, base_y + bob + 2))
            cursor_x += char_surf.get_width()

        # Redraw foreground on top of shadow
        cursor_x = start_x
        for i, (ch, char_surf) in enumerate(
            zip(self._title_chars, char_surfaces)
        ):
            bob = int(3 * math.sin(self.time * 4.0 + i * 0.6))
            surface.blit(char_surf, (cursor_x, base_y + bob))
            cursor_x += char_surf.get_width()

    @staticmethod
    def _draw_diamond(surface, cx, cy, r, color):
        """Draw a small diamond shape (rotated square)."""
        points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, points)

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        """
        Convert HSV (h in 0-360, s and v in 0-1) to an (R, G, B) tuple.
        """
        h60 = h / 60.0
        hi = int(h60) % 6
        f = h60 - int(h60)
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        rgb_map = {
            0: (v, t, p),
            1: (q, v, p),
            2: (p, v, t),
            3: (p, q, v),
            4: (t, p, v),
            5: (v, p, q),
        }
        r, g, b = rgb_map[hi]
        return (int(r * 255), int(g * 255), int(b * 255))

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def _on_play(self):
        self.audio.play_sfx("select")
        from scenes.play_scene import PlayScene
        self.game.change_state(PlayScene(self.game))

    def _on_settings(self):
        self.audio.play_sfx("select")
        from scenes.settings_scene import SettingsScene
        self.game.change_state(SettingsScene(self.game))

    def _on_exit(self):
        self.audio.play_sfx("select")
        # Small delay so the SFX can play before shutdown
        pygame.time.delay(150)
        self.game.running = False
