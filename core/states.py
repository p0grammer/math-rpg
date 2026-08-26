"""
Mathpal — State Machine
========================
Abstract base class for all game states (scenes). Each state owns its own
handle_event / update / draw lifecycle, and the Game class switches between
them via a simple state-swap (no stack needed for Step 1).
"""

from abc import ABC, abstractmethod


class State(ABC):
    """Base class for every game scene (menu, play, boss, results, etc.)."""

    def __init__(self, game):
        """
        Parameters
        ----------
        game : core.game.Game
            Back-reference to the owning Game instance for accessing the
            renderer, audio manager, and triggering state transitions.
        """
        self.game = game

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def enter(self):
        """Called once when this state becomes the active state."""
        pass

    def exit(self):
        """Called once when this state is being replaced by another."""
        pass

    # ------------------------------------------------------------------
    # Per-frame callbacks
    # ------------------------------------------------------------------

    @abstractmethod
    def handle_event(self, event):
        """
        Process a single ``pygame.event.Event``.

        The Game loop iterates all events and forwards each one here.
        """
        pass

    @abstractmethod
    def update(self, dt):
        """
        Advance game logic by *dt* seconds (float, typically ~0.0167 at 60 FPS).
        """
        pass

    @abstractmethod
    def draw(self, surface):
        """
        Render this state onto *surface* (the internal-resolution canvas).

        The renderer will scale it up to the display window afterwards.
        """
        pass
