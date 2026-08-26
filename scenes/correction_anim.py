"""
Mathpal — Kinetic Error Correction Animation
==============================================
The app's **killer feature**.  When a student gets a Power Rule problem
wrong, this animation visually deconstructs the solution in 7 cinematic
phases:

1. **DISPLAY**   — Show the original expression, pulsing.
2. **DETACH**    — The exponent shakes violently, cracks appear.
3. **FALL**      — The exponent detaches and falls with *simulated gravity*,
                   bouncing off a ground line with decreasing amplitude.
4. **MULTIPLY**  — The exponent slides left to sit beside the coefficient;
                   a retro ``×`` fades in.
5. **COMPUTE**   — ``coeff × exp`` flashes and morphs into the product,
                   with pixel-sparkle particles.
6. **TICK_DOWN** — The original exponent slot ticks like a retro departure
                   board: ``3 → 2``.
7. **RESULT**    — The final derivative assembles and pulses with neon glow.

Physics
-------
The falling exponent uses a simple Euler integration with configurable
gravity, damping, and bounce threshold from ``config.py``.
"""

import math
import random

import pygame

from config import (
    Colors,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    CORRECTION_GRAVITY, CORRECTION_DAMPING, CORRECTION_BOUNCE_THRESHOLD,
    CORR_T_DISPLAY, CORR_T_DETACH, CORR_T_FALL,
    CORR_T_MULTIPLY, CORR_T_COMPUTE, CORR_T_TICK, CORR_T_RESULT,
    FONT_SIZE_LARGE, FONT_SIZE_SMALL, FONT_SIZE_MEDIUM,
)
from engine.ui_components import get_font
from engine.math_renderer import MathRenderer
from engine.audio import AudioManager


# ======================================================================
# Sparkle particle
# ======================================================================

class _Sparkle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size")

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-70, 70)
        self.vy = random.uniform(-90, -20)
        self.life = random.uniform(0.3, 0.7)
        self.max_life = self.life
        self.size = random.randint(1, 3)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120 * dt          # light gravity on sparkles
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha_ratio = self.life / self.max_life
        c = int(255 * alpha_ratio)
        color = (c, c, int(c * 0.7))
        pygame.draw.rect(surface, color,
                         (int(self.x), int(self.y), self.size, self.size))


# ======================================================================
# Phase enum
# ======================================================================

PHASE_DISPLAY  = 0
PHASE_DETACH   = 1
PHASE_FALL     = 2
PHASE_MULTIPLY = 3
PHASE_COMPUTE  = 4
PHASE_TICK     = 5
PHASE_RESULT   = 6
PHASE_DONE     = 7


# ======================================================================
# Correction Animation
# ======================================================================

