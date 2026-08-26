"""
Mathpal — Math Expression Renderer
====================================
Renders polynomial expressions with **pixel-font superscripts** on a
transparent ``pygame.Surface``.

The renderer tokenizes an expression string (e.g. ``'4x^3'``) into
segments and draws each one at the correct baseline or elevation.
Superscripts are rendered at **70 % font size** and positioned at
**40 % elevation** above the baseline.

Crucially, the renderer returns **per-token bounding rects** so that
the correction animation can grab and move individual parts of the
expression independently.
"""

import pygame

from config import Colors, FONT_SIZE_LARGE
from engine.ui_components import get_font


class MathToken:
    """A single renderable piece of a math expression."""

    __slots__ = ("text", "is_superscript", "surface", "rect")

    def __init__(self, text, is_superscript=False):
        self.text = text
        self.is_superscript = is_superscript
        self.surface = None            # Set during render
        self.rect = None               # pygame.Rect set during render


class MathRenderer:
    """Renders math expressions with superscripts and per-token metadata."""

    def __init__(self, base_size=None):
        size = base_size or FONT_SIZE_LARGE
        self.base_font = get_font(size, bold=True)
        self.sup_font = get_font(max(8, int(size * 0.7)), bold=True)
        self._base_h = self.base_font.get_linesize()
        self._sup_h = self.sup_font.get_linesize()

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------

    @staticmethod
    def tokenize(expr_str):
        """
        Split an expression like ``'4x^3'`` into :class:`MathToken` objects.

        ``^`` triggers superscript for the following run of digits / minus.

        Returns
        -------
        list[MathToken]
        """
        tokens = []
        i = 0
        n = len(expr_str)
        while i < n:
            if expr_str[i] == "^":
                i += 1
                sup = ""
                while i < n and (expr_str[i].isdigit() or expr_str[i] == "-"):
                    sup += expr_str[i]
                    i += 1
                if sup:
                    tokens.append(MathToken(sup, is_superscript=True))
            else:
                tokens.append(MathToken(expr_str[i]))
                i += 1
        return tokens

    # ------------------------------------------------------------------
    # Full expression render
    # ------------------------------------------------------------------

    def render(self, expr_str, color=None):
        """
        Render a full expression and return ``(surface, tokens, token_rects)``.

        Parameters
        ----------
        expr_str : str
            e.g. ``'4x^3'``, ``'12x^2'``
        color : tuple, optional
            RGB colour for the glyphs.

        Returns
        -------
        surface : pygame.Surface
            Transparent surface containing the rendered expression.
        tokens : list[MathToken]
            Token objects with their ``.surface`` and ``.rect`` populated.
        token_rects : dict[int, pygame.Rect]
            Mapping from token index → bounding rect on the surface.
        """
        color = color or Colors.TEXT_PRIMARY
        tokens = self.tokenize(expr_str)

        # --- First pass: render each glyph surface ----------------------
        for tok in tokens:
            font = self.sup_font if tok.is_superscript else self.base_font
            tok.surface = font.render(tok.text, False, color)

        # --- Measure total width and max height --------------------------
        total_w = sum(t.surface.get_width() for t in tokens)
        total_h = self._base_h + int(self._sup_h * 0.4)  # room for sups

        # --- Second pass: position each token ----------------------------
        surface = pygame.Surface((total_w + 2, total_h + 2), pygame.SRCALPHA)
        baseline_y = int(self._sup_h * 0.4)     # top margin for sups

        x = 0
        token_rects = {}
        for i, tok in enumerate(tokens):
            if tok.is_superscript:
                y = baseline_y - int(self._sup_h * 0.55)
            else:
                y = baseline_y
            tok.rect = pygame.Rect(x, y, tok.surface.get_width(),
                                   tok.surface.get_height())
            surface.blit(tok.surface, tok.rect.topleft)
            token_rects[i] = tok.rect.copy()
            x += tok.surface.get_width()

        return surface, tokens, token_rects

    # ------------------------------------------------------------------
    # Render single token (for animation)
    # ------------------------------------------------------------------

    def render_part(self, text, is_superscript=False, color=None):
        """Render a standalone text token as a ``pygame.Surface``."""
        color = color or Colors.TEXT_PRIMARY
        font = self.sup_font if is_superscript else self.base_font
        return font.render(text, False, color)
