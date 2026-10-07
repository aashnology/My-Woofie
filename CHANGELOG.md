# Changelog

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
