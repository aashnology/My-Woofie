# Woof

# 🐕 Aspen — The Desktop Break Enforcement Companion

Aspen is a lightweight desktop virtual pet for Windows and macOS. He roams the edge of your screen, follows your cursor when you move it, and, after **4 hours of continuous computer use**, barks at you until you step away. When your break is over, he calls you back to work.

Everything runs locally. There are no API calls, no accounts and no network access.

---

## Table of Contents

- [Features](#features)
- [Privacy](#privacy)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Test Mode](#test-mode)
- [Audio Fallbacks](#audio-fallbacks)
- [Logging](#logging)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- **Transparent desktop overlay**: a borderless, always-on-top window with a transparent background.
- **Click-through**: your clicks pass through Aspen to the apps underneath unless you interact with him directly.
- **Animated states**: separate sprite animations for roaming, chasing, barking and calling you back.
- **4-hour focus timer**: tracks continuous usage and triggers a break alert when the limit is reached.
- **Configurable break timer**: a 15-minute default, editable in one file.
- **Smart reset**: the focus timer resets only after you have genuinely been away for 15 continuous minutes.
- **Audio alerts**: a bark when it is time to stop, a whistle when it is time to return.
- **Graceful fallbacks**: missing audio files or sound libraries fall back to system beeps instead of crashing.
- **Readable logs**: every state transition is printed to the terminal.

## Privacy

Aspen is built to be non-invasive. He does **not**:

- capture screen pixels or screenshots
- log keypresses
- read file contents
- read or log active window titles
- send any data over the network

Activity detection relies only on **elapsed time** and **mouse displacement thresholds**. Aspen needs to know that the pointer moved, not what you were doing.

## How It Works

### Session lifecycle

```
FOCUS  ──(4h of continuous use)──▶  BARK  ──▶  BREAK  ──(break timer hits 0)──▶  HAUL  ──▶  FOCUS
```

1. **FOCUS**: Aspen tracks continuous usage. If no mouse movement is detected for 15 continuous minutes, you are considered away and the focus timer resets.
2. **BARK**: when the focus limit is reached, Aspen plays `bark.wav`, shows a warning banner and starts the break timer.
3. **BREAK**: the break countdown runs while you are away from the screen.
4. **HAUL**: when the break timer reaches 0, Aspen plays `return.wav` and shows a desktop notification asking you to return to work.

### Pet state machine

| State | Trigger | Behavior |
|---|---|---|
| `ROAM_STATE` | Default | Wanders randomly around the desktop perimeter |
| `CHASE_STATE` | Cursor movement detected | Moves toward the current `(x, y)` mouse position at `PET_SPEED` |
| `BARK_ALERT_STATE` | Focus limit reached | Plays the bark sound, shows the break warning and starts the break timer |
| `HAUL_ALERT_STATE` | Break timer reaches 0 | Plays the return sound and shows the "back to work" notification |

Each state maps to a sprite animation in the GUI layer: `IDLE`, `CHASE`, `BARK`, `HAUL`.

## Tech Stack

- **Python 3**
- **PyQt6**: transparent, frameless overlay window and animations
- **pynput**: mouse position tracking (no keyboard logging)
- **psutil / os**: lightweight system utilities
- **pygame.mixer** (optional): audio playback, with `winsound` / system bell fallback

All core mechanics (timers, state machine, cursor tracking, audio triggers) are plain, local Python with hardcoded logic, so every behavior can be read, debugged and changed directly.

## Project Structure

```
aspen/
├── main.py          # Entry point: wires the GUI, timer engine and pet together
├── gui.py           # Transparent overlay window, click-through, sprite rendering
├── timer.py         # Focus/break timers and mouse-activity detection
├── pet.py           # Finite state machine controlling Aspen's behavior
├── config.py        # Hardcoded constants (timers, speed, audio, test mode)
├── requirements.txt
├── assets/
│   ├── images/      # Sprite frames for IDLE, CHASE, BARK, HAUL
│   └── audio/
│       ├── bark.wav
│       └── return.wav
└── README.md
```

All assets are loaded with paths relative to the source file (`os.path.dirname(__file__)`), so the project runs from any working directory.

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/aspen.git
cd aspen

# 2. (Recommended) create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

**Example `requirements.txt`:**

```
PyQt6
pynput
psutil
pygame
```

> **macOS note:** `pynput` needs permission to observe mouse input. If Aspen does not react to your cursor, open *System Settings → Privacy & Security → Input Monitoring* (and *Accessibility*) and allow your terminal or VS Code.

## Usage

```bash
python main.py
```

Aspen appears on your desktop and starts roaming. Leave him running in the background while you work.

To stop him, press `Ctrl + C` in the terminal where he is running.

## Configuration

All tunable values live at the top of `config.py`:

```python
# Hardcoded Constants
TEST_MODE = True  # If True, 4 hours -> 10 seconds for rapid debugging
FOCUS_TIME_LIMIT_SECONDS = 10 if TEST_MODE else 4 * 3600
BREAK_TIME_LIMIT_SECONDS = 5 if TEST_MODE else 15 * 60
PET_SPEED = 5
AUDIO_ENABLED = True
```

| Constant | Default (live) | Description |
|---|---|---|
| `TEST_MODE` | `True` | Shrinks timers so you can test the full cycle in seconds |
| `FOCUS_TIME_LIMIT_SECONDS` | `4 * 3600` | Continuous usage allowed before the break alert |
| `BREAK_TIME_LIMIT_SECONDS` | `15 * 60` | Length of the enforced break |
| `PET_SPEED` | `5` | Pixels moved per update when roaming or chasing |
| `AUDIO_ENABLED` | `True` | Turns bark and whistle sounds on or off |

**Set `TEST_MODE = False` before using Aspen for real.**

## Test Mode

With `TEST_MODE = True`, the focus limit becomes 10 seconds and the break becomes 5 seconds. Run `python main.py` in the VS Code terminal and you will see the whole cycle (FOCUS → BARK → BREAK → HAUL) within about 15 seconds.

## Audio Fallbacks

Aspen never crashes because of sound:

1. He tries `pygame.mixer` to play `bark.wav` and `return.wav`.
2. If pygame is unavailable or a file is missing, he falls back to `winsound.Beep` on Windows.
3. On other systems he uses the terminal bell.

Set `AUDIO_ENABLED = False` to silence him entirely.

## Logging

Aspen uses Python's built-in `logging` module and prints to the console. State transitions look like this:

```
INFO  | State change: FOCUS -> BARK
INFO  | State change: BARK -> BREAK
INFO  | State change: BREAK -> HAUL
INFO  | State change: HAUL -> FOCUS
```

## Roadmap

Ideas for future versions (not implemented yet):

- [ ] Packaged executables for Windows and macOS
- [ ] Additional pet skins and animations
- [ ] System tray icon with pause and snooze controls
- [ ] Optional daily break statistics, stored locally only

## License

Add your preferred license here (for example MIT) and include a `LICENSE` file in the repository.
