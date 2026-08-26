"""
Mathpal — Game Core
====================
The central ``Game`` class owns the Pygame display, the 60 FPS game loop,
and the state machine.  Everything else plugs in via states (scenes).

Loop order each frame
---------------------
1. ``clock.tick(FPS)`` → compute *dt*
2. Poll ``pygame.event`` → forward each to the active state
3. ``state.update(dt)``
4. Clear internal surface → ``state.draw(surface)``
5. ``renderer.present()`` (nearest-neighbor upscale)
6. ``crt.apply()`` (scanline overlay, if enabled)
7. ``pygame.display.flip()``
"""

import sys
import pygame

from config import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    DISPLAY_WIDTH, DISPLAY_HEIGHT,
    FPS, TITLE,
    CRT_ENABLED_DEFAULT,
    AUDIO_SAMPLE_RATE,
    Colors,
)
from engine.renderer import Renderer
from engine.audio import AudioManager
from engine.effects import CRTEffect
from logic.settings_manager import SettingsManager


class Game:
    """Top-level application object.  Create one, call ``run()``."""

    def __init__(self):
        # --- Pygame init -------------------------------------------------
        pygame.init()
        pygame.mixer.init(
            frequency=AUDIO_SAMPLE_RATE,
            size=-16,
            channels=2,
            buffer=512,
        )

        self.display = pygame.display.set_mode(
            (DISPLAY_WIDTH, DISPLAY_HEIGHT),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(f"\u2605 {TITLE} \u2605  —  Learn Math. Level Up.")

        # --- Settings & State --------------------------------------------
        self.settings = SettingsManager()

        # --- Sub-systems -------------------------------------------------
        self.renderer = Renderer(INTERNAL_WIDTH, INTERNAL_HEIGHT, self.display)
        self.audio = AudioManager()
        self.audio.set_bgm_volume(self.settings.bgm_volume)
        self.audio.set_sfx_volume(self.settings.sfx_volume)
        self.crt = CRTEffect(DISPLAY_WIDTH, DISPLAY_HEIGHT)

        # --- State -------------------------------------------------------
        self.clock = pygame.time.Clock()
        self.running = True
        self.crt_enabled = self.settings.crt_enabled
        self._state = None

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def change_state(self, new_state):
        """
        Swap the active scene.  Calls ``exit()`` on the old state and
        ``enter()`` on the new one.
        """
        if self._state is not None:
            self._state.exit()
        self._state = new_state
        self._state.enter()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Enter the main loop.  Blocks until ``self.running`` is ``False``."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0   # Seconds since last frame

            # ---- Events ------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                elif self._state is not None:
                    self._state.handle_event(event)

            # ---- Update ------------------------------------------------
            if self._state is not None:
                self._state.update(dt)

            # ---- Draw --------------------------------------------------
            surface = self.renderer.get_surface()
            surface.fill(Colors.BLACK)

            if self._state is not None:
                self._state.draw(surface)

            self.renderer.present()

            if self.crt_enabled:
                self.crt.apply(self.display)

            pygame.display.flip()

        # ---- Shutdown --------------------------------------------------
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _handle_resize(self, new_w, new_h):
        """Recreate renderer and CRT overlay when the window is resized."""
        self.display = pygame.display.set_mode(
            (new_w, new_h), pygame.RESIZABLE
        )
        self.renderer = Renderer(
            INTERNAL_WIDTH, INTERNAL_HEIGHT, self.display
        )
        self.crt = CRTEffect(new_w, new_h)
