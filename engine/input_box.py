"""
Mathpal — Retro Input Box
==========================
A DOS-style text input widget with a blinking block cursor, sunken 3D bevel,
and keyboard capture for typing math answers.

Supports: alphanumeric, ``^``, ``x``, ``-``, ``(``, ``)``.
Returns the typed string when ENTER is pressed.
"""

import pygame

from config import (
    Colors,
    INPUTBOX_MAX_LEN,
    FONT_SIZE_MEDIUM,
)
from engine.ui_components import get_font


class InputBox:
    """Retro text input field — captures keyboard, blinking cursor, Enter to submit."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = get_font(FONT_SIZE_MEDIUM)
        self.text = ""
        self.active = False
        self.max_length = INPUTBOX_MAX_LEN

        # Blinking cursor
        self._cursor_timer = 0.0
        self._cursor_visible = True
        self._blink_interval = 0.38          # seconds

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event):
        """
        Process keyboard input.

        Returns
        -------
        str or None
            The submitted text when ENTER is pressed, else ``None``.
        """
        if not self.active:
            return None

        if event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_RETURN:
            result = self.text.strip()
            self.text = ""
            self._cursor_timer = 0
            self._cursor_visible = True
            return result if result else None

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            self._cursor_timer = 0
            self._cursor_visible = True
            return None

        # Accept printable characters up to max length
        ch = event.unicode
        if ch and ch.isprintable() and len(self.text) < self.max_length:
            self.text += ch
            self._cursor_timer = 0
            self._cursor_visible = True

        return None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        """Blink the cursor."""
        self._cursor_timer += dt
        if self._cursor_timer >= self._blink_interval:
            self._cursor_timer -= self._blink_interval
            self._cursor_visible = not self._cursor_visible

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        """Draw the input box with sunken bevel, text, and blinking cursor."""
        r = self.rect
        b = 2   # bevel width

        # --- Sunken bevel (dark top-left, light bottom-right) ------------
        pygame.draw.rect(surface, Colors.BTN_SHADOW, (r.x, r.y, r.w, b))
        pygame.draw.rect(surface, Colors.BTN_SHADOW, (r.x, r.y, b, r.h))
        pygame.draw.rect(surface, Colors.INPUT_BORDER,
                         (r.x, r.y + r.h - b, r.w, b))
        pygame.draw.rect(surface, Colors.INPUT_BORDER,
                         (r.x + r.w - b, r.y, b, r.h))

        # --- Background --------------------------------------------------
        inner = pygame.Rect(r.x + b, r.y + b, r.w - 2 * b, r.h - 2 * b)
        pygame.draw.rect(surface, Colors.INPUT_BG, inner)

        # --- Text --------------------------------------------------------
        text_surf = self.font.render(self.text, False, Colors.TEXT_PRIMARY)
        text_x = inner.x + 4
        text_y = inner.y + (inner.h - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))

        # --- Block cursor ------------------------------------------------
        if self.active and self._cursor_visible:
            cursor_x = text_x + text_surf.get_width() + 1
            cursor_h = min(inner.h - 4, text_surf.get_height())
            cursor_y = text_y
            pygame.draw.rect(surface, Colors.INPUT_CURSOR,
                             (cursor_x, cursor_y, 7, cursor_h))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def clear(self):
        self.text = ""
        self._cursor_timer = 0
        self._cursor_visible = True

    def activate(self):
        self.active = True
        self._cursor_visible = True
        self._cursor_timer = 0

    def deactivate(self):
        self.active = False
