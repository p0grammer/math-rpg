"""
Mathpal — Visual Effects
=========================
Post-processing effects applied to the final display surface.

Current effects
---------------
* **CRT scanlines** — alternating semi-transparent dark horizontal lines
  that mimic the look of an old cathode-ray tube monitor.  The overlay is
  pre-rendered once and blitted every frame (very cheap).
"""

import pygame

from config import CRT_SCANLINE_ALPHA


class CRTEffect:
    """
    Mimics CRT scanlines by overlaying semi-transparent horizontal bars.

    The overlay is built once in ``__init__`` and then simply blitted onto
    the display each frame, so the per-frame cost is a single surface blit.
    """

    def __init__(self, width, height, alpha=None):
        """
        Parameters
        ----------
        width, height : int
            Dimensions of the **display** surface (post-upscale).
        alpha : int, optional
            Opacity of each scanline (0-255).  Defaults to
            ``CRT_SCANLINE_ALPHA`` from config.
        """
        if alpha is None:
            alpha = CRT_SCANLINE_ALPHA

        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        scanline_color = (0, 0, 0, alpha)

        # Draw a 1-px dark line on every other row
        for y in range(0, height, 2):
            pygame.draw.line(self.overlay, scanline_color,
                             (0, y), (width - 1, y))

    def apply(self, surface):
        """Blit the pre-rendered scanline overlay onto *surface*."""
        surface.blit(self.overlay, (0, 0))
