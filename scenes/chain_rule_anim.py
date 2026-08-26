"""
Mathpal — Chain Rule Kinetic Error Correction Animation
=========================================================
Bespoke visualizer for the Chain Rule (Level 5 Boss: The Chain Golem):
    d/dx[ f(g(x)) ] = f'(g(x)) * g'(x)

Phases
------
1. IDENTIFY — Highlights outer shell power in Cyan and inner core in Gold.
2. OUTER    — Derives outer shell while leaving inner core untouched.
3. EXTRACT  — Detaches the inner core to find its derivative.
4. DERIVE   — Evaluates derivative of inside term.
5. COMBINE  — Multiplies outer coefficient by inner derivative into final answer.
6. DONE     — Complete.
"""

import math
import random
import pygame

from config import (
    Colors,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
)
from engine.ui_components import get_font
from engine.math_renderer import MathRenderer
from engine.audio import AudioManager


class _Sparkle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color")

    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-80, 80)
        self.vy = random.uniform(-90, -10)
        self.life = random.uniform(0.3, 0.7)
        self.max_life = self.life
        self.size = random.randint(1, 3)
        self.color = color or Colors.SPARKLE

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120 * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        c = tuple(int(ch * ratio) for ch in self.color)
        pygame.draw.rect(surface, c, (int(self.x), int(self.y), self.size, self.size))


PHASE_IDENTIFY = 0
PHASE_OUTER    = 1
PHASE_EXTRACT  = 2
PHASE_DERIVE   = 3
PHASE_COMBINE  = 4
PHASE_DONE     = 5


