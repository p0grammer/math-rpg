"""
Mathpal — Retro UI Components
===============================
Procedurally drawn UI widgets styled after 90s desktop and console games:
chunky 3D-beveled buttons, bordered panels, and crisp pixel-font labels.

Everything is rendered directly to a ``pygame.Surface`` — no sprite assets
needed.  Anti-aliasing is always **off** so text stays sharp and crunchy
when the renderer scales it up with nearest-neighbor.
"""

import pygame

from config import (
    Colors,
    BUTTON_BEVEL,
    FONT_SIZE_MEDIUM,
    FONT_PREFERENCES,
)


# ======================================================================
# Font helper
# ======================================================================

def get_font(size, bold=False):
    """
    Return a ``pygame.font.Font`` trying each family in FONT_PREFERENCES.
    Falls back to the Pygame default if nothing matches.
    """
    for name in FONT_PREFERENCES:
        font = pygame.font.SysFont(name, size, bold=bold)
        if font:
            return font
    return pygame.font.Font(None, size)


# ======================================================================
# RetroButton
# ======================================================================

class RetroButton:
    """
    A chunky, 3D-beveled button inspired by Win 3.1 / SNES menu UIs.

    States
    ------
    * **Normal** — flat face with light top-left / dark bottom-right bevel.
    * **Hovered** — brighter face, gentle color lift.
    * **Pressed** — inverted bevel (sunken look), text offset 1px down-right.
    """

    def __init__(self, x, y, width, height, text, bevel=BUTTON_BEVEL):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bevel = bevel
        self.hovered = False
        self.pressed = False
        self.on_click = None   # Callable — set externally

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event, coord_converter=None):
        """
        Feed a ``pygame.event.Event`` to this button.

        Parameters
        ----------
        coord_converter : callable, optional
            Function that maps display-space (x, y) to internal-space.
            Pass ``renderer.screen_to_internal`` here.
        """
        if event.type == pygame.MOUSEMOTION:
            pos = coord_converter(event.pos) if coord_converter else event.pos
            self.hovered = self.rect.collidepoint(pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = coord_converter(event.pos) if coord_converter else event.pos
            if self.rect.collidepoint(pos):
                self.pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                pos = coord_converter(event.pos) if coord_converter else event.pos
                if self.rect.collidepoint(pos) and self.on_click:
                    self.on_click()
            self.pressed = False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, surface, font):
        """Draw the button onto *surface* using the supplied *font*."""
        b = self.bevel
        r = self.rect

        # Pick palette based on state
        if self.pressed:
            face = Colors.BTN_PRESSED
            tl   = Colors.BTN_SHADOW      # Inverted bevel
            br   = Colors.BTN_HIGHLIGHT
        elif self.hovered:
            face = Colors.BTN_HOVER
            tl   = Colors.BTN_HIGHLIGHT
            br   = Colors.BTN_SHADOW
        else:
            face = Colors.BTN_NORMAL
            tl   = Colors.BTN_HIGHLIGHT
            br   = Colors.BTN_SHADOW

        # --- Outer bevel (top-left light / bottom-right shadow) ----------
        # Top edge
        pygame.draw.rect(surface, tl, (r.x, r.y, r.w, b))
        # Left edge
        pygame.draw.rect(surface, tl, (r.x, r.y, b, r.h))
        # Bottom edge
        pygame.draw.rect(surface, br, (r.x, r.y + r.h - b, r.w, b))
        # Right edge
        pygame.draw.rect(surface, br, (r.x + r.w - b, r.y, b, r.h))

        # --- Face --------------------------------------------------------
        pygame.draw.rect(surface, face,
                         (r.x + b, r.y + b, r.w - 2 * b, r.h - 2 * b))

        # --- Inner 1px highlight line (top of face) for extra depth ------
        inner_hl = tuple(min(255, c + 30) for c in face)
        pygame.draw.line(surface, inner_hl,
                         (r.x + b, r.y + b),
                         (r.x + r.w - b - 1, r.y + b))

        # --- Label -------------------------------------------------------
        text_surf = font.render(self.text, False, Colors.TEXT_PRIMARY)
        tx = r.centerx - text_surf.get_width() // 2
        ty = r.centery - text_surf.get_height() // 2
        if self.pressed:
            tx += 1
            ty += 1
        surface.blit(text_surf, (tx, ty))


# ======================================================================
# RetroPanel
# ======================================================================

class RetroPanel:
    """
    A bordered rectangle — used as a backdrop for groups of UI elements.
    Drawn with a 2-tone bevel (inset style, opposite of buttons).
    """

    def __init__(self, x, y, width, height, bevel=2):
        self.rect = pygame.Rect(x, y, width, height)
        self.bevel = bevel

    def draw(self, surface, fill_color=None):
        b = self.bevel
        r = self.rect
        fill = fill_color or Colors.MIDNIGHT

        # Sunken bevel — dark top-left, light bottom-right
        pygame.draw.rect(surface, Colors.BTN_SHADOW, (r.x, r.y, r.w, b))
        pygame.draw.rect(surface, Colors.BTN_SHADOW, (r.x, r.y, b, r.h))
        pygame.draw.rect(surface, Colors.BTN_HIGHLIGHT,
                         (r.x, r.y + r.h - b, r.w, b))
        pygame.draw.rect(surface, Colors.BTN_HIGHLIGHT,
                         (r.x + r.w - b, r.y, b, r.h))

        pygame.draw.rect(surface, fill,
                         (r.x + b, r.y + b, r.w - 2 * b, r.h - 2 * b))


# ======================================================================
# RetroLabel
# ======================================================================

class RetroLabel:
    """Simple static text label.  No anti-aliasing for crisp pixel look."""

    def __init__(self, x, y, text, color=None, font_size=FONT_SIZE_MEDIUM,
                 bold=False, anchor="topleft"):
        self.pos = (x, y)
        self.text = text
        self.color = color or Colors.TEXT_PRIMARY
        self.font = get_font(font_size, bold=bold)
        self.anchor = anchor

    def draw(self, surface):
        text_surf = self.font.render(self.text, False, self.color)
        rect = text_surf.get_rect(**{self.anchor: self.pos})
        surface.blit(text_surf, rect)

    def set_text(self, text):
        self.text = text
