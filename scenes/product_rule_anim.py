"""
Mathpal — Product Rule Kinetic Error Correction
=================================================
Kinetic visualizer that breaks down the Product Rule:
    d/dx[ (f)(g) ] = f'g + fg'

Phases
------
1. INTRO   — Highlights f in Cyan and g in Gold.
2. SPLIT   — Clones and splits into two branches: [ f' * g ] + [ f * g' ].
3. DERIVE  — Derives f -> f' and g -> g' in place.
4. EXPAND  — Multiplies out both polynomial components.
5. MERGE   — Slides both terms together and merges like terms into final sum.
6. DONE    — Ready to advance.
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


PHASE_INTRO  = 0
PHASE_SPLIT  = 1
PHASE_DERIVE = 2
PHASE_EXPAND = 3
PHASE_MERGE  = 4
PHASE_DONE   = 5


class ProductRuleCorrectionAnimation:
    """7-phase visualizer for Product Rule error correction."""

    def __init__(self, problem):
        self.problem = problem
        self.audio = AudioManager()
        self.mr = MathRenderer()
        self.small_font = get_font(FONT_SIZE_SMALL)
        self.med_font = get_font(FONT_SIZE_MEDIUM, bold=True)
        self.big_font = get_font(FONT_SIZE_LARGE, bold=True)

        self.phase = PHASE_INTRO
        self.phase_timer = 0.0
        self.total_time = 0.0
        self.center_x = INTERNAL_WIDTH // 2
        self.center_y = 110

        self.label_text = "Product Rule: d/dx( f \u00b7 g )"
        self._sparkles: list[_Sparkle] = []
        self._flash_alpha = 0.0

        # Term strings
        self.u_str = self.problem.u_str
        self.v_str = self.problem.v_str
        self.du_str = self.problem.du_str
        self.dv_str = self.problem.dv_str
        self.term1_str = self.problem.term1_str
        self.term2_str = self.problem.term2_str
        self.ans_str = self.problem.answer_str

        # Split positions
        self.split_progress = 0.0
        self.merge_progress = 0.0

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

        if self.phase == PHASE_INTRO:
            self.label_text = "Step 1: Identify factors ( f ) and ( g )"
            if self.phase_timer >= 1.2:
                self._advance()
                self.audio.play_sfx("split")

        elif self.phase == PHASE_SPLIT:
            self.split_progress = min(1.0, self.phase_timer / 1.0)
            self.label_text = "Step 2: Apply Formula:  [ f' \u00b7 g ] + [ f \u00b7 g' ]"
            if self.phase_timer >= 1.4:
                self._advance()
                self.audio.play_sfx("correct")

        elif self.phase == PHASE_DERIVE:
            self.label_text = f"Step 3: Derive each: ({self.u_str})'={self.du_str}, ({self.v_str})'={self.dv_str}"
            if self.phase_timer >= 1.5:
                self._advance()
                self.audio.play_sfx("slide")

        elif self.phase == PHASE_EXPAND:
            self.label_text = f"Step 4: Multiply out: {self.term1_str} + {self.term2_str}"
            if self.phase_timer >= 1.4:
                self._advance()
                self.audio.play_sfx("merge")
                self.audio.play_sfx("levelup")
                self._flash_alpha = 1.0
                for _ in range(25):
                    self._sparkles.append(_Sparkle(self.center_x, self.center_y))

        elif self.phase == PHASE_MERGE:
            self.merge_progress = min(1.0, self.phase_timer / 0.8)
            self.label_text = f"Final Answer:  {self.ans_str} !"
            if self.phase_timer >= 2.0:
                self._advance()

    def _advance(self):
        self.phase += 1
        self.phase_timer = 0.0

    def draw(self, surface):
        # Dark overlay
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))

        for sp in self._sparkles:
            sp.draw(surface)

        cy = self.center_y
        cx = self.center_x

        if self.phase == PHASE_INTRO:
            # Draw (f)(g) with colored factors
            f_surf, _, _ = self.mr.render(f"({self.u_str})", color=Colors.PROD_F_COLOR)
            g_surf, _, _ = self.mr.render(f"({self.v_str})", color=Colors.PROD_G_COLOR)
            total_w = f_surf.get_width() + g_surf.get_width() + 8
            sx = cx - total_w // 2
            surface.blit(f_surf, (sx, cy - 15))
            surface.blit(g_surf, (sx + f_surf.get_width() + 8, cy - 15))

            # Color tags under
            f_tag = self.small_font.render("f", False, Colors.PROD_F_COLOR)
            g_tag = self.small_font.render("g", False, Colors.PROD_G_COLOR)
            surface.blit(f_tag, (sx + f_surf.get_width() // 2 - 4, cy + 20))
            surface.blit(g_tag, (sx + f_surf.get_width() + 8 + g_surf.get_width() // 2 - 4, cy + 20))

        elif self.phase == PHASE_SPLIT:
            # Expanding branches: [f'g] + [fg']
            offset = int(60 * self.split_progress)
            # Left branch: (f')(g)
            t1_surf, _, _ = self.mr.render(f"[ ({self.u_str})'({self.v_str}) ]", color=Colors.PROD_DF_COLOR)
            # Plus
            plus_surf = self.med_font.render("+", False, Colors.PROD_PLUS)
            # Right branch: (f)(g')
            t2_surf, _, _ = self.mr.render(f"[ ({self.u_str})({self.v_str})' ]", color=Colors.PROD_DG_COLOR)

            surface.blit(t1_surf, (cx - offset - t1_surf.get_width(), cy - 15))
            surface.blit(plus_surf, (cx - plus_surf.get_width() // 2, cy - 8))
            surface.blit(t2_surf, (cx + offset, cy - 15))

        elif self.phase == PHASE_DERIVE:
            # Derived factors in place: [(du)(v)] + [(u)(dv)]
            t1_surf, _, _ = self.mr.render(f"[ ({self.du_str})({self.v_str}) ]", color=Colors.PROD_DF_COLOR)
            plus_surf = self.med_font.render("+", False, Colors.PROD_PLUS)
            t2_surf, _, _ = self.mr.render(f"[ ({self.u_str})({self.dv_str}) ]", color=Colors.PROD_DG_COLOR)

            offset = 60
            surface.blit(t1_surf, (cx - offset - t1_surf.get_width(), cy - 15))
            surface.blit(plus_surf, (cx - plus_surf.get_width() // 2, cy - 8))
            surface.blit(t2_surf, (cx + offset, cy - 15))

        elif self.phase == PHASE_EXPAND:
            # Multiplied: 12x^2 + 6x^2
            t1_surf, _, _ = self.mr.render(self.term1_str, color=Colors.PROD_DF_COLOR)
            plus_surf = self.med_font.render("+", False, Colors.PROD_PLUS)
            t2_surf, _, _ = self.mr.render(self.term2_str, color=Colors.PROD_DG_COLOR)

            offset = 40
            surface.blit(t1_surf, (cx - offset - t1_surf.get_width(), cy - 15))
            surface.blit(plus_surf, (cx - plus_surf.get_width() // 2, cy - 8))
            surface.blit(t2_surf, (cx + offset, cy - 15))

        elif self.phase >= PHASE_MERGE:
            # Merged glowing answer
            ans_surf, _, _ = self.mr.render(self.ans_str, color=Colors.CORRECT_GLOW)
            surface.blit(ans_surf, (cx - ans_surf.get_width() // 2, cy - 15))

            # Pulse underline
            pulse = 0.5 + 0.5 * math.sin(self.total_time * 5.0)
            line_w = int(ans_surf.get_width() + 40 * pulse)
            pygame.draw.line(surface, Colors.CORRECT_GLOW,
                             (cx - line_w // 2, cy + 22), (cx + line_w // 2, cy + 22), 2)

        # White flash overlay
        if self._flash_alpha > 0:
            flash = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self._flash_alpha * 120)))
            surface.blit(flash, (0, 0))

        # Bottom label
        if self.label_text:
            lbl = self.small_font.render(self.label_text, False, Colors.TEXT_SECONDARY)
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy + 65))

        # Prompt when done
        if self.phase == PHASE_DONE:
            if int(self.total_time * 3) % 2 == 0:
                prompt = self.small_font.render("Press SPACE to continue", False, Colors.TEXT_ACCENT)
                surface.blit(prompt, (cx - prompt.get_width() // 2, cy + 90))
