"""
Mathpal — Global Configuration & Constants
===========================================
All magic numbers live here. Internal resolution is rendered at a low pixel
count and then scaled up with nearest-neighbor filtering for that authentic
retro crunch.
"""

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
INTERNAL_WIDTH = 480          # Low-res canvas width
INTERNAL_HEIGHT = 360         # Low-res canvas height
SCALE_FACTOR = 3              # Nearest-neighbor upscale multiplier
DISPLAY_WIDTH = INTERNAL_WIDTH * SCALE_FACTOR    # 1440
DISPLAY_HEIGHT = INTERNAL_HEIGHT * SCALE_FACTOR  # 1080
FPS = 60
TITLE = "MATHPAL"

# ---------------------------------------------------------------------------
# Color Palette — CGA / EGA inspired with neon accents
# ---------------------------------------------------------------------------

class Colors:
    """Retro color palette constants (R, G, B tuples)."""

    # Neutrals
    BLACK       = (0,   0,   0)
    WHITE       = (255, 255, 255)

    # Background tones
    DARK_NAVY   = (12,  12,  48)
    DEEP_BLUE   = (24,  24,  80)
    ROYAL_BLUE  = (40,  40,  120)
    MIDNIGHT    = (8,   8,   32)

    # Neon accents
    NEON_GREEN  = (0,   255, 128)
    NEON_PINK   = (255, 0,   128)
    NEON_CYAN   = (0,   255, 255)
    ELECTRIC_YELLOW = (255, 255, 0)
    HOT_ORANGE  = (255, 128, 0)
    NEON_PURPLE = (180, 0,   255)

    # Button face colors
    BTN_NORMAL    = (55,  50,  140)
    BTN_HOVER     = (75,  70,  190)
    BTN_PRESSED   = (35,  30,  100)
    BTN_HIGHLIGHT = (110, 105, 220)   # Top / left bevel (light)
    BTN_SHADOW    = (22,  18,  70)    # Bottom / right bevel (dark)

    # Text
    TEXT_PRIMARY   = (255, 255, 255)
    TEXT_SECONDARY = (170, 170, 210)
    TEXT_ACCENT    = (0,   255, 128)
    TEXT_DIM       = (60,  60,  100)

    # Game HUD
    XP_GOLD       = (255, 215, 0)
    HEALTH_RED    = (220, 40,  40)
    HEALTH_GREEN  = (40,  220, 80)
    SHIELD_BLUE   = (60,  140, 255)

    # Starfield
    STAR_DIM      = (80,  80,  120)
    STAR_BRIGHT   = (200, 200, 255)

    # Battle scene
    BATTLE_BG     = (8,   8,   28)
    ENEMY_BODY    = (120, 40,  160)
    ENEMY_DARK    = (80,  20,  120)
    ENEMY_LIGHT   = (160, 80,  200)
    ENEMY_EYES    = (255, 50,  50)
    ENEMY_CROWN   = (255, 215, 0)
    HP_BAR_BG     = (30,  30,  50)
    HP_BAR_FILL   = (40,  200, 80)
    HP_BAR_LOW    = (200, 50,  50)
    HP_BAR_BORDER = (80,  80,  120)

    # Text box
    TEXTBOX_BG     = (14,  14,  45)
    TEXTBOX_BORDER = (70,  70,  160)
    SPEAKER_NAME   = (0,   255, 200)

    # Input box
    INPUT_BG      = (8,   8,   30)
    INPUT_BORDER  = (50,  50,  130)
    INPUT_CURSOR  = (0,   255, 128)

    # Correction animation
    OVERLAY_BG    = (0,   0,   0)
    SPARKLE       = (255, 255, 180)
    CORRECT_GLOW  = (100, 255, 150)

    # Twin Guards (Level 2 Enemy)
    TWIN_LEFT_BODY   = (40,  150, 220)   # Cyan armored guard
    TWIN_LEFT_DARK   = (20,  80,  140)
    TWIN_LEFT_LIGHT  = (100, 210, 255)
    TWIN_RIGHT_BODY  = (220, 50,  150)   # Magenta armored guard
    TWIN_RIGHT_DARK  = (140, 20,  90)
    TWIN_RIGHT_LIGHT = (255, 120, 200)
    TWIN_CORE_GOLD   = (255, 220, 50)
    TWIN_SHIELD_EDGE = (240, 240, 255)

    # Product Rule Animation
    PROD_F_COLOR  = (0,   230, 255)      # Cyan for f(x)
    PROD_G_COLOR  = (255, 215, 0)        # Gold/Yellow for g(x)
    PROD_DF_COLOR = (120, 255, 160)      # Neon Green for f'(x)
    PROD_DG_COLOR = (255, 140, 60)       # Orange for g'(x)
    PROD_PLUS     = (255, 100, 180)      # Pink for '+' sign
    PROD_BRACKET  = (160, 160, 210)

    # Settings UI
    SETTING_ACTIVE_BAR   = (0,   255, 160)
    SETTING_INACTIVE_BAR = (35,  40,  75)
    SETTING_BLOCK_BORDER = (80,  90,  140)
    TOGGLE_ON            = (40,  220, 100)
    TOGGLE_OFF           = (220, 60,  60)

    # Boss & Monster Sprites
    GOLEM_STONE          = (110, 110, 130)
    GOLEM_STONE_DARK     = (65,  65,  85)
    GOLEM_STONE_LIGHT    = (160, 160, 185)
    GOLEM_MOLTEN_CORE    = (255, 120, 30)
    GOLEM_CHAIN_IRON     = (180, 190, 210)
    GOLEM_RUNE           = (255, 200, 50)

    ACCUM_BRASS          = (200, 150, 60)
    ACCUM_GEAR           = (140, 100, 40)
    ACCUM_RIEMANN_BLUE   = (0,   200, 255)

    SLIME_BODY           = (50,  220, 120)
    SLIME_CORE           = (180, 255, 200)

    CRYSTAL_PRISM        = (160, 80,  255)
    CRYSTAL_EDGE         = (220, 180, 255)

    SKULL_BONE           = (230, 230, 240)
    SKULL_FLAME          = (0,   255, 200)

    BOSS_BANNER_BG       = (180, 20,  20)
    BOSS_BANNER_BORDER   = (255, 215, 0)