class CorrectionAnimation:
    """
    7-phase kinetic animation that visually deconstructs a Power Rule
    derivative step-by-step.

    Parameters
    ----------
    problem : logic.math_generator.PowerRuleProblem
    """

    def __init__(self, problem):
        self.problem = problem
        self.audio = AudioManager()
        self.mr = MathRenderer()
        self.label_font = get_font(FONT_SIZE_SMALL)
        self.big_font = get_font(FONT_SIZE_LARGE, bold=True)
        self.med_font = get_font(FONT_SIZE_MEDIUM, bold=True)

        # Phase machine
        self.phase = PHASE_DISPLAY
        self.phase_timer = 0.0
        self.total_time = 0.0

        # --- Layout (centered in upper screen area) ---------------------
        self.center_x = INTERNAL_WIDTH // 2
        self.center_y = 105

        # --- Pre-render individual expression parts ---------------------
        self.coeff_text = str(problem.coefficient)
        self.var_text = problem.variable
        self.exp_text = str(problem.exponent)

        self.coeff_surf = self.mr.render_part(self.coeff_text, color=Colors.TEXT_PRIMARY)
        self.var_surf = self.mr.render_part(self.var_text, color=Colors.TEXT_PRIMARY)
        self.exp_surf = self.mr.render_part(self.exp_text, is_superscript=True,
                                            color=Colors.ELECTRIC_YELLOW)

        # Compute positions so expression is centered
        total_w = (self.coeff_surf.get_width() +
                   self.var_surf.get_width() +
                   self.exp_surf.get_width())
        self.base_x = self.center_x - total_w // 2
        self.coeff_x = self.base_x
        self.var_x = self.coeff_x + self.coeff_surf.get_width()
        self.exp_origin_x = float(self.var_x + self.var_surf.get_width())
        self.exp_origin_y = float(self.center_y - self.exp_surf.get_height())

        self.base_y = self.center_y    # baseline for normal text

        # --- Animated exponent position (mutable) -----------------------
        self.exp_x = self.exp_origin_x
        self.exp_y = self.exp_origin_y
        self.exp_vx = 0.0
        self.exp_vy = 0.0

        # Ground line for bouncing
        self.ground_y = self.center_y + 50.0

        # --- Phase-specific state ---------------------------------------
        self.shake_offset = (0, 0)
        self.bounce_count = 0
        self._fall_settled = False

        # Multiply phase
        self._multiply_start_x = 0.0
        self._multiply_start_y = 0.0
        self._multiply_target_x = 0.0
        self._multiply_target_y = 0.0
        self._multiply_alpha = 0

        # Compute phase
        self.result_coeff_text = str(problem.answer_coefficient)
        self.result_coeff_surf = self.mr.render_part(
            self.result_coeff_text, color=Colors.CORRECT_GLOW
        )
        self._sparkles: list[_Sparkle] = []
        self._compute_flash = 0.0

        # Tick-down phase
        self._tick_value = problem.exponent
        self._tick_progress = 0.0

        # Result phase
        self.result_exp_text = str(problem.answer_exponent)
        self._result_glow = 0.0

        # Labels
        self.label_text = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_complete(self):
        return self.phase == PHASE_DONE

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        self.phase_timer += dt
        self.total_time += dt

        # Update sparkles regardless of phase
        for sp in self._sparkles:
            sp.update(dt)
        self._sparkles = [s for s in self._sparkles if s.life > 0]

        dispatch = {
            PHASE_DISPLAY:  self._update_display,
            PHASE_DETACH:   self._update_detach,
            PHASE_FALL:     self._update_fall,
            PHASE_MULTIPLY: self._update_multiply,
            PHASE_COMPUTE:  self._update_compute,
            PHASE_TICK:     self._update_tick,
            PHASE_RESULT:   self._update_result,
        }
        fn = dispatch.get(self.phase)
        if fn:
            fn(dt)

    def _advance(self):
        self.phase += 1
        self.phase_timer = 0.0

    # --- Phase updates --------------------------------------------------

    def _update_display(self, dt):
        self.label_text = "Watch carefully..."
        if self.phase_timer >= CORR_T_DISPLAY:
            self._advance()
            self.audio.play_sfx("crack")

    def _update_detach(self, dt):
        self.label_text = ""
        # Violent shaking
        intensity = min(3, int(self.phase_timer * 8))
        self.shake_offset = (
            random.randint(-intensity, intensity),
            random.randint(-intensity, intensity),
        )
        if self.phase_timer >= CORR_T_DETACH:
            self._advance()
            self.shake_offset = (0, 0)
            # Launch exponent with a slight upward-left kick
            self.exp_vx = random.uniform(-25, -10)
            self.exp_vy = -100.0

    def _update_fall(self, dt):
        # Gravity
        self.exp_vy += CORRECTION_GRAVITY * dt
        self.exp_x += self.exp_vx * dt
        self.exp_y += self.exp_vy * dt

        # Bounce off ground
        if self.exp_y >= self.ground_y:
            self.exp_y = self.ground_y
            self.exp_vy *= -CORRECTION_DAMPING
            self.exp_vx *= 0.7
            self.bounce_count += 1
            if self.bounce_count <= 3:
                self.audio.play_sfx("bounce")

            if abs(self.exp_vy) < CORRECTION_BOUNCE_THRESHOLD:
                self.exp_vy = 0
                self.exp_y = self.ground_y
                self._fall_settled = True

        if self.phase_timer >= CORR_T_FALL:
            self._advance()
            self.audio.play_sfx("slide")
            # Save start position for lerp
            self._multiply_start_x = self.exp_x
            self._multiply_start_y = self.exp_y
            # Target: right of the coefficient, on the baseline
            self._multiply_target_x = float(
                self.coeff_x + self.coeff_surf.get_width() + 20
            )
            self._multiply_target_y = float(
                self.base_y - self.coeff_surf.get_height() + 4
            )

    def _update_multiply(self, dt):
        # Smoothstep lerp toward target
        t = min(1.0, self.phase_timer / (CORR_T_MULTIPLY * 0.7))
        t = t * t * (3.0 - 2.0 * t)   # smoothstep

        self.exp_x = self._lerp(self._multiply_start_x,
                                self._multiply_target_x, t)
        self.exp_y = self._lerp(self._multiply_start_y,
                                self._multiply_target_y, t)

        # Fade in × sign
        self._multiply_alpha = min(255,
                                   int(self.phase_timer / CORR_T_MULTIPLY * 255))

        c = self.problem.coefficient
        e = self.problem.exponent
        self.label_text = f"{c}  \u00d7  {e}  =  ?"

        if self.phase_timer >= CORR_T_MULTIPLY:
            self._advance()
            self.audio.play_sfx("correct")
            # Spawn sparkles around the multiplication area
            spark_cx = (self.coeff_x + self._multiply_target_x) / 2 + 10
            spark_cy = self._multiply_target_y
            for _ in range(18):
                self._sparkles.append(_Sparkle(spark_cx, spark_cy))

    def _update_compute(self, dt):
        self._compute_flash = max(0, 1.0 - self.phase_timer * 2.5)
        c = self.problem.coefficient
        e = self.problem.exponent
        self.label_text = f"{c}  \u00d7  {e}  =  {c * e}"

        if self.phase_timer >= CORR_T_COMPUTE:
            self._advance()
            self.audio.play_sfx("tick")
            self._tick_value = self.problem.exponent
            self._tick_progress = 0.0

    def _update_tick(self, dt):
        self._tick_progress = min(1.0, self.phase_timer / CORR_T_TICK)
        # Tick from old exponent to new
        if self._tick_progress >= 0.5 and self._tick_value != self.problem.answer_exponent:
            self._tick_value = self.problem.answer_exponent
            self.audio.play_sfx("tick")

        e = self.problem.exponent
        ne = self.problem.answer_exponent
        self.label_text = f"Exponent:  {e}  \u2192  {e} \u2212 1  =  {ne}"

        if self.phase_timer >= CORR_T_TICK:
            self._advance()
            self.audio.play_sfx("levelup")
            # Spawn celebration sparkles
            for _ in range(24):
                self._sparkles.append(
                    _Sparkle(self.center_x + random.randint(-60, 60),
                             self.center_y + 70)
                )

    def _update_result(self, dt):
        self._result_glow = 0.5 + 0.5 * math.sin(self.total_time * 5.0)
        ans = self.problem.answer_str
        expr = self.problem.expression_str
        self.label_text = f"d/dx( {expr} )  =  {ans}  !"

        if self.phase_timer >= CORR_T_RESULT:
            self._advance()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        # --- Semi-transparent overlay ------------------------------------
        overlay = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # --- Sparkles (behind everything) --------------------------------
        for sp in self._sparkles:
            sp.draw(surface)

        # --- Phase-specific rendering ------------------------------------
        if self.phase <= PHASE_FALL:
            self._draw_expression_with_falling_exp(surface)
        elif self.phase == PHASE_MULTIPLY:
            self._draw_multiply_phase(surface)
        elif self.phase == PHASE_COMPUTE:
            self._draw_compute_phase(surface)
        elif self.phase == PHASE_TICK:
            self._draw_tick_phase(surface)
        elif self.phase >= PHASE_RESULT:
            self._draw_result_phase(surface)

        # --- Ground line (phases 2-4) ------------------------------------
        if PHASE_FALL <= self.phase <= PHASE_MULTIPLY:
            gy = int(self.ground_y) + self.exp_surf.get_height() + 2
            pygame.draw.line(surface, Colors.TEXT_DIM,
                             (self.center_x - 80, gy),
                             (self.center_x + 80, gy), 1)

        # --- Label text at bottom ----------------------------------------
        if self.label_text:
            lbl = self.label_font.render(
                self.label_text, False, Colors.TEXT_SECONDARY
            )
            surface.blit(lbl,
                         (self.center_x - lbl.get_width() // 2,
                          self.center_y + 80))

        # --- "Press SPACE" prompt when done ------------------------------
        if self.phase == PHASE_DONE:
            if int(self.total_time * 3) % 2 == 0:
                prompt = self.label_font.render(
                    "Press SPACE to continue", False, Colors.TEXT_ACCENT
                )
                surface.blit(prompt,
                             (self.center_x - prompt.get_width() // 2,
                              self.center_y + 100))

    # --- Phase draw helpers ---------------------------------------------

    def _draw_expression_with_falling_exp(self, surface):
        """Phases 0-2: expression with the exponent at its animated position."""
        by = self.base_y - self.coeff_surf.get_height()

        # Coefficient
        surface.blit(self.coeff_surf, (self.coeff_x, by))
        # Variable
        surface.blit(self.var_surf, (self.var_x, by))

        # Exponent (animated position + shake)
        ex = int(self.exp_x) + self.shake_offset[0]
        ey = int(self.exp_y) + self.shake_offset[1]
        surface.blit(self.exp_surf, (ex, ey))

        # "?" in original slot during FALL phase
        if self.phase == PHASE_FALL:
            q_surf = self.mr.render_part("?", is_superscript=True,
                                         color=Colors.NEON_PINK)
            if int(self.total_time * 4) % 2 == 0:
                surface.blit(q_surf, (int(self.exp_origin_x),
                                       int(self.exp_origin_y)))

        # Pulsing outline during DISPLAY phase
        if self.phase == PHASE_DISPLAY:
            pulse = 0.5 + 0.5 * math.sin(self.total_time * 4)
            c = int(60 + 40 * pulse)
            total_w = (self.coeff_surf.get_width() +
                       self.var_surf.get_width() +
                       self.exp_surf.get_width() + 6)
            pygame.draw.rect(surface, (c, c, int(c * 1.5)),
                             (self.coeff_x - 3, by - 3,
                              total_w, self.coeff_surf.get_height() + 6), 1)

    def _draw_multiply_phase(self, surface):
        """Phase 3: exponent slides next to coefficient, × fades in."""
        by = self.base_y - self.coeff_surf.get_height()

        # Coefficient (static)
        surface.blit(self.coeff_surf, (self.coeff_x, by))

        # × sign (fading in)
        times_surf = self.big_font.render("\u00d7", False, Colors.NEON_CYAN)
        times_x = self.coeff_x + self.coeff_surf.get_width() + 6
        times_alpha_surf = times_surf.copy()
        times_alpha_surf.set_alpha(self._multiply_alpha)
        surface.blit(times_alpha_surf, (times_x, by))

        # Exponent (sliding toward target)
        surface.blit(self.exp_surf, (int(self.exp_x), int(self.exp_y)))

        # Variable + original exponent slot (dimmed, in background)
        dim_var = self.mr.render_part(self.var_text, color=Colors.TEXT_DIM)
        dim_q = self.mr.render_part("?", is_superscript=True, color=Colors.TEXT_DIM)
        surface.blit(dim_var, (self.var_x, by))
        surface.blit(dim_q, (int(self.exp_origin_x), int(self.exp_origin_y)))

    def _draw_compute_phase(self, surface):
        """Phase 4: multiplication result flashes in."""
        by = self.base_y - self.coeff_surf.get_height()

        # Flash overlay
        if self._compute_flash > 0:
            flash_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                                        pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, int(self._compute_flash * 100)))
            surface.blit(flash_surf, (0, 0))

        # Show the computed coefficient
        surface.blit(self.result_coeff_surf,
                     (self.center_x - self.result_coeff_surf.get_width() // 2,
                      by))

        # Dimmed variable + exponent slot
        dim_var = self.mr.render_part(self.var_text, color=Colors.TEXT_DIM)
        dim_q = self.mr.render_part("?", is_superscript=True, color=Colors.TEXT_DIM)
        rv_x = self.center_x + self.result_coeff_surf.get_width() // 2
        surface.blit(dim_var, (rv_x, by))
        surface.blit(dim_q,
                     (rv_x + dim_var.get_width(),
                      int(self.exp_origin_y)))

    def _draw_tick_phase(self, surface):
        """Phase 5: exponent slot ticks down like a departure board."""
        by = self.base_y - self.coeff_surf.get_height()

        # Result coefficient (green)
        surface.blit(self.result_coeff_surf,
                     (self.center_x - self.result_coeff_surf.get_width() // 2,
                      by))

        # Variable
        rv_x = self.center_x + self.result_coeff_surf.get_width() // 2
        surface.blit(self.var_surf, (rv_x, by))

        # Ticking exponent — clip vertically to simulate flap board
        tick_str = str(self._tick_value)
        tick_surf = self.mr.render_part(tick_str, is_superscript=True,
                                        color=Colors.ELECTRIC_YELLOW)

        exp_draw_x = rv_x + self.var_surf.get_width()
        exp_draw_y = int(self.exp_origin_y)

        # During transition, add a vertical "roll" offset
        if self._tick_progress < 0.5:
            roll = int(math.sin(self._tick_progress * math.pi * 4) * 3)
        else:
            roll = 0
        surface.blit(tick_surf, (exp_draw_x, exp_draw_y + roll))

        # Bracket decoration around the ticking digit
        bracket_color = Colors.NEON_CYAN if self._tick_progress < 0.5 else Colors.CORRECT_GLOW
        bw = tick_surf.get_width() + 6
        bh = tick_surf.get_height() + 4
        pygame.draw.rect(surface, bracket_color,
                         (exp_draw_x - 3, exp_draw_y - 2, bw, bh), 1)

    def _draw_result_phase(self, surface):
        """Phase 6: final answer glows and assembles."""
        by = self.base_y - self.coeff_surf.get_height()

        # Glow effect: render answer with pulsing color
        glow = self._result_glow
        gr = int(100 + 155 * glow)
        gg = int(255)
        gb = int(150 + 105 * glow)
        glow_color = (min(255, gr), gg, min(255, gb))

        # Render full answer expression
        answer_str = self.problem.answer_str
        ans_surf, _, _ = self.mr.render(answer_str, color=glow_color)

        ax = self.center_x - ans_surf.get_width() // 2
        ay = by
        surface.blit(ans_surf, (ax, ay))

        # Decorative lines
        lw = ans_surf.get_width() + 30
        ly = ay + ans_surf.get_height() + 6
        pygame.draw.line(surface, Colors.CORRECT_GLOW,
                         (self.center_x - lw // 2, ly),
                         (self.center_x + lw // 2, ly), 1)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t
