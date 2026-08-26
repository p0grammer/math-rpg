"""
Mathpal — Play Scene (Data-Driven Campaign & Boss Battles)
===========================================================
Drives the 50-level campaign dynamically from `data/levels.json`, supporting
procedural standard enemies, custom Boss battles, and topic-specific
kinetic error visualizers.
"""

import math
import random
from enum import Enum, auto

import pygame

from config import (
    Colors,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_TITLE,
    INPUTBOX_X, INPUTBOX_Y, INPUTBOX_WIDTH, INPUTBOX_HEIGHT,
    XP_PER_CORRECT, STARTING_LIVES,
)
from core.states import State
from engine.audio import AudioManager
from engine.text_box import TextBox
from engine.input_box import InputBox
from engine.math_renderer import MathRenderer
from engine.ui_components import get_font
from logic.levels import LevelManager, LevelDefinition
from logic.equation_generator import MathProblem
from logic.settings_manager import SettingsManager
from scenes.correction_anim import CorrectionAnimation
from scenes.product_rule_anim import ProductRuleCorrectionAnimation
from scenes.chain_rule_anim import ChainRuleCorrectionAnimation


class SubState(Enum):
    STORY_INTRO      = auto()
    TUTORIAL         = auto()
    BATTLE           = auto()
    CORRECT          = auto()
    INCORRECT        = auto()
    LEVEL_VICTORY    = auto()
    CAMPAIGN_VICTORY = auto()


