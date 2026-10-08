"""Central configuration for My-Woofie. Every tunable value lives in this file."""
import os

import paths

VERSION = "2.0.2"

BASE_DIR = paths.resource_dir()
DATA_DIR = paths.data_dir()
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")      # one sub-folder per avatar
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
FONT_FILE = os.path.join(BASE_DIR, "assets", "fonts", "PressStart2P-Regular.ttf")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")          # local-only break statistics
PET_STATE_FILE = os.path.join(DATA_DIR, "pet_state.json")  # mood, daily counters, wardrobe
BREAK_PROMPTS_FILE = paths.user_file("break_prompts.txt")
FOCUS_PROMPTS_FILE = paths.user_file("focus_prompts.txt")
BREAK_TIPS_FILE = paths.user_file("break_tips.txt")        # V2: stretch / water / eye tips shown during breaks

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

PET_SPEED = 2                    # pixels per frame; kept low so My-Woofie stays calm (Settings can scale it)
AUDIO_ENABLED = True

# Avatar
DEFAULT_AVATAR = "aspen"

# Cursor following
CHASE_WINDOW_SECONDS = 3.0       # he sits beside the cursor this long after the mouse stops, but a chase in progress always finishes
CHASE_STOP_DISTANCE_PX = 50      # sit down this close to the cursor

# Sounds: event name -> list of (sound file stem in assets/audio, delay in milliseconds).
SOUND_EVENTS = {
    "break_start": [("puppy_bark", 0), ("soft_howl", 650)],
    "break_end": [("soft_chime", 0)],
    "micro": [("soft_chime", 0)],
}
SOUND_VOLUMES = {"puppy_bark": 0.8, "soft_howl": 0.45, "soft_chime": 0.5}

# Speech bubbles and message banks
SHOW_HUD = True
HUD_ALWAYS_VISIBLE = False      # False = the HUD only appears during breaks (tray menu can override)
ALWAYS_SHOW_BUBBLES = True       # False = bubbles only appear when audio is muted/disabled
BUBBLE_SECONDS = 8
PROMPT_ORDER = "sequential"      # "sequential" or "random"

# Rendering
# LOCKED: every dog, including any avatar added in the future, must fit exactly this canvas
# (width x height, pixels). This size was approved on a real Windows desktop; do not change it.
SPRITE_SIZE = (53, 47)
FRAME_INTERVAL_MS = 33
ANIMATION_FRAME_MS = 400
LOG_LEVEL = "DEBUG"

# ---------------------------------------------------------------------------------------------
# Version 2
# ---------------------------------------------------------------------------------------------
# Snooze: "5 more minutes", limited per focus cycle so it cannot become a way to skip breaks.
DEFAULT_SNOOZE_MINUTES = 5
DEFAULT_MAX_SNOOZES = 2
TEST_SNOOZE_SECONDS = 4
# A break counts as "taken" when the mouse was active for no more than this share of it.
BREAK_ACTIVE_TOLERANCE = 0.25

# Micro-breaks: short reminders between the big breaks (eye rest, stretch, water, posture).
MICRO_ENABLED = True
DEFAULT_MICRO_INTERVAL_MINUTES = 20
DEFAULT_MICRO_SECONDS = 20
TEST_MICRO_INTERVAL_SECONDS = 6
TEST_MICRO_SECONDS = 3
MICRO_QUIET_BEFORE_BREAK_SECONDS = 300   # no micro-break this close to a big break
MICRO_PRESENCE_SECONDS = 60              # skip it if the mouse has been still this long
MICRO_KINDS = ("eyes", "stretch", "water", "posture")   # rotated in this order

# Mood and streaks
MOOD_START = 70.0
MOOD_FLOOR = 0.0
MOOD_CEILING = 100.0
MOOD_DRIFT_TARGET = 60.0         # while the app was closed, mood drifts gently toward this
MOOD_DRIFT_PER_HOUR = 2.0
MOOD_EVENTS = {                  # how each event changes mood
    "break_taken": 12.0, "break_skipped": -15.0, "snoozed": -4.0, "away": 8.0,
    "micro_done": 2.0, "micro_skipped": -1.0, "pet": 1.0, "treat": 6.0, "fetch": 4.0,
}
DROOPY_SPEED_FACTOR = 0.75
STREAK_GAP_DAYS = 2              # one missing day keeps a streak alive (weekends, days off)
STATS_KEEP_DAYS = 120

# Wardrobe: accessory -> streak days needed to unlock it.
ACCESSORIES = {"party_hat": 1, "flower": 3, "beanie": 5, "bandana": 7, "top_hat": 10, "crown": 14}

# Petting, treats and fetch
PET_HOLD_SECONDS = 0.35
PET_TICK_SECONDS = 1.5
MAX_PET_BOOSTS_PER_DAY = 20
MAX_TREATS_PER_DAY = 5
MAX_FETCH_BOOSTS_PER_DAY = 5
FETCH_IDLE_TIMEOUT_SECONDS = 90
BALL_SIZE = 18
BALL_FRICTION = 0.985
BALL_BOUNCE = 0.6

# Time of day
DEFAULT_SLEEP_START_HOUR = 22    # the pup curls up for a nap when you pause mouse use after this
DEFAULT_SLEEP_END_HOUR = 6
DEFAULT_BEDTIME_HOUR = 23        # the gentle "go to bed" nudge starts after this hour
BEDTIME_REPEAT_MINUTES = 60
SLEEP_AFTER_IDLE_SECONDS = 60
MORNING_START_HOUR = 5
MORNING_END_HOUR = 11

# Fullscreen / presentation awareness (window sizes only, never window titles)
FULLSCREEN_POLL_SECONDS = 3.0

# Multi-monitor
SCREEN_HOP_SECONDS = 120         # roughly how often he wanders to another monitor
