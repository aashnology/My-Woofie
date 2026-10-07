"""Central configuration for Aspen. Every tunable value lives in this file."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")      # one sub-folder per avatar
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
FONT_FILE = os.path.join(BASE_DIR, "assets", "fonts", "PressStart2P-Regular.ttf")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
BREAK_PROMPTS_FILE = os.path.join(BASE_DIR, "break_prompts.txt")
FOCUS_PROMPTS_FILE = os.path.join(BASE_DIR, "focus_prompts.txt")

# Hardcoded Constants
TEST_MODE = True  # If True, set 4 hours -> 10 seconds for rapid debugging in VS Code!
FOCUS_TIME_LIMIT_SECONDS = 10 if TEST_MODE else 4 * 3600
BREAK_TIME_LIMIT_SECONDS = 5 if TEST_MODE else 15 * 60
PET_SPEED = 5
AUDIO_ENABLED = True

# Presence detection: the focus timer resets after this long without mouse movement.
AWAY_RESET_SECONDS = 8 if TEST_MODE else 15 * 60
MOUSE_MOVE_THRESHOLD_PX = 6

# Avatar
DEFAULT_AVATAR = "aspen"

# Cursor following
CHASE_WINDOW_SECONDS = 5.0       # keep following for this long after the mouse last moved
CHASE_STOP_DISTANCE_PX = 90      # sit down this close to the cursor
HAUL_DISPLAY_SECONDS = 4 if TEST_MODE else 20

# Sounds: event name -> list of (sound file stem in assets/audio, delay in milliseconds).
SOUND_EVENTS = {
    "break_start": [("puppy_bark", 0), ("soft_howl", 650)],
    "break_end": [("soft_chime", 0)],
}
SOUND_VOLUMES = {"puppy_bark": 0.8, "soft_howl": 0.45, "soft_chime": 0.5}

# Speech bubbles and message banks
SHOW_HUD = True
ALWAYS_SHOW_BUBBLES = True       # False = bubbles only appear when audio is muted/disabled
BUBBLE_SECONDS = 8
PROMPT_ORDER = "sequential"      # "sequential" or "random"

# Rendering
SPRITE_TARGET_PX = 160           # on-screen sprite height; each avatar is scaled by a whole number
FRAME_INTERVAL_MS = 33
ANIMATION_FRAME_MS = 250
LOG_LEVEL = "DEBUG"
