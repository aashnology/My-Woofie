# Aspen Technical Guide

This guide explains how Aspen works internally: the architecture, the logic of each module, the features built on top, and how to extend them. For installation and a feature overview, see the [README](../README.md).

## Contents

1. [Design principles](#1-design-principles)
2. [Architecture at a glance](#2-architecture-at-a-glance)
3. [The main loop](#3-the-main-loop)
4. [Timer engine (`timer.py`)](#4-timer-engine-timerpy)
5. [Pet state machine (`pet.py`)](#5-pet-state-machine-petpy)
6. [Windows and rendering (`gui.py`, `retro.py`)](#6-windows-and-rendering-guipy-retropy)
7. [Avatar selection, settings and menus](#7-avatar-selection-settings-and-menus)
8. [Audio (`audio.py`)](#8-audio-audiopy)
9. [Speech bubbles and message banks (`prompts.py`)](#9-speech-bubbles-and-message-banks-promptspy)
10. [Asset pipeline (`assets_builder.py`, `tools/`)](#10-asset-pipeline-assets_builderpy-tools)
11. [Configuration reference](#11-configuration-reference)
12. [Logging and debugging](#12-logging-and-debugging)
13. [Extending Aspen](#13-extending-aspen)
14. [Known limitations](#14-known-limitations)

---

## 1. Design principles

- **Local and hardcoded.** All timers, state logic, cursor tracking and audio triggers are plain Python. There are no API calls or network access.
- **Privacy by construction.** Aspen never captures pixels, logs keys, reads files or records window titles. The only inputs are the clock and the cursor position.
- **Modular.** Each concern lives in one module with a small interface, so any piece can be debugged or replaced on its own.
- **Never crash on missing resources.** Missing sprites are redrawn in memory, missing audio falls back to a system beep, and missing prompt files fall back to a built-in message.
- **Easy to debug.** `python main.py --test` shrinks the 4-hour timer to 10 seconds, and every state change is logged.

## 2. Architecture at a glance

```
                      ┌───────────────┐
        QCursor.pos() │   main.py     │  AspenApp: owns everything,
        ─────────────▶│  (controller) │  runs the 33 ms tick
                      └──────┬────────┘
        ┌───────────┬────────┼─────────┬──────────────┬────────────┐
        ▼           ▼        ▼         ▼              ▼            ▼
   timer.py      pet.py   gui.py    audio.py      prompts.py   settings.py
                                                                      timer_dialog.py
 SessionTimer     Pet    PetWindow  SoundPlayer   PromptBank    Settings
 (phases)      (FSM +    HudWindow  (events,      (message      (avatar,
               movement) BubbleWin  fallbacks)    rotation)     mute)
                            │
                 retro.py (pixel font + boxes)      selector.py (avatar picker)
                 assets_builder.py (sprites + sounds)    config.py (constants)
```

`main.py` is the only module that knows about all the others. The timer, pet, prompts and settings modules do not import each other (apart from `pet.py` using the `Phase` enum), so each can be tested in isolation.

## 3. The main loop

`AspenApp._tick` runs every `FRAME_INTERVAL_MS` (33 ms, about 30 frames per second) from a `QTimer`:

1. Read the cursor position with `QCursor.pos()`.
2. Feed it to `SessionTimer.update()`. If the phase changes, call `_on_phase`.
3. Decide whether to chase: Aspen chases while the mouse moved within the last `CHASE_WINDOW_SECONDS`.
4. Call `Pet.update()` to advance the state machine and position.
5. Sync the pet window: position, animation, facing and bob offset.
6. Move or expire the speech bubble.
7. Refresh the HUD.

Using `QCursor.pos()` instead of a global input hook keeps coordinates identical to Qt window coordinates and needs no operating-system permission.

## 4. Timer engine (`timer.py`)

`SessionTimer` tracks one repeating cycle with three phases:

```
FOCUS ──(focus limit reached)──▶ BREAK ──(break time elapsed)──▶ HAUL ──(display time elapsed)──▶ FOCUS
```

| Phase | Meaning | Leaves when |
|---|---|---|
| `FOCUS` | The user is working. | `focus_limit` seconds of continuous use have passed. |
| `BREAK` | Aspen is barking; the break countdown runs. | `break_limit` seconds have passed. |
| `HAUL` | Break is over; Aspen calls the user back. | `haul_display` seconds have passed, then a new focus session starts. |

### Presence detection

- A position only counts as movement if it is at least `MOUSE_MOVE_THRESHOLD_PX` away from the last position that counted. This filters out tiny jitters.
- `_last_activity` stores the time of the last counted movement.
- At each update, **before** recording new movement, the timer computes `idle = now - _last_activity`. If the phase is `FOCUS`, a session is running and `idle >= away_reset`, the session is cleared. The next movement starts a fresh session. Checking idle time before recording movement means a long gap, such as a laptop sleeping, is correctly treated as time away.

### Adjustable limits

`SessionTimer(focus_limit, break_limit, away_reset, haul_display)` takes its durations as arguments and falls back to `config.py`. `main.py` works out the values for the run (`resolve_timers`): test mode uses the `TEST_*` constants; otherwise the order is command-line flags (`--focus`, `--break`), then the saved `settings.json` values, then `DEFAULT_FOCUS_MINUTES` / `DEFAULT_BREAK_MINUTES`. `set_limits()` and `restart_focus()` apply a change made in the Timer settings dialog without restarting the app.

### Time source

The timer uses `time.monotonic()`, which is not affected by clock changes. The clock is injectable (`SessionTimer(clock=...)`), so tests can simulate hours in milliseconds with a fake clock.

### Public interface

| Member | Purpose |
|---|---|
| `update(position)` | Process one cursor sample. Returns the new `Phase` if it changed, else `None`. |
| `focus_elapsed()` | Seconds into the current focus session (0 when away). |
| `break_remaining()` | Seconds left in the break. |
| `seconds_since_move()` | Time since the last counted movement (drives chasing). |
| `moved_now` | Whether the latest sample counted as movement. |

## 5. Pet state machine (`pet.py`)

`Pet` is a finite state machine with four states and no Qt dependency, so it works on plain numbers.

| State | Entered when | Behavior |
|---|---|---|
| `ROAM_STATE` | Default, or the mouse has been still for `CHASE_WINDOW_SECONDS`, or an alert ends | Walks the screen perimeter, pausing and occasionally reversing. |
| `CHASE_STATE` | The mouse moved recently | Moves toward the cursor; stops `CHASE_STOP_DISTANCE_PX` away and sits. |
| `BARK_ALERT_STATE` | Timer enters `BREAK` | Runs to mid-screen at double speed, barking animation, hopping. |
| `HAUL_ALERT_STATE` | Timer enters `HAUL` | Same position, excited animation, bigger hops. |

Alert states take priority: while one is active, cursor chasing is ignored. `set_phase()` is the bridge from timer phases to pet states.

### Movement

- **Chasing.** The target is the cursor offset by half the sprite size so Aspen centers on it. Speed is `PET_SPEED × (1 + 0.5 × min(distance / 600, 1))` (2 to 3 pixels per frame by default), an easy amble that is a little quicker when the cursor is far away. He stops `CHASE_STOP_DISTANCE_PX` from the cursor.
- **Roaming.** Roaming speed is half of `PET_SPEED`, with frequent rests of two to six seconds. The screen edge is treated as a rectangular loop of length `2 × (width + height)`. Aspen keeps a single distance `s` along that loop. `_point_at(s)` converts it to coordinates, and moving is just increasing or decreasing `s`. This is why he follows the edge cleanly, including around corners.
- **Returning to the edge.** When roaming resumes from elsewhere (after chasing or an alert), `_nearest_s()` finds the closest point on the loop and Aspen walks there in a straight line before rejoining it.
- **Bounds.** Positions are clamped to the screen. `set_size()` recomputes bounds when the avatar (and sprite size) changes.

### Animation selection

`Pet.animation(now)` returns one of `bark`, `haul`, `happy` (just patted), `walk` (moving) or `idle`. `Pet.bob(now)` returns a vertical offset using `abs(sin(...))`, which makes a hop. Hop height scales with the sprite height so a small dog does not leap around, and the hop rates are deliberately slow. The GUI picks the frame by time: `index = int(now × 1000 / ANIMATION_FRAME_MS) % frame_count`.

## 6. Windows and rendering (`gui.py`, `retro.py`)

Aspen is three borderless, always-on-top, translucent windows (`Qt.Tool` keeps them out of the taskbar).

| Window | Click-through | Notes |
|---|---|---|
| `PetWindow` | Partly | The window mask is set from the sprite's opaque pixels, so clicks on transparent areas pass to the apps below, while clicks on the dog reach Aspen (pats). |
| `HudWindow` | Fully (`WindowTransparentForInput`) | Top-center status bar. |
| `BubbleWindow` | Fully | Follows the dog's head. |

### Sprite scaling and flipping

- **Cropping.** `load_frames()` finds the smallest box containing the dog across all of an avatar's frames and crops every frame to it. The dog's size is therefore independent of the canvas.
- **Scaling.** The target size (`SPRITE_TARGET_PX`, default 40, or the size chosen in the menu) refers to the dog's longest side. For large sizes (a factor of 1.8 or more) frames are scaled by a whole number with nearest-neighbor so pixels stay sharp. For small sizes the frame is enlarged 4× with nearest-neighbor and then reduced smoothly to the exact size, which keeps a tiny dog readable.
- Facing is handled by mirroring the pixmap. Each avatar declares its native facing (Bailey's art faces left), and the window flips whenever the pet's direction differs from it.
- Mirrored pixmaps and their masks are cached so nothing is recomputed per frame.

### Retro styling (`retro.py`)

- **Font:** the bundled Press Start 2P, loaded with `QFontDatabase`, falling back to Courier New. Antialiasing is disabled for crisp pixels.
- **Pixel boxes:** `draw_box()` fills a rectangle as a cross of two overlapping rectangles, giving notched corners, then draws a smaller one inside for the border and a translucent copy offset by the border width as a drop shadow.
- **HUD:** 16 segments, colored green, amber then red as the focus meter fills, blue while counting down the break, and a flashing gold "BACK TO WORK!" at the end.
- **Bubble:** text is wrapped manually with `QFontMetrics` so line spacing stays readable in the bitmap font. The window is sized to the text, and a small stepped tail points at the dog.

## 7. Avatar selection, settings and menus

- `available_avatars()` lists the avatars whose art exists. The selector shows each as a card with its idle frame.
- Inputs: arrow keys, mouse click, double-click or Enter/Space to confirm, Esc to cancel. The selected card's border blinks.
- `AvatarSelector.choose(current)` shows the dialog modally and returns the id or `None`. Previews are loaded at 150 px, independent of the on-screen size.
- **Flow:** on startup `pick_avatar()` uses the saved avatar when there is one, and otherwise (or with `--select`) opens the selector. The tray menu's "Change avatar..." swaps the avatar live: new frames, new native facing, new pet size.
- `Settings` is a small JSON file (`settings.json`, git-ignored) holding `avatar`, `muted`, `size_px`, `hud_always`, `focus_minutes` and `break_minutes`. Read and write errors are logged and never fatal.
- **Timer settings.** `timer_dialog.py` is a styled `QDialog` with two spin boxes (focus 1 to 720 minutes, break 1 to 120) and preset buttons. It runs on first launch, with `--settings`, and from the menu.
- **Menu.** `AspenApp._build_menu()` creates one `QMenu` (timer settings, avatar, size, focus meter, mute, quit). It is attached to the tray icon and also shown when the pet window emits `menu_requested` (right-click), so the controls are reachable even if the tray icon is hidden.
- **Command line.** `--select`, `--settings`, `--test`, `--focus MIN`, `--break MIN`, parsed with `argparse` (`parse_known_args`, so Qt's own flags still pass through).

## 8. Audio (`audio.py`)

- **Events, not files.** `config.SOUND_EVENTS` maps events to sounds with delays in milliseconds:

  ```python
  "break_start": [("puppy_bark", 0), ("soft_howl", 650)],
  "break_end":   [("soft_chime", 0)],
  ```

  `play_event()` plays zero-delay sounds immediately and schedules the others with `QTimer.singleShot`, which is how the howl layers after the bark without blocking the app.
- **Preloading.** At startup every sound named in `SOUND_EVENTS` is loaded into `pygame.mixer` with its volume from `SOUND_VOLUMES`.
- **Fallback chain.** pygame → on Windows `winsound.PlaySound` (or `Beep`) → `QApplication.beep()` → terminal bell. Any failure is logged and the chain continues.
- **Silent mode.** `SoundPlayer.silent` is true when muted or when `AUDIO_ENABLED` is false. In that case nothing plays and the app relies on speech bubbles.
- Desktop apps have no browser-style autoplay restrictions; "silent mode" is the equivalent safety net.

## 9. Speech bubbles and message banks (`prompts.py`)

- `PromptBank(path, fallback, order)` reads a text file: one message per line, blank lines and `#` comments ignored.
- **Rotation:** `"sequential"` walks the lines and wraps around; `"random"` picks a random line that differs from the previous one.
- **Live reload:** the file's modification time is checked on every `next()`, so edits apply without restarting. If the file is missing or empty, a built-in message is used (a warning is logged once).
- `AspenApp._say()` shows the bubble when `ALWAYS_SHOW_BUBBLES` is true or the player is silent, and removes it after `BUBBLE_SECONDS`.
- Triggers: entering `BREAK` uses the break bank; entering `HAUL` uses the focus bank (and also a tray notification when available).

## 10. Asset pipeline (`assets_builder.py`, `tools/`)

Assets are generated on first run, and existing files are never overwritten, so anything can be replaced by hand.

### Sprites: ten frames per avatar

`idle_0/1`, `walk_0/1`, `bark_0/1`, `haul_0/1`, `happy_0/1`, saved to `assets/images/<avatar>/`. The `POSES` table lists each pose's parameters (tail position, eyes, mouth, ear lift, head and body offset, paw lift).

### Drawn avatars (Aspen, Biscuit, Cocoa)

- Painted on a 32×32 canvas with `QPainter`, antialiasing off, using ellipses with a slightly larger black ellipse behind each as an outline.
- A palette dictionary makes a new color variant a few hex codes.
- A **shading pass** (`_shade`) then adds the cell-shaded look: pixels next to the lower or right edge are darkened, pixels next to the upper or left edge are lightened, and eyes, tongue, tag and cheeks are left untouched.

### Design avatars (Bailey, Benny, Snow)

- Base sprites in `assets/designs/<avatar>.png` (48×48 canvas) come from the design sheet via `tools/import_designs.py`:
  1. Extract the page images with `pdfimages`.
  2. Crop to the artwork and detect the source pixel grid (cell size and phase) by looking for periodic edges.
  3. Take the median color of each cell, which removes JPEG noise and keeps colors saturated.
  4. Quantize to a small palette, flood-fill the background from the borders (so white fur inside the outline is kept), snap near-black pixels to a single outline color, and drop stray specks.
- Animation frames are made by editing the base grid (`render_design_pose`):
  - **Head lift:** shift the head rectangle up one or two cells and stretch its bottom row so it stays joined.
  - **Paw lift:** shift one side's bottom rows up.
  - **Open mouth:** a dark block with a pink tongue pixel at the mouth anchor.
  - **Happy eyes:** paint over the eye with the surrounding face color and draw a dark closed-eye line.
- Each design's `spec` in `AVATARS` holds the head box, foot row, eye and mouth coordinates.

### Sounds

All three are synthesized with the standard library (no numpy), written as 16-bit mono WAV files at 22.05 kHz.

- **Puppy bark:** two yaps. Each has a falling pitch contour, a harmonic stack shaped by two formant peaks (around 900 Hz and 2.3 kHz) to mimic a vocal tract, a breathy noise burst at the onset, and a fast attack with exponential decay.
- **Soft howl:** a 1.9-second gliding tone with gentle vibrato that fades in and out, built from a few harmonics at low volume.
- **Soft chime:** two bell-like notes (B5 then E6) built from three partials with different decay rates.

## 11. Configuration reference

All values live in `config.py`.

| Constant | Default | Meaning |
|---|---|---|
| `TEST_MODE` | `False` | `True` (or `--test`) uses 10 s focus, 5 s break, 8 s away. |
| `DEFAULT_FOCUS_MINUTES` | 240 | Focus time when nothing else is chosen. |
| `DEFAULT_BREAK_MINUTES` | 15 | Break length when nothing else is chosen. |
| `TEST_FOCUS_SECONDS`, `TEST_BREAK_SECONDS`, `TEST_AWAY_SECONDS`, `TEST_HAUL_SECONDS` | 10, 5, 8, 4 | Test-mode timings. |
| `AWAY_RESET_SECONDS` | 15 min | Mouse stillness that counts as being away. |
| `HAUL_DISPLAY_SECONDS` | 20 | How long the back-to-work state lasts. |
| `MOUSE_MOVE_THRESHOLD_PX` | 6 | Smallest movement that counts. |
| `PET_SPEED` | 2 | Base pixels per frame (roaming uses half). |
| `AUDIO_ENABLED` | `True` | Master sound switch. |
| `DEFAULT_AVATAR` | `"aspen"` | Highlighted in the selector on first run. |
| `CHASE_WINDOW_SECONDS` | 3.0 | How long he keeps following after the last movement. |
| `CHASE_STOP_DISTANCE_PX` | 50 | How close he gets to the cursor. |
| `SOUND_EVENTS`, `SOUND_VOLUMES` | see file | Which sounds play on which event, with delays and volumes. |
| `SHOW_HUD` | `True` | Allow the top HUD at all. |
| `HUD_ALWAYS_VISIBLE` | `False` | `False` = HUD only during breaks (menu can override). |
| `ALWAYS_SHOW_BUBBLES` | `True` | `False` = bubbles only when silent. |
| `BUBBLE_SECONDS` | 8 | Bubble lifetime. |
| `PROMPT_ORDER` | `"sequential"` | Or `"random"`. |
| `SPRITE_TARGET_PX` | 40 | Default on-screen size of the dog's longest side. |
| `SIZE_CHOICES` | Tiny 32, Small 40, Medium 64, Large 96 | Sizes offered in the menu. |
| `FRAME_INTERVAL_MS` | 33 | Tick rate. |
| `ANIMATION_FRAME_MS` | 400 | Time per animation frame. |
| `LOG_LEVEL` | `"DEBUG"` | Console log verbosity. |

## 12. Logging and debugging

Python's `logging` module prints to the terminal (visible in the VS Code console). Typical output:

```
INFO | aspen.timer    | Phase FOCUS -> BREAK
INFO | aspen.pet      | State CHASE_STATE -> BARK_ALERT_STATE
INFO | aspen.prompts  | Loaded 5 prompts from break_prompts.txt
INFO | aspen.timer    | Phase BREAK -> HAUL
```

Debugging tips:

- Run `python main.py --test` (or set `TEST_MODE = True`) and move the mouse steadily to see a full cycle in about 20 seconds. If the mouse is still for 8 seconds the focus timer resets.
- Logger names (`aspen.timer`, `aspen.pet`, `aspen.audio`, ...) identify the module a message came from.
- The timer and pet have no Qt dependency, so you can script them in a plain Python shell with a fake clock.

## 13. Extending Aspen

- **Add an avatar.** Add an entry to `AVATARS`. A drawn avatar needs a palette; a design avatar needs `assets/designs/<id>.png` and a `spec`. It then appears in the selector.
- **Change messages or sounds.** Edit the text files, replace WAV files, or change `SOUND_EVENTS`.
- **Add a new alert.** Add a phase in `timer.py`, a state in `pet.py` mapped in `set_phase()`, and handle it in `AspenApp._on_phase()`.
- **Change the cycle.** The timer rules are in `_advance()` and `update()`, in one file.

## 14. Known limitations

- Verified with headless runs and unit-style simulations; behavior on real Windows and macOS desktops (click-through masks, tray notifications, audio devices) should be checked on your machine.
- Presence is mouse-only by design, so working without touching the mouse looks like being away.
- Only the primary monitor is used.
- Window masks for click-through can behave differently on macOS.
- There is no start-at-login option or packaged installer yet.
- The default sounds are synthesized and sound artificial compared with real recordings.
