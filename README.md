# 🐶 Aspen: The Desktop Break Enforcement Companion

Aspen is a pixel-art puppy who lives on your desktop (Windows/macOS). Pick your pup from six dogs, and he trots after your cursor while you work. After **4 hours of continuous computer use** he barks, shows a speech bubble and counts down your break. When the break ends he sends a gentle chime and a "back to work" nudge.

Everything runs locally. No network calls, no screen capture, no keylogging, no window titles, no file reading. Presence is detected only from elapsed time and mouse displacement.

## Prerequisites

- Python 3.9+
- pip

## Install and run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The project ships in `TEST_MODE`: the 4-hour timer is 10 seconds and the break is 5 seconds, so you can see the whole cycle in about 20 seconds (keep moving the mouse). Set `TEST_MODE = False` in `config.py` for real use. Quit from the tray menu or with `Ctrl+C`.

## Avatar selection flow

1. On first launch a retro "CHOOSE YOUR PUP" screen appears with six dogs:
   - **Aspen** (golden retriever), **Biscuit** (cream puppy) and **Cocoa** (chocolate lab), drawn in code
   - **Bailey** (beagle), **Benny** (Bernese pup) and **Snow** (fluffy white pup), built from the artwork in `Aspen_designs.pdf`
2. Pick one with the mouse or the arrow keys, then click **START** or press Enter.
3. Your choice is saved in `settings.json` (git-ignored) and used on every later launch.
4. To change it later, use **Change avatar...** in the tray menu, or run `python main.py --select`.

## Cursor interaction

| State | Behavior |
|---|---|
| `ROAM_STATE` | Walks around the screen edge and pauses now and then |
| `CHASE_STATE` | Trots after your cursor whenever you have moved the mouse in the last 5 seconds, running faster the farther away you are, and sits down near it |
| `BARK_ALERT_STATE` | Runs to mid-screen and barks when the focus limit is reached |
| `HAUL_ALERT_STATE` | Bounces excitedly when the break ends |

Click Aspen to pat him. Clicks anywhere else on his window pass through to your apps. The focus timer resets only after 15 minutes (`AWAY_RESET_SECONDS`) without mouse movement.

## Retro HUD and speech bubbles

- A pixel-art **HUD** at the top of the screen shows a focus meter (green → amber → red), the break countdown, and a flashing "BACK TO WORK!" message. Turn it off with `SHOW_HUD = False`.
- **Speech bubbles** appear above Aspen when the break starts ("Time for a break!") and when it ends ("Time to get back to focus!"). They always appear in silent mode (sounds muted or `AUDIO_ENABLED = False`). With sound on, `ALWAYS_SHOW_BUBBLES = True` shows them too; set it to `False` for bubbles only when silent.
- Mute from the tray menu (**Mute sounds**) to switch to bubble-only alerts. The choice is remembered.

## Sounds and triggers

Sounds live in `assets/audio/` and are preloaded at startup. Missing files or a missing sound library fall back to system beeps, so audio never crashes the app.

| Event | Trigger | Sounds |
|---|---|---|
| `break_start` | Focus timer reaches its limit | `puppy_bark.wav`, then `soft_howl.wav` 650 ms later |
| `break_end` | Break timer reaches zero | `soft_chime.wav` |

The mapping and volumes are in `config.py` (`SOUND_EVENTS`, `SOUND_VOLUMES`). The default bark, howl and chime are synthesized on first run. To use a real recording, drop your own WAV into `assets/audio/` with the same file name, for example `puppy_bark.wav`. Existing files are never overwritten.

## Customizing messages

Speech bubble text comes from two plain text files in the project root:

- `break_prompts.txt` — shown when it's time to take a break
- `focus_prompts.txt` — shown when it's time to get back to work

Write one message per line. Blank lines and lines starting with `#` are ignored. Files are re-read when they change, so edits apply without restarting Aspen. Set `PROMPT_ORDER` in `config.py` to `"sequential"` (default) or `"random"`. If a file is missing or empty, Aspen falls back to a built-in message.

## Art style and custom avatars

All avatars share one look: chunky near-black outlines, flat cell shading (lighter top-left edges, darker bottom-right edges) and a warm palette. Each dog has ten frames: `idle_0/1`, `walk_0/1`, `bark_0/1`, `haul_0/1` and `happy_0/1`, stored in `assets/images/<avatar>/`. Replace any PNG to restyle a frame; existing files are never overwritten.

- **Drawn dogs** (Aspen, Biscuit, Cocoa) are painted in `assets_builder.py` from a small palette, so a recolor is a few hex codes.
- **Design dogs** (Bailey, Benny, Snow) start from a clean base sprite in `assets/designs/<avatar>.png`. Animation frames are made by editing that sprite: head lifts, paw lifts, open mouth and happy eyes, positioned by the `spec` entry in `AVATARS`.
- To regenerate the base sprites from the PDF: `pip install pillow numpy`, install poppler (`pdfimages`), then run `python tools/import_designs.py Aspen_designs.pdf`.
- To add a dog, add an entry to `AVATARS` (and a base sprite in `assets/designs/` for a design dog). It shows up in the selector automatically.

## Configuration

All tunables are in `config.py`: `TEST_MODE`, `FOCUS_TIME_LIMIT_SECONDS`, `BREAK_TIME_LIMIT_SECONDS`, `AWAY_RESET_SECONDS`, `PET_SPEED`, `AUDIO_ENABLED`, `SOUND_EVENTS`, `SHOW_HUD`, `ALWAYS_SHOW_BUBBLES`, `BUBBLE_SECONDS`, `PROMPT_ORDER`, `SPRITE_TARGET_PX`.

## Project structure

```
aspen/
├── main.py              # entry point, app controller, tray menu
├── gui.py               # pet window, retro HUD, speech bubble
├── selector.py          # retro avatar selection screen
├── retro.py             # pixel palette, bitmap font, pixel boxes
├── pet.py               # finite state machine and movement
├── timer.py             # focus/break timers and presence detection
├── audio.py             # preloaded sounds, event sequencing, beep fallbacks
├── prompts.py           # message bank loader and rotation
├── settings.py          # saved avatar and mute state
├── assets_builder.py    # generates avatars and sounds on first run
├── config.py            # all tunable constants
├── break_prompts.txt    # break messages
├── focus_prompts.txt    # back-to-work messages
├── requirements.txt
├── tools/import_designs.py  # PDF artwork -> base sprites (optional)
└── assets/
    ├── designs/         # base sprites for the design dogs
    ├── images/<avatar>/ # animation frames
    ├── audio/           # wav files
    └── fonts/           # Press Start 2P (SIL Open Font License, see OFL.txt)
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Aspen desktop break companion"
git branch -M main
git remote add origin https://github.com/<your-username>/aspen.git
git push -u origin main
```

Add a `LICENSE` file for the code and a screenshot or GIF of Aspen to this README before sharing. The bundled font keeps its own license (`assets/fonts/OFL.txt`).

## Platform notes

- On macOS, the system tray and notifications depend on your notification settings for Terminal/VS Code.
- Mouse position is read through Qt, so no Accessibility or Input Monitoring permission is needed.