class PlayScene(State):
    """Universal Battle & Campaign Scene driven dynamically by LevelDefinitions."""

    def __init__(self, game, level_id=1):
        super().__init__(game)
        self.audio = AudioManager()
        self.settings = SettingsManager()
        self.mr = MathRenderer()

        self.small_font = get_font(FONT_SIZE_SMALL)
        self.med_font   = get_font(FONT_SIZE_MEDIUM, bold=True)
        self.big_font   = get_font(FONT_SIZE_LARGE, bold=True)
        self.title_font = get_font(FONT_SIZE_TITLE, bold=True)

        self.text_box = TextBox()
        self.input_box = InputBox(
            INPUTBOX_X, INPUTBOX_Y, INPUTBOX_WIDTH, INPUTBOX_HEIGHT
        )

        self.current_level_id = level_id
        self.level_def: LevelDefinition = LevelManager.get_level(self.current_level_id)

        self.sub_state = SubState.STORY_INTRO
        self.enemy_hp = self.level_def.enemy_max_hp
        self.problems_solved = 0
        self.current_problem: MathProblem = None
        self.xp_earned = 0
        self.lives = STARTING_LIVES
        self.time = 0.0

        self.correction_anim = None
        self.slash_timer = 0.0
        self.screen_flash = 0.0
        self.enemy_hit_flash = 0.0
        self._enemy_bob = 0.0
        self._equation_surf = None

        self.text_box.set_messages(self.level_def.story_messages)

    def enter(self):
        if self.sub_state in (SubState.STORY_INTRO, SubState.TUTORIAL):
            self.audio.play_bgm("village")
        else:
            self.audio.play_bgm("battle")

    def exit(self):
        self.audio.play_bgm("village")

    # ------------------------------------------------------------------
    # Event Handling
    # ------------------------------------------------------------------

    def handle_event(self, event):
        if self.sub_state == SubState.STORY_INTRO:
            if self.text_box.handle_event(event):
                self.sub_state = SubState.TUTORIAL
                self.text_box.set_messages(self.level_def.tutorial_messages)

        elif self.sub_state == SubState.TUTORIAL:
            if self.text_box.handle_event(event):
                self._start_battle()

        elif self.sub_state == SubState.BATTLE:
            self.text_box.handle_event(event)
            result = self.input_box.handle_event(event)
            if result is not None:
                self._check_answer(result)

        elif self.sub_state == SubState.CORRECT:
            pass

        elif self.sub_state == SubState.INCORRECT:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.correction_anim and self.correction_anim.is_complete:
                    self._resume_battle()

        elif self.sub_state == SubState.LEVEL_VICTORY:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance_to_next_level()

        elif self.sub_state == SubState.CAMPAIGN_VICTORY:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                from scenes.menu_scene import MenuScene
                self.game.change_state(MenuScene(self.game))

    # ------------------------------------------------------------------
    # Update Loop
    # ------------------------------------------------------------------

    def update(self, dt):
        self.time += dt
        self.text_box.update(dt)
        self._enemy_bob = math.sin(self.time * 2.8) * 3.5

        if self.sub_state == SubState.BATTLE:
            self.input_box.update(dt)

        elif self.sub_state == SubState.CORRECT:
            self.slash_timer += dt
            self.screen_flash = max(0.0, self.screen_flash - dt * 3.0)
            self.enemy_hit_flash = max(0.0, self.enemy_hit_flash - dt * 4.0)

            if self.slash_timer >= 1.6:
                if self.enemy_hp <= 0:
                    self._handle_enemy_defeat()
                else:
                    self._next_problem()

        elif self.sub_state == SubState.INCORRECT:
            if self.correction_anim and not self.correction_anim.is_complete:
                self.correction_anim.update(dt)

    # ------------------------------------------------------------------
    # Battle Logic
    # ------------------------------------------------------------------

    def _start_battle(self):
        self.sub_state = SubState.BATTLE
        self.audio.play_bgm("battle")
        self.enemy_hp = self.level_def.enemy_max_hp
        self.problems_solved = 0

        prefix = "BOSS ENCOUNTER: " if self.level_def.is_boss else ""
        intro_text = [
            ("", f"{prefix}{self.level_def.enemy_name} emerges!"),
            ("MASTER LEIBNIZ", f"Use your knowledge of {self.level_def.topic.replace('_', ' ')}!"),
        ]
        self.text_box.set_messages(intro_text)
        self._generate_problem()

    def _generate_problem(self):
        diff = 1 + self.problems_solved // 2
        self.current_problem = self.level_def.generate_problem(difficulty=min(diff, 3))
        self._equation_surf, _, _ = self.mr.render(
            self.current_problem.expression_str, color=Colors.ELECTRIC_YELLOW
        )
        self.input_box.clear()
        self.input_box.activate()

    def _check_answer(self, answer):
        if self.current_problem.check_answer(answer):
            self._on_correct()
        else:
            self._on_incorrect()

    def _on_correct(self):
        self.audio.play_sfx("slash")
        self.sub_state = SubState.CORRECT
        self.slash_timer = 0.0
        self.screen_flash = 1.0
        self.enemy_hit_flash = 1.0
        self.enemy_hp = max(0, self.enemy_hp - self.level_def.hp_per_hit)
        xp_gain = XP_PER_CORRECT * (2 if self.level_def.is_boss else 1)
        self.xp_earned += xp_gain
        self.settings.total_xp += xp_gain
        self.problems_solved += 1
        self.input_box.deactivate()

        self.text_box.set_messages([
            ("", f"DIRECT HIT!  +{xp_gain} XP!"),
        ])

    def _on_incorrect(self):
        self.audio.play_sfx("wrong")
        self.sub_state = SubState.INCORRECT
        self.input_box.deactivate()

        # Dynamic visualizer routing
        if self.level_def.topic == "CHAIN_RULE":
            self.correction_anim = ChainRuleCorrectionAnimation(self.current_problem)
        elif self.level_def.topic == "PRODUCT_RULE":
            self.correction_anim = ProductRuleCorrectionAnimation(self.current_problem)
        elif self.level_def.topic == "POWER_RULE":
            self.correction_anim = CorrectionAnimation(self.current_problem)
        else:
            # Fallback to chain / power rule visualizer
            self.correction_anim = ChainRuleCorrectionAnimation(self.current_problem)

    def _resume_battle(self):
        self.correction_anim = None
        self.sub_state = SubState.BATTLE
        self.text_box.set_messages([
            ("MASTER LEIBNIZ", "Steady your blade! Try again!"),
        ])
        self.input_box.clear()
        self.input_box.activate()

    def _next_problem(self):
        self.sub_state = SubState.BATTLE
        self._generate_problem()
        praise = [
            "Great strike! Next equation!",
            "Their power is wavering! Keep going!",
            "Calculus mastery in action! Attack again!",
        ]
        self.text_box.set_messages([("MASTER LEIBNIZ", random.choice(praise))])

    def _handle_enemy_defeat(self):
        self.audio.play_sfx("levelup")
        self.settings.save()

        if self.current_level_id < LevelManager.max_level():
            self.sub_state = SubState.LEVEL_VICTORY
            self.audio.play_bgm("village")
            next_lvl = self.current_level_id + 1
            self.text_box.set_messages(self.level_def.victory_messages + [
                ("", f"Press SPACE to advance to LEVEL {next_lvl}...")
            ])
        else:
            self.sub_state = SubState.CAMPAIGN_VICTORY
            self.audio.play_bgm("village")
            self.text_box.set_messages(self.level_def.victory_messages + [
                ("", "ALL 50 LEVELS CONQUERED! Press SPACE to return to Menu.")
            ])

    def _advance_to_next_level(self):
        self.current_level_id += 1
        self.settings.unlocked_level = max(self.settings.unlocked_level, self.current_level_id)
        self.settings.save()

        self.level_def = LevelManager.get_level(self.current_level_id)
        self.sub_state = SubState.STORY_INTRO
        self.enemy_hp = self.level_def.enemy_max_hp
        self.problems_solved = 0
        self.text_box.set_messages(self.level_def.story_messages)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, surface):
        surface.fill(Colors.BATTLE_BG)

        if self.sub_state in (SubState.STORY_INTRO, SubState.TUTORIAL):
            self._draw_story_bg(surface)
        else:
            self._draw_battle_scene(surface)

        self.text_box.draw(surface)

        if self.screen_flash > 0:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self.screen_flash * 140)))
            surface.blit(flash, (0, 0))

    def _draw_story_bg(self, surface):
        for y in range(0, INTERNAL_HEIGHT, 4):
            b = max(0, 18 - y // 25)
            pygame.draw.line(surface, (b, b, b + 12), (0, y), (INTERNAL_WIDTH, y))

        cx = INTERNAL_WIDTH // 2
        header_text = f"~ {self.level_def.name.upper()} ~"
        header_col = Colors.ENEMY_CROWN if self.level_def.is_boss else Colors.ELECTRIC_YELLOW
        lbl = self.med_font.render(header_text, False, header_col)
        surface.blit(lbl, (cx - lbl.get_width() // 2, 22))

        # Boss indicator on story screen
        if self.level_def.is_boss:
            b_tag = self.small_font.render("\u2605 BOSS ENCOUNTER \u2605", False, Colors.HEALTH_RED)
            surface.blit(b_tag, (cx - b_tag.get_width() // 2, 42))

        if self.sub_state == SubState.TUTORIAL:
            f_surf = self.med_font.render(self.level_def.formula_display, False, Colors.NEON_CYAN)
            surface.blit(f_surf, (cx - f_surf.get_width() // 2, 68))
            pygame.draw.line(surface, Colors.TEXTBOX_BORDER, (cx - 140, 62), (cx + 140, 62), 1)
            pygame.draw.line(surface, Colors.TEXTBOX_BORDER, (cx - 140, 92), (cx + 140, 92), 1)

    def _draw_battle_scene(self, surface):
        self._draw_hud(surface)

        # Boss Warning Banner at top
        if self.level_def.is_boss and self.sub_state == SubState.BATTLE:
            self._draw_boss_banner(surface)

        if self.sub_state != SubState.INCORRECT:
            self._draw_enemy_by_type(surface)

        self._draw_hp_bar(surface)

        if self.current_problem and self._equation_surf:
            self._draw_equation(surface)

        if self.sub_state == SubState.CORRECT and self.slash_timer < 0.35:
            self._draw_slash(surface)

        if self.sub_state == SubState.BATTLE:
            self._draw_input_area(surface)

        if self.sub_state == SubState.INCORRECT and self.correction_anim:
            self.correction_anim.draw(surface)

        if self.sub_state in (SubState.LEVEL_VICTORY, SubState.CAMPAIGN_VICTORY):
            self._draw_victory_banner(surface)

    def _draw_hud(self, surface):
        lives_text = "\u2665 " * self.lives
        lives_surf = self.small_font.render(lives_text, False, Colors.HEALTH_RED)
        surface.blit(lives_surf, (8, 4))

        lvl_tag = f"LVL {self.current_level_id}/50  |  XP: {self.xp_earned}"
        xp_surf = self.small_font.render(lvl_tag, False, Colors.XP_GOLD)
        surface.blit(xp_surf, (INTERNAL_WIDTH - xp_surf.get_width() - 8, 4))

    def _draw_boss_banner(self, surface):
        pulse = 0.5 + 0.5 * math.sin(self.time * 5.0)
        cx = INTERNAL_WIDTH // 2
        banner_surf = pygame.Surface((220, 18), pygame.SRCALPHA)
        banner_surf.fill((160, 20, 20, int(180 + 50 * pulse)))
        surface.blit(banner_surf, (cx - 110, 20))
        pygame.draw.rect(surface, Colors.BOSS_BANNER_BORDER, (cx - 110, 20, 220, 18), 1)

        txt = self.small_font.render("\u26a0 BOSS BATTLE \u26a0", False, Colors.WHITE)
        surface.blit(txt, (cx - txt.get_width() // 2, 22))

    def _draw_enemy_by_type(self, surface):
        t = self.level_def.enemy_type
        if t == "golem":
            self._draw_chain_golem(surface)
        elif t == "twins":
            self._draw_twin_guards(surface)
        elif t == "slime":
            self._draw_slime(surface)
        elif t == "crystal":
            self._draw_crystal(surface)
        elif t == "skull":
            self._draw_skull(surface)
        elif t == "accumulator":
            self._draw_accumulator(surface)
        else:
            self._draw_polynomial_beast(surface)

    # ------------------------------------------------------------------
    # Procedural Enemy Sprite Renderers
    # ------------------------------------------------------------------

    def _draw_chain_golem(self, surface):
        """Level 5 Boss: The Chain Golem (Armored stone colossus with heavy chains)."""
        cx = INTERNAL_WIDTH // 2
        cy = 92 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)

        stone_col = Colors.WHITE if flash else Colors.GOLEM_STONE
        dark_col = Colors.WHITE if flash else Colors.GOLEM_STONE_DARK
        light_col = Colors.WHITE if flash else Colors.GOLEM_STONE_LIGHT
        core_col = Colors.WHITE if flash else Colors.GOLEM_MOLTEN_CORE

        # Massive Stone Shoulders & Torso
        pygame.draw.rect(surface, dark_col, (cx - 42, cy - 28, 84, 56))
        pygame.draw.rect(surface, stone_col, (cx - 38, cy - 24, 76, 48))
        pygame.draw.rect(surface, light_col, (cx - 38, cy - 24, 76, 48), 2)

        # Molten Core (Pulsing lava heart)
        pulse = 0.5 + 0.5 * math.sin(self.time * 6.0)
        core_r = int(12 + 3 * pulse)
        pygame.draw.circle(surface, core_col, (cx, cy + 2), core_r)
        pygame.draw.circle(surface, Colors.ELECTRIC_YELLOW, (cx, cy + 2), max(2, core_r - 5))

        # Stone Head with Glowing Rune Eyes
        pygame.draw.rect(surface, stone_col, (cx - 16, cy - 42, 32, 20))
        pygame.draw.rect(surface, light_col, (cx - 16, cy - 42, 32, 20), 2)
        pygame.draw.rect(surface, Colors.GOLEM_RUNE, (cx - 10, cy - 34, 6, 4))
        pygame.draw.rect(surface, Colors.GOLEM_RUNE, (cx + 4, cy - 34, 6, 4))

        # Heavy Iron Chains wrapped around arms
        for side in (-1, 1):
            fist_x = cx + side * 46
            # Stone Fists
            pygame.draw.rect(surface, stone_col, (fist_x - 10, cy + 4, 20, 24))
            pygame.draw.rect(surface, light_col, (fist_x - 10, cy + 4, 20, 24), 2)
            # Chain links
            for link_y in range(cy - 16, cy + 8, 8):
                pygame.draw.rect(surface, Colors.GOLEM_CHAIN_IRON, (fist_x - 6, link_y, 12, 6), 1)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 44))

    def _draw_accumulator(self, surface):
        """Level 10 Boss: The Accumulator (Clockwork Riemann integral engine)."""
        cx = INTERNAL_WIDTH // 2
        cy = 92 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)

        brass = Colors.WHITE if flash else Colors.ACCUM_BRASS
        gear_col = Colors.WHITE if flash else Colors.ACCUM_GEAR

        # Rotating Gear Ring
        angle_off = self.time * 1.5
        for i in range(8):
            a = angle_off + i * (math.pi / 4)
            gx = cx + int(36 * math.cos(a))
            gy = cy + int(36 * math.sin(a))
            pygame.draw.rect(surface, gear_col, (gx - 4, gy - 4, 8, 8))

        # Brass Engine Core
        pygame.draw.circle(surface, brass, (cx, cy), 30)
        pygame.draw.circle(surface, Colors.ACCUM_RIEMANN_BLUE, (cx, cy), 18)

        # Integral Symbol Rune
        int_sym = self.big_font.render("\u222b", False, Colors.WHITE)
        surface.blit(int_sym, (cx - int_sym.get_width() // 2, cy - int_sym.get_height() // 2))

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 44))

    def _draw_slime(self, surface):
        """Gelatinous pulsing slime with eye and bouncing nucleus."""
        cx = INTERNAL_WIDTH // 2
        cy = 96 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)
        body = Colors.WHITE if flash else Colors.SLIME_BODY

        squish = math.sin(self.time * 4.0) * 3
        w = int(32 + squish)
        h = int(24 - squish)

        pygame.draw.ellipse(surface, body, (cx - w, cy - h + 10, w * 2, h * 2))
        pygame.draw.ellipse(surface, Colors.SLIME_CORE, (cx - w + 6, cy - h + 14, (w - 6) * 2, (h - 6) * 2), 2)
        # Eye
        pygame.draw.circle(surface, Colors.WHITE, (cx, cy + 8), 5)
        pygame.draw.circle(surface, Colors.BLACK, (cx + 1, cy + 8), 2)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 42))

    def _draw_crystal(self, surface):
        """Floating geometric crystal with rotating facets."""
        cx = INTERNAL_WIDTH // 2
        cy = 92 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)
        c_col = Colors.WHITE if flash else Colors.CRYSTAL_PRISM
        e_col = Colors.WHITE if flash else Colors.CRYSTAL_EDGE

        pts = [
            (cx, cy - 28), (cx + 22, cy), (cx, cy + 28), (cx - 22, cy)
        ]
        pygame.draw.polygon(surface, c_col, pts)
        pygame.draw.polygon(surface, e_col, pts, 2)
        pygame.draw.line(surface, e_col, (cx, cy - 28), (cx, cy + 28), 1)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 42))

    def _draw_skull(self, surface):
        """Floating cyber-skull with glowing turquoise flames."""
        cx = INTERNAL_WIDTH // 2
        cy = 92 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)
        bone = Colors.WHITE if flash else Colors.SKULL_BONE

        # Cranium
        pygame.draw.circle(surface, bone, (cx, cy - 4), 20)
        pygame.draw.rect(surface, bone, (cx - 12, cy + 4, 24, 14))
        # Eye sockets
        pygame.draw.circle(surface, Colors.BLACK, (cx - 7, cy - 2), 5)
        pygame.draw.circle(surface, Colors.BLACK, (cx + 7, cy - 2), 5)
        pygame.draw.circle(surface, Colors.SKULL_FLAME, (cx - 7, cy - 2), 2)
        pygame.draw.circle(surface, Colors.SKULL_FLAME, (cx + 7, cy - 2), 2)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 42))

    def _draw_polynomial_beast(self, surface):
        cx = INTERNAL_WIDTH // 2
        cy = 95 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)
        body_col = Colors.WHITE if flash else Colors.ENEMY_BODY
        border_col = Colors.WHITE if flash else Colors.ENEMY_LIGHT

        pts = [
            (cx + int(34 * math.cos(math.radians(-90 + i * 72))),
             cy + int(34 * math.sin(math.radians(-90 + i * 72))))
            for i in range(5)
        ]
        pygame.draw.polygon(surface, body_col, pts)
        pygame.draw.polygon(surface, border_col, pts, 2)

        eye_y = cy - 4
        for ex in (cx - 10, cx + 10):
            pygame.draw.rect(surface, Colors.ENEMY_EYES, (ex - 3, eye_y - 3, 6, 6))
            pygame.draw.rect(surface, Colors.BLACK, (ex - 1, eye_y - 1, 3, 3))

        crown_y = cy - 40
        crown_pts = [
            (cx - 16, crown_y + 12), (cx - 16, crown_y + 4),
            (cx - 10, crown_y + 8),  (cx - 5,  crown_y),
            (cx,      crown_y + 8),  (cx + 5,  crown_y),
            (cx + 10, crown_y + 8),  (cx + 16, crown_y + 4),
            (cx + 16, crown_y + 12),
        ]
        pygame.draw.polygon(surface, Colors.ENEMY_CROWN, crown_pts)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 42))

    def _draw_twin_guards(self, surface):
        cx = INTERNAL_WIDTH // 2
        cy = 94 + int(self._enemy_bob)
        flash = (self.enemy_hit_flash > 0 and int(self.time * 20) % 2 == 0)

        # Left Guard (Cyan)
        g1_cx = cx - 28
        g1_body = Colors.WHITE if flash else Colors.TWIN_LEFT_BODY
        g1_light = Colors.WHITE if flash else Colors.TWIN_LEFT_LIGHT
        pygame.draw.rect(surface, g1_body, (g1_cx - 14, cy - 23, 28, 41))
        pygame.draw.rect(surface, g1_light, (g1_cx - 14, cy - 23, 28, 41), 2)
        pygame.draw.rect(surface, Colors.NEON_CYAN, (g1_cx - 8, cy - 14, 16, 4))

        # Right Guard (Magenta)
        g2_cx = cx + 28
        g2_body = Colors.WHITE if flash else Colors.TWIN_RIGHT_BODY
        g2_light = Colors.WHITE if flash else Colors.TWIN_RIGHT_LIGHT
        pygame.draw.rect(surface, g2_body, (g2_cx - 14, cy - 23, 28, 41))
        pygame.draw.rect(surface, g2_light, (g2_cx - 14, cy - 23, 28, 41), 2)
        pygame.draw.rect(surface, Colors.NEON_PINK, (g2_cx - 8, cy - 14, 16, 4))

        # Center Shield
        pulse = 0.5 + 0.5 * math.sin(self.time * 6.0)
        shield_pts = [
            (cx, cy - 22), (cx + 18, cy - 8), (cx + 12, cy + 24),
            (cx, cy + 32), (cx - 12, cy + 24), (cx - 18, cy - 8)
        ]
        shield_fill = Colors.WHITE if flash else (int(200 + 55 * pulse), int(180 + 40 * pulse), 40)
        pygame.draw.polygon(surface, shield_fill, shield_pts)
        pygame.draw.polygon(surface, Colors.TWIN_SHIELD_EDGE, shield_pts, 2)

        name = self.small_font.render(self.level_def.enemy_name, False, Colors.TEXT_SECONDARY)
        surface.blit(name, (cx - name.get_width() // 2, cy + 44))

    def _draw_hp_bar(self, surface):
        bar_w, bar_h = 160, 10
        bar_x = (INTERNAL_WIDTH - bar_w) // 2
        bar_y = 155

        pygame.draw.rect(surface, Colors.HP_BAR_BG, (bar_x, bar_y, bar_w, bar_h))
        ratio = max(0.0, self.enemy_hp / self.level_def.enemy_max_hp)
        fill_col = Colors.HP_BAR_FILL if ratio > 0.3 else Colors.HP_BAR_LOW
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_col, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(surface, Colors.HP_BAR_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)

        hp_lbl = self.small_font.render(f"HP: {self.enemy_hp}/{self.level_def.enemy_max_hp}", False, Colors.TEXT_PRIMARY)
        surface.blit(hp_lbl, (bar_x + bar_w + 8, bar_y - 1))

    def _draw_equation(self, surface):
        cx = INTERNAL_WIDTH // 2
        eq_y = 178
        prefix = self.med_font.render(f"f(x) = ", False, Colors.TEXT_SECONDARY)
        total_w = prefix.get_width() + self._equation_surf.get_width()
        start_x = cx - total_w // 2
        surface.blit(prefix, (start_x, eq_y))
        surface.blit(self._equation_surf, (start_x + prefix.get_width(), eq_y - 2))

    def _draw_input_area(self, surface):
        op_label = getattr(self.current_problem, "operator_label", "d/dx =")
        label = self.med_font.render(op_label, False, Colors.NEON_CYAN)
        surface.blit(label, (INPUTBOX_X - label.get_width() - 8, INPUTBOX_Y + 2))
        self.input_box.draw(surface)

        hint = self.small_font.render("ENTER to submit", False, Colors.TEXT_DIM)
        surface.blit(hint, (INPUTBOX_X, INPUTBOX_Y + INPUTBOX_HEIGHT + 4))

    def _draw_slash(self, surface):
        progress = min(1.0, self.slash_timer / 0.22)
        sx = int(INTERNAL_WIDTH * 0.20)
        sy = 40
        ex = int(sx + INTERNAL_WIDTH * 0.60 * progress)
        ey = int(sy + 130 * progress)
        for i, width in enumerate([6, 3, 1]):
            c = min(255, 200 + i * 28)
            pygame.draw.line(surface, (c, c, c), (sx - i * 3, sy + i * 2), (ex - i * 3, ey + i * 2), width)

    def _draw_victory_banner(self, surface):
        cx = INTERNAL_WIDTH // 2
        pulse = 0.5 + 0.5 * math.sin(self.time * 4)
        r = int(100 + 155 * pulse)
        banner_txt = "BOSS DEFEATED!" if self.level_def.is_boss else "STAGE CLEAR!"
        vic = self.title_font.render(banner_txt, False, (min(255, r), 255, 120))
        surface.blit(vic, (cx - vic.get_width() // 2, 55))
