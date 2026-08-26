"""
Mathpal — Renderer
===================
Manages a low-resolution internal surface and scales it up to the display
window using nearest-neighbor interpolation. This is the single trick that
gives the entire app its authentic retro pixel-art look.

Internal resolution : 480 × 360
Display resolution  : 1440 × 1080  (3× scale)
"""

import pygame


class Renderer:
    """Owns the internal canvas and handles upscaling to the OS window."""

    def __init__(self, internal_w, internal_h, display_surface):
        """
        Parameters
        ----------
        internal_w, internal_h : int
            Pixel dimensions of the low-resolution canvas.
        display_surface : pygame.Surface
            The actual OS window surface (high-res).
        """
        self.internal_surface = pygame.Surface((internal_w, internal_h))
        self.display = display_surface
        self._display_size = display_surface.get_size()
        self._scale_x = internal_w / self._display_size[0]
        self._scale_y = internal_h / self._display_size[1]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_surface(self):
        """Return the low-res surface that scenes should draw onto."""
        return self.internal_surface

    def present(self):
        """Scale the internal surface up and blit it onto the display."""
        scaled = pygame.transform.scale(self.internal_surface, self._display_size)
        self.display.blit(scaled, (0, 0))

    def screen_to_internal(self, screen_pos):
        """
        Convert display-space mouse coordinates to internal-surface coordinates.

        Parameters
        ----------
        screen_pos : tuple[int, int]
            (x, y) from a ``pygame.event`` in display-pixel space.

        Returns
        -------
        tuple[int, int]
            Corresponding (x, y) on the internal surface.
        """
        return (int(screen_pos[0] * self._scale_x),
                int(screen_pos[1] * self._scale_y))