# ---------------------------------------------------------------------------
# Typography — sizes are for the INTERNAL resolution surface
# ---------------------------------------------------------------------------
FONT_SIZE_TITLE  = 48
FONT_SIZE_LARGE  = 24
FONT_SIZE_MEDIUM = 16
FONT_SIZE_SMALL  = 12

# Preferred fonts in fallback order (system monospace / pixel-friendly)
FONT_PREFERENCES = ["Consolas", "Courier New", "Menlo", "Monaco", "monospace"]

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
AUDIO_SFX_VOLUME  = 0.4
AUDIO_BGM_VOLUME  = 0.25
AUDIO_SAMPLE_RATE = 44100

# ---------------------------------------------------------------------------
# CRT Scanline Effect
# ---------------------------------------------------------------------------
CRT_SCANLINE_ALPHA   = 45        # 0-255 — lower is subtler
CRT_ENABLED_DEFAULT  = True

# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------
BUTTON_WIDTH   = 180
BUTTON_HEIGHT  = 36
BUTTON_BEVEL   = 3
BUTTON_SPACING = 14

# ---------------------------------------------------------------------------
# Gamification Defaults
# ---------------------------------------------------------------------------
STARTING_LIVES = 3
XP_PER_CORRECT = 10
XP_PER_STREAK_BONUS = 5
LEVEL_XP_BASE = 100              # XP to reach level 2
LEVEL_XP_GROWTH = 1.4            # Multiplier per level

# ---------------------------------------------------------------------------
# Battle Scene
# ---------------------------------------------------------------------------
ENEMY_MAX_HP       = 100
PROBLEMS_TO_WIN    = 5
HP_DAMAGE_PER_HIT  = 20          # 100 / 20 = 5 correct answers to win

# ---------------------------------------------------------------------------
# Text Box  (RPG-style, bottom of screen)
# ---------------------------------------------------------------------------
TEXTBOX_X          = 15
TEXTBOX_Y          = 262
TEXTBOX_WIDTH      = 450
TEXTBOX_HEIGHT     = 88
TEXTBOX_CHAR_SPEED = 32          # Characters per second (typewriter)
TEXTBOX_BEVEL      = 3
TEXTBOX_PADDING    = 8

# ---------------------------------------------------------------------------
# Input Box
# ---------------------------------------------------------------------------
INPUTBOX_X         = 145
INPUTBOX_Y         = 222
INPUTBOX_WIDTH     = 175
INPUTBOX_HEIGHT    = 22
INPUTBOX_MAX_LEN   = 18

# ---------------------------------------------------------------------------
# Correction Animation
# ---------------------------------------------------------------------------
CORRECTION_GRAVITY          = 480    # px / s²
CORRECTION_DAMPING          = 0.55   # Bounce energy retention (0-1)
CORRECTION_BOUNCE_THRESHOLD = 12     # Min velocity to stop bouncing

# Phase durations (seconds)
CORR_T_DISPLAY   = 1.2
CORR_T_DETACH    = 0.6
CORR_T_FALL      = 1.6
CORR_T_MULTIPLY  = 1.2
CORR_T_COMPUTE   = 1.0
CORR_T_TICK      = 0.8
CORR_T_RESULT    = 2.5

