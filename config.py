"""Central configuration for My-Woofie. Every tunable value lives in this file."""

VERSION = "1.0.0"
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")      # one sub-folder per avatar
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
FONT_FILE = os.path.join(BASE_DIR, "assets", "fonts", "PressStart2P-Regular.ttf")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
BREAK_PROMPTS_FILE = os.path.join(BASE_DIR, "break_prompts.txt")
FOCUS_PROMPTS_FILE = os.path.join(BASE_DIR, "focus_prompts.txt")

# Timers. The defaults below can be changed from the Timer settings dialog (right-click My-Woofie),
# or per run with --focus / --break. Saved choices live in settings.json.
TEST_MODE = False  # True (or `python main.py --test`) shrinks the timers for debugging in VS Code
DEFAULT_FOCUS_MINUTES = 240
DEFAULT_BREAK_MINUTES = 15
TEST_FOCUS_SECONDS = 10
TEST_BREAK_SECONDS = 5
TEST_AWAY_SECONDS = 8
TEST_HAUL_SECONDS = 4

FOCUS_TIME_LIMIT_SECONDS = TEST_FOCUS_SECONDS if TEST_MODE else DEFAULT_FOCUS_MINUTES * 60
BREAK_TIME_LIMIT_SECONDS = TEST_BREAK_SECONDS if TEST_MODE else DEFAULT_BREAK_MINUTES * 60
# The focus timer resets after this long without mouse movement (you were really away).
AWAY_RESET_SECONDS = TEST_AWAY_SECONDS if TEST_MODE else 15 * 60
HAUL_DISPLAY_SECONDS = TEST_HAUL_SECONDS if TEST_MODE else 20
MOUSE_MOVE_THRESHOLD_PX = 6

PET_SPEED = 2                    # pixels per frame; kept low so My-Woofie stays calm
AUDIO_ENABLED = True

# Avatar
DEFAULT_AVATAR = "aspen"

# Cursor following
CHASE_WINDOW_SECONDS = 3.0       # keep following for this long after the mouse last moved
CHASE_STOP_DISTANCE_PX = 50      # sit down this close to the cursor

# Sounds: event name -> list of (sound file stem in assets/audio, delay in milliseconds).
SOUND_EVENTS = {
    "break_start": [("puppy_bark", 0), ("soft_howl", 650)],
    "break_end": [("soft_chime", 0)],
}
SOUND_VOLUMES = {"puppy_bark": 0.8, "soft_howl": 0.45, "soft_chime": 0.5}

# Speech bubbles and message banks
SHOW_HUD = True
HUD_ALWAYS_VISIBLE = False      # False = the HUD only appears during breaks (tray menu can override)
ALWAYS_SHOW_BUBBLES = True       # False = bubbles only appear when audio is muted/disabled
BUBBLE_SECONDS = 8
PROMPT_ORDER = "sequential"      # "sequential" or "random"

# Rendering
SPRITE_SIZE = (53, 47)           # every dog is drawn on exactly this canvas (width x height, pixels)
FRAME_INTERVAL_MS = 33
ANIMATION_FRAME_MS = 400
LOG_LEVEL = "DEBUG"