class ChainRuleCorrectionAnimation:
    """Kinetic visualizer for nested Chain Rule derivatives."""

    def __init__(self, problem):
        self.problem = problem
        self.audio = AudioManager()
        self.mr = MathRenderer()
        self.small_font = get_font(FONT_SIZE_SMALL)
        self.med_font   = get_font(FONT_SIZE_MEDIUM, bold=True)
        self.big_font   = get_font(FONT_SIZE_LARGE, bold=True)

        self.phase = PHASE_IDENTIFY
        self.phase_timer = 0.0
        self.total_time = 0.0
        self.center_x = INTERNAL_WIDTH // 2
        self.center_y = 110

        self.label_text = "Chain Rule: d/dx[ f(g(x)) ]"
        self._sparkles: list[_Sparkle] = []
        self._flash_alpha = 0.0

        # Raw problem parameters
        raw = self.problem.raw_data
        self.a = raw.get("a", 3)
        self.b = raw.get("b", 2)
        self.n = raw.get("n", 4)
        self.front_c = raw.get("front_c", self.a * self.n)
        self.exp_minus_1 = self.n - 1

        self.inner_str = f"{self.a}x+{self.b}"
        self.ans_str = self.problem.answer_str

    @property
    def is_complete(self):
        return self.phase == PHASE_DONE

    def update(self, dt):
        self.phase_timer += dt
        self.total_time += dt

        for sp in self._sparkles:
            sp.update(dt)
        self._sparkles = [s for s in self._sparkles if s.life > 0]
        self._flash_alpha = max(0.0, self._flash_alpha - dt * 2.5)

        if self.phase == PHASE_IDENTIFY:
            self.label_text = f"Step 1: Outer power is ({self.n}), Inner is ({self.inner_str})"
            if self.phase_timer >= 1.3:
                self._advance()
                self.audio.play_sfx("crack")

        elif self.phase == PHASE_OUTER:
            self.label_text = f"Step 2: Derive outer power -> {self.n}({self.inner_str})^{self.exp_minus_1}"
            if self.phase_timer >= 1.5:
                self._advance()
                self.audio.play_sfx("split")

        elif self.phase == PHASE_EXTRACT:
            self.label_text = f"Step 3: Multiply by derivative of inside: d/dx({self.inner_str})"
            if self.phase_timer >= 1.4:
                self._advance()
                self.audio.play_sfx("correct")

        elif self.phase == PHASE_DERIVE:
            self.label_text = f"Step 4: Inside derivative = {self.a}  ->  {self.n} * {self.a} = {self.front_c}"
            if self.phase_timer >= 1.5:
                self._advance()
                self.audio.play_sfx("merge")
                self.audio.play_sfx("levelup")
                self._flash_alpha = 1.0
                for _ in range(30):
                    self._sparkles.append(_Sparkle(self.center_x, self.center_y, Colors.GOLEM_MOLTEN_CORE))

        elif self.phase == PHASE_COMBINE:
            self.label_text = f"Final Derivative:  {self.ans_str} !"
            if self.phase_timer >= 2.0:
                self._advance()

    def _advance(self):
        self.phase += 1
        self.phase_timer = 0.0

    def draw(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))

        for sp in self._sparkles:
            sp.draw(surface)

        cx, cy = self.center_x, self.center_y

        if self.phase == PHASE_IDENTIFY:
            # Draw (3x+2)^4 with inner highlighted
            outer_left = self.mr.render_part("(", color=Colors.NEON_CYAN)
            inner_surf = self.mr.render_part(self.inner_str, color=Colors.GOLEM_MOLTEN_CORE)
            outer_right = self.mr.render_part(f")^{self.n}", color=Colors.NEON_CYAN)

            total_w = outer_left.get_width() + inner_surf.get_width() + outer_right.get_width()
            sx = cx - total_w // 2
            surface.blit(outer_left, (sx, cy - 15))
            surface.blit(inner_surf, (sx + outer_left.get_width(), cy - 15))
            surface.blit(outer_right, (sx + outer_left.get_width() + inner_surf.get_width(), cy - 15))

        elif self.phase == PHASE_OUTER:
            # 4(3x+2)^3
            txt = f"{self.n}({self.inner_str})^{self.exp_minus_1}"
            s, _, _ = self.mr.render(txt, color=Colors.NEON_CYAN)
            surface.blit(s, (cx - s.get_width() // 2, cy - 15))

        elif self.phase == PHASE_EXTRACT:
            # 4(3x+2)^3 * d/dx(3x+2)
            txt = f"{self.n}({self.inner_str})^{self.exp_minus_1} \u00b7 [d/dx({self.inner_str})]"
            s, _, _ = self.mr.render(txt, color=Colors.ELECTRIC_YELLOW)
            surface.blit(s, (cx - s.get_width() // 2, cy - 15))

        elif self.phase == PHASE_DERIVE:
            # 4(3x+2)^3 * 3
            txt = f"{self.n}({self.inner_str})^{self.exp_minus_1} \u00b7 ({self.a})"
            s, _, _ = self.mr.render(txt, color=Colors.GOLEM_MOLTEN_CORE)
            surface.blit(s, (cx - s.get_width() // 2, cy - 15))

        elif self.phase >= PHASE_COMBINE:
            # Final simplified glowing derivative
            s, _, _ = self.mr.render(self.ans_str, color=Colors.CORRECT_GLOW)
            surface.blit(s, (cx - s.get_width() // 2, cy - 15))

            pulse = 0.5 + 0.5 * math.sin(self.total_time * 5.0)
            line_w = int(s.get_width() + 40 * pulse)
            pygame.draw.line(surface, Colors.CORRECT_GLOW,
                             (cx - line_w // 2, cy + 22), (cx + line_w // 2, cy + 22), 2)

        if self._flash_alpha > 0:
            flash = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self._flash_alpha * 120)))
            surface.blit(flash, (0, 0))

        if self.label_text:
            lbl = self.small_font.render(self.label_text, False, Colors.TEXT_SECONDARY)
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy + 65))

        if self.phase == PHASE_DONE:
            if int(self.total_time * 3) % 2 == 0:
                prompt = self.small_font.render("Press SPACE to continue", False, Colors.TEXT_ACCENT)
                surface.blit(prompt, (cx - prompt.get_width() // 2, cy + 90))
