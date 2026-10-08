# Changelog

## 2.0.1

- **Timer prompt at every start:** the focus and break dialog now appears on every launch (after a Windows test showed it only appeared the first time). The dialog has an **ASK ME EVERY TIME I START** tick box, also available in Settings, System. Untick it to keep your saved times. Cancelling keeps the saved times, and `--focus` / `--break` / `--test` skip the prompt.
- **Dog size locked at 53 x 47 pixels** (approved on a real Windows desktop). The size is documented in `config.py`, and tests fail if any current or future avatar, with or without an accessory, is a different size.

## 2.0.0 (Version 2)

- **Snooze:** "Snooze 5 min" on the break card, limited per focus cycle (default 2, configurable 0 to 5). Snoozes are counted in the stats and lower mood.
- **Break quality:** a break counts as taken only if the mouse stayed mostly still (under 25% active); otherwise it is recorded as skipped.
- **Micro-breaks:** rotating 20-second eye rest, stretch, water and posture reminders between big breaks, with Done / Skip. Never close to a big break, never while you are away or in fullscreen.
- **Break guidance:** `break_tips.txt` supplies specific tips shown on the break card and rotating during the break.
- **Settings window** (tabs: Timers, Pet, Sound, System, Data) replacing the timer-only dialog; volume slider; speed slider.
- **Mood and streaks:** mood from break behaviour, pats, treats and fetch; droopy dogs walk slower; healthy-day streak (one missing day is forgiven).
- **Interaction:** click-and-hold petting with hearts, treats (5 a day) and a draggable, throwable fetch ball.
- **Time of day:** night naps when idle, morning stretch and greeting, bedtime nudges.
- **Wardrobe:** six accessories (party hat, flower, beanie, bandana, top hat, crown) unlocked at 1, 3, 5, 7, 10 and 14 streak days.
- **Fullscreen and presentation awareness:** Windows via window and monitor sizes; macOS via optional Quartz; manual Presentation mode everywhere. Only sizes are compared, never titles.
- **Multi-monitor:** roams between monitors, chases the cursor across them, alerts and HUD appear on the cursor's monitor; reacts to monitors being plugged or removed.
- **Start at login** (Windows registry Run key, macOS LaunchAgent, Linux autostart file) and a richer tray menu (click for status, double-click to pause).
- **Local stats:** weekly summary window, `--stats`, **Delete my data** and `--delete-data`, optional recording switch.
- **Packaging:** PyInstaller spec, `packaging/build.py`, GitHub Actions release workflow (`.github/workflows/release.yml`), per-user data folder for packaged apps.
- New modules: `companion.py`, `stats.py`, `mood.py`, `microbreak.py`, `tips.py`, `daypart.py`, `toys.py`, `wardrobe.py`, `dialogs.py`, `fullscreen.py`, `autostart.py`, `paths.py`. `main.py` is now a thin launcher.
- Tests grew from 19 to 101.

## 1.0.0 (Version 1)

First complete release of My-Woofie.

- Six pixel-art dogs: Aspen, Biscuit, Cocoa (drawn in code) and Bailey, Benny, Snow (built from the design sheet), each with ten animation frames.
- Every dog is drawn on a fixed 53 × 47 pixel canvas.
- Retro avatar picker with an "ask me every time" option; dismissing it is never remembered.
- Cursor following with slow, calm movement; roaming along the screen edge when idle.
- Focus and break timer with presence detection (15 minutes without mouse movement resets the session).
- Adjustable focus and break times (dialog, command line or `config.py`); defaults 4 hours and 15 minutes.
- Bark, soft howl and soft chime on break start and end, with beep fallbacks.
- Pixel speech bubbles in silent mode (or always), with rotating messages from `break_prompts.txt` and `focus_prompts.txt`.
- Retro HUD with focus meter, break countdown and a back-to-work flash.
- Right-click and tray menu: pause, timer settings, change avatar, focus meter, mute, reset all settings, quit.
- Stop from the command line (`--stop`), single-instance protection, `--reset`, `--select`, `--test`, `--version`.
- Settings saved locally; no network access, screen capture or key logging.
- User guide, technical guide, unit tests and MIT license.
