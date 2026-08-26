"""
Mathpal — RPG Text Box
========================
A Final Fantasy / Pokémon-style text box with:

* **Typewriter effect** — characters reveal one-by-one.
* **Speaker name tag** — in accent color above the border.
* **Message queue** — feed multiple messages; SPACE / ENTER advances.
* **Blinking prompt arrow** — ``▼`` when text is fully revealed.
* 3D beveled border matching the retro UI style.
* Automatic **word-wrapping** to fit within the box.
"""

import pygame

from config import (
    Colors,
    TEXTBOX_X, TEXTBOX_Y, TEXTBOX_WIDTH, TEXTBOX_HEIGHT,
    TEXTBOX_CHAR_SPEED, TEXTBOX_BEVEL, TEXTBOX_PADDING,
    FONT_SIZE_SMALL,
)
from engine.ui_components import get_font


class TextBox:
    """RPG text box with typewriter reveal and message queue."""

    def __init__(self, x=None, y=None, width=None, height=None):
        self.rect = pygame.Rect(
            x or TEXTBOX_X,
            y or TEXTBOX_Y,
            width or TEXTBOX_WIDTH,
            height or TEXTBOX_HEIGHT,
        )
        self.font = get_font(FONT_SIZE_SMALL)
        self.speaker_font = get_font(FONT_SIZE_SMALL, bold=True)

        self._messages: list[tuple[str, str]] = []    # (speaker, text)
        self._speaker = ""
        self._text = ""
        self._wrapped_lines: list[str] = []
        self._revealed = 0.0           # Float chars revealed so far
        self._finished = False         # Current message fully revealed?
        self._active = False           # Any message being displayed?
        self._prompt_timer = 0.0
        self._char_speed = TEXTBOX_CHAR_SPEED
        self._total_chars = 0          # Total chars across all wrapped lines

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_messages(self, messages):
        """
        Load a queue of ``(speaker, text)`` tuples.
        Immediately starts displaying the first one.
        """
        self._messages = list(messages)
        self._advance()

    @property
    def is_active(self):
        return self._active

    @property
    def all_done(self):
        return not self._active and len(self._messages) == 0

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        """
        Process SPACE / ENTER.

        Returns
        -------
        bool
            ``True`` when **all** messages in the queue have been read.
        """
        if not self._active:
            return False

        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE, pygame.K_RETURN
        ):
            if self._finished:
                self._advance()
                return not self._active     # True = queue exhausted
            else:
                # Skip typewriter — reveal everything at once
                self._revealed = self._total_chars
                self._finished = True
        return False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        if self._active and not self._finished:
            self._revealed += self._char_speed * dt
            if self._revealed >= self._total_chars:
                self._revealed = self._total_chars
                self._finished = True
        self._prompt_timer += dt

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        if not self._active:
            return

        r = self.rect
        bv = TEXTBOX_BEVEL
        pad = TEXTBOX_PADDING

        # --- Speaker name tag (above the box) ----------------------------
        if self._speaker:
            tag_surf = self.speaker_font.render(
                self._speaker, False, Colors.SPEAKER_NAME,
            )
            surface.blit(tag_surf, (r.x + pad + 2, r.y - tag_surf.get_height() - 2))

        # --- Box border (beveled) ----------------------------------------
        # Top / left (light)
        pygame.draw.rect(surface, Colors.TEXTBOX_BORDER,
                         (r.x, r.y, r.w, bv))
        pygame.draw.rect(surface, Colors.TEXTBOX_BORDER,
                         (r.x, r.y, bv, r.h))
        # Bottom / right (darker)
        darker = tuple(max(0, c - 30) for c in Colors.TEXTBOX_BORDER)
        pygame.draw.rect(surface, darker,
                         (r.x, r.y + r.h - bv, r.w, bv))
        pygame.draw.rect(surface, darker,
                         (r.x + r.w - bv, r.y, bv, r.h))
        # Fill
        pygame.draw.rect(surface, Colors.TEXTBOX_BG,
                         (r.x + bv, r.y + bv,
                          r.w - 2 * bv, r.h - 2 * bv))

        # --- Revealed text (word-wrapped) --------------------------------
        inner_x = r.x + bv + pad
        inner_y = r.y + bv + pad
        line_h = self.font.get_linesize() + 2
        chars_left = int(self._revealed)

        for line in self._wrapped_lines:
            if chars_left <= 0:
                break
            visible = line[:chars_left]
            chars_left -= len(line)
            line_surf = self.font.render(visible, False, Colors.TEXT_PRIMARY)
            surface.blit(line_surf, (inner_x, inner_y))
            inner_y += line_h

        # --- Blinking ▼ prompt -------------------------------------------
        if self._finished:
            if int(self._prompt_timer * 3) % 2 == 0:
                arrow = self.font.render("\u25BC", False, Colors.TEXT_ACCENT)
                surface.blit(arrow,
                             (r.x + r.w - bv - pad - arrow.get_width(),
                              r.y + r.h - bv - pad - arrow.get_height()))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _advance(self):
        """Pop the next message or deactivate."""
        if self._messages:
            self._speaker, self._text = self._messages.pop(0)
            self._wrapped_lines = self._word_wrap(self._text)
            self._total_chars = sum(len(ln) for ln in self._wrapped_lines)
            self._revealed = 0.0
            self._finished = False
            self._active = True
            self._prompt_timer = 0.0
        else:
            self._active = False

    def _word_wrap(self, text):
        """Split *text* into lines that fit inside the text box."""
        max_w = (self.rect.w - 2 * TEXTBOX_BEVEL - 2 * TEXTBOX_PADDING)
        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            test = f"{current} {word}".strip()
            tw, _ = self.font.size(test)
            if tw <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
