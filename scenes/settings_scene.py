"""
Mathpal — Settings Scene
=========================
Classic 90s-styled system configuration menu featuring:
* 10-block discrete retro volume bars for BGM and SFX.
* Tactile 8-bit click sound on volume step changes.
* CRT scanline ON/OFF toggle.
* Real-time audio and visual updates with JSON persistence.
* Full keyboard (Up/Down/Left/Right/Enter) and mouse support.
"""

import pygame

from config import (
    Colors,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    BUTTON_WIDTH, BUTTON_HEIGHT,
)
from core.states import State
from engine.audio import AudioManager
from engine.ui_components import RetroButton, RetroPanel, get_font
from logic.settings_manager import SettingsManager


class SettingsScene(State):
    """Settings scene with 10-block discrete volume bars and CRT toggle."""

    def __init__(self, game):
        super().__init__(game)
        self.audio = AudioManager()
        self.settings = SettingsManager()

        self.small_font = get_font(FONT_SIZE_SMALL)
        self.med_font   = get_font(FONT_SIZE_MEDIUM, bold=True)
        self.big_font   = get_font(FONT_SIZE_LARGE, bold=True)

        # Selected setting index: 0 = BGM, 1 = SFX, 2 = CRT, 3 = BACK
        self.selected_row = 0
        self.total_rows = 4

        # Block bar configuration
        self.num_blocks = 10
        self.block_w = 12
        self.block_h = 16
        self.block_spacing = 3

        # Back Button
        btn_w = 160
        btn_h = 32
        self.back_button = RetroButton(
            (INTERNAL_WIDTH - btn_w) // 2,
            295,
            btn_w,
            btn_h,
            "\u25c0  BACK TO MENU",
        )
        self.back_button.on_click = self._on_back

        # Panels
        self.main_panel = RetroPanel(24, 20, INTERNAL_WIDTH - 48, INTERNAL_HEIGHT - 40)

        # Cache block rects for mouse picking
        self._bgm_rects = self._calc_bar_rects(105)
        self._sfx_rects = self._calc_bar_rects(165)
        self._crt_rect = pygame.Rect(INTERNAL_WIDTH // 2 + 10, 220, 100, 24)

    def _calc_bar_rects(self, y):
        start_x = INTERNAL_WIDTH // 2 - 10
        rects = []
        for i in range(self.num_blocks):
            rx = start_x + i * (self.block_w + self.block_spacing)
            rects.append(pygame.Rect(rx, y, self.block_w, self.block_h))
        return rects

    def enter(self):
        # Keep village theme playing
        self.audio.play_bgm("village")

    def exit(self):
        self.settings.save()

    def handle_event(self, event):
        converter = self.game.renderer.screen_to_internal

        # Mouse handling
        self.back_button.handle_event(event, converter)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = converter(event.pos) if converter else event.pos

            # Click on BGM bar
            for i, r in enumerate(self._bgm_rects):
                if r.collidepoint(pos):
                    self.selected_row = 0
                    self._set_bgm_blocks(i + 1)
                    return

            # Click on SFX bar
            for i, r in enumerate(self._sfx_rects):
                if r.collidepoint(pos):
                    self.selected_row = 1
                    self._set_sfx_blocks(i + 1)
                    return

            # Click on CRT toggle
            if self._crt_rect.collidepoint(pos):
                self.selected_row = 2
                self._toggle_crt()
                return

        # Keyboard navigation
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_row = (self.selected_row - 1) % self.total_rows
                self.audio.play_sfx("hover")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_row = (self.selected_row + 1) % self.total_rows
                self.audio.play_sfx("hover")

            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._handle_left()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._handle_right()

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.selected_row == 2:
                    self._toggle_crt()
                elif self.selected_row == 3:
                    self._on_back()

    def _handle_left(self):
        if self.selected_row == 0:
            blocks = max(0, self._get_bgm_blocks() - 1)
            self._set_bgm_blocks(blocks)
        elif self.selected_row == 1:
            blocks = max(0, self._get_sfx_blocks() - 1)
            self._set_sfx_blocks(blocks)
        elif self.selected_row == 2:
            self._toggle_crt()

    def _handle_right(self):
        if self.selected_row == 0:
            blocks = min(self.num_blocks, self._get_bgm_blocks() + 1)
            self._set_bgm_blocks(blocks)
        elif self.selected_row == 1:
            blocks = min(self.num_blocks, self._get_sfx_blocks() + 1)
            self._set_sfx_blocks(blocks)
        elif self.selected_row == 2:
            self._toggle_crt()

    def _get_bgm_blocks(self):
        return int(round(self.audio.get_bgm_volume() * 10))

    def _set_bgm_blocks(self, blocks):
        vol = max(0.0, min(1.0, blocks / 10.0))
        self.audio.set_bgm_volume(vol)
        self.settings.bgm_volume = vol
        self.settings.save()
        self.audio.play_sfx("block_click")

    def _get_sfx_blocks(self):
        return int(round(self.audio.get_sfx_volume() * 10))

    def _set_sfx_blocks(self, blocks):
        vol = max(0.0, min(1.0, blocks / 10.0))
        self.audio.set_sfx_volume(vol)
        self.settings.sfx_volume = vol
        self.settings.save()
        self.audio.play_sfx("block_click")

    def _toggle_crt(self):
        self.game.crt_enabled = not self.game.crt_enabled
        self.settings.crt_enabled = self.game.crt_enabled
        self.settings.save()
        self.audio.play_sfx("toggle")

    def _on_back(self):
        self.audio.play_sfx("select")
        from scenes.menu_scene import MenuScene
        self.game.change_state(MenuScene(self.game))

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(Colors.DARK_NAVY)
        self.main_panel.draw(surface)

        cx = INTERNAL_WIDTH // 2

        # --- Title ---
        title = self.big_font.render("\u2699  SYSTEM CONFIG", False, Colors.ELECTRIC_YELLOW)
        surface.blit(title, (cx - title.get_width() // 2, 36))

        pygame.draw.line(surface, Colors.TEXTBOX_BORDER, (50, 68), (INTERNAL_WIDTH - 50, 68), 1)

        # --- Row 0: BGM Volume ---
        self._draw_option_row(
            surface,
            row_idx=0,
            y=102,
            label="BGM MUSIC",
            render_type="bar",
            value_blocks=self._get_bgm_blocks(),
            rects=self._bgm_rects,
        )

        # --- Row 1: SFX Volume ---
        self._draw_option_row(
            surface,
            row_idx=1,
            y=162,
            label="SFX SOUNDS",
            render_type="bar",
            value_blocks=self._get_sfx_blocks(),
            rects=self._sfx_rects,
        )

        # --- Row 2: CRT Scanlines ---
        self._draw_option_row(
            surface,
            row_idx=2,
            y=222,
            label="CRT SCANLINES",
            render_type="toggle",
            toggle_state=self.game.crt_enabled,
        )

        # --- Row 3: Back Button ---
        # Highlight pointer if row 3 is selected
        if self.selected_row == 3:
            ptr = self.med_font.render("\u25b6", False, Colors.NEON_CYAN)
            surface.blit(ptr, (self.back_button.rect.x - 20, self.back_button.rect.y + 6))
        self.back_button.draw(surface, self.med_font)

        # --- Footer Hint ---
        hint = self.small_font.render("\u2191\u2193 Select   \u2190\u2192 Adjust   ENTER Confirm", False, Colors.TEXT_DIM)
        surface.blit(hint, (cx - hint.get_width() // 2, INTERNAL_HEIGHT - 28))

    def _draw_option_row(self, surface, row_idx, y, label, render_type="bar", value_blocks=0, rects=None, toggle_state=False):
        is_selected = (self.selected_row == row_idx)
        label_color = Colors.NEON_CYAN if is_selected else Colors.TEXT_PRIMARY

        # Selection pointer
        if is_selected:
            ptr = self.med_font.render("\u25b6", False, Colors.NEON_CYAN)
            surface.blit(ptr, (44, y + 2))

        # Label
        lbl_surf = self.med_font.render(label, False, label_color)
        surface.blit(lbl_surf, (64, y + 2))

        if render_type == "bar":
            # Draw 10 discrete blocks
            for i, r in enumerate(rects):
                filled = (i < value_blocks)
                fill_col = Colors.SETTING_ACTIVE_BAR if filled else Colors.SETTING_INACTIVE_BAR
                pygame.draw.rect(surface, fill_col, r)
                border_col = Colors.NEON_GREEN if (filled and is_selected) else Colors.SETTING_BLOCK_BORDER
                pygame.draw.rect(surface, border_col, r, 1)

            # Percentage text
            pct_str = f"{value_blocks * 10}%"
            pct_surf = self.small_font.render(pct_str, False, Colors.TEXT_SECONDARY)
            surface.blit(pct_surf, (rects[-1].right + 12, y + 3))

        elif render_type == "toggle":
            r = self._crt_rect
            # Background toggle box
            box_col = (20, 24, 50)
            pygame.draw.rect(surface, box_col, r)
            border_col = Colors.NEON_CYAN if is_selected else Colors.TEXTBOX_BORDER
            pygame.draw.rect(surface, border_col, r, 1)

            txt = "[ ON ]" if toggle_state else "[ OFF ]"
            txt_col = Colors.TOGGLE_ON if toggle_state else Colors.TOGGLE_OFF
            t_surf = self.med_font.render(txt, False, txt_col)
            surface.blit(t_surf, (r.centerx - t_surf.get_width() // 2, r.centery - t_surf.get_height() // 2))
