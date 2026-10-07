# 🐶 Aspen

**A digital companion that lives on your desktop and looks after you while you work.**

![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green) ![License: MIT](https://img.shields.io/badge/license-MIT-yellow)

## Introduction

Long stretches at a screen are easy to lose track of. Aspen is a small pixel-art puppy who sits on top of your desktop, ambles after your cursor, and keeps quiet company while you work. After the focus time you choose (4 hours by default) he barks, shows a speech bubble and counts down a break. When the break is over, he calls you back with a gentle chime.

He is a companion first and a timer second: small, calm, a little silly, and easy to read, change and run locally.

![Choose your pup](docs/images/selector.png)

## Meet the pups

Pick your favorite on first launch (you can change it any time from the right-click menu).

| | | |
|:---:|:---:|:---:|
| <img src="docs/images/avatars/aspen.png" width="140"><br>**Aspen**<br>Golden retriever | <img src="docs/images/avatars/biscuit.png" width="140"><br>**Biscuit**<br>Cream puppy | <img src="docs/images/avatars/cocoa.png" width="140"><br>**Cocoa**<br>Chocolate lab |
| <img src="docs/images/avatars/bailey.png" width="140"><br>**Bailey**<br>Beagle | <img src="docs/images/avatars/benny.png" width="140"><br>**Benny**<br>Bernese pup | <img src="docs/images/avatars/snow.png" width="140"><br>**Snow**<br>Fluffy white pup |

## What Aspen does

- **Stays small and calm.** By default he is about twice the size of your mouse cursor and moves slowly, so he does not pull your attention. Size is adjustable from the menu.
- **Follows your cursor.** He wanders the screen edge when you are idle, and ambles toward the cursor while you move the mouse.
- **Uses a focus time you choose.** Set your own focus and break lengths (default 4 hours and 15 minutes) in the timer settings.
- **Tracks continuous use.** The focus timer resets only after 15 minutes without mouse movement, which means you really were away.
- **Nudges you to take a break.** At the limit he barks, shows a speech bubble and counts down the break on a retro game-style HUD, then calls you back with a soft chime.
- **Speaks in text when it is quiet.** Mute him and every alert appears as a speech bubble instead.
- **Rotates your own messages.** Edit `break_prompts.txt` and `focus_prompts.txt` to change what he says.
- **Reacts to pats and a right-click menu.** Click him for a happy hop. Right-click for settings, or to quit.
- **Remembers your choices.** Avatar, size, timers and mute state are saved locally.

![HUD and speech bubble](docs/images/hud-and-bubble.png)

## What Aspen does not do

- He does **not** capture your screen, log keystrokes, read your files or record window titles.
- He does **not** use the network. No accounts, analytics or cloud services.
- He does **not** lock your screen or block your input. He nudges; you decide.
- He does **not** know what you are doing. Presence comes only from elapsed time and mouse movement, so reading or typing without touching the mouse for 15 minutes counts as being away.
- He does **not** follow you across multiple monitors (primary screen only) or start automatically at login.
- He does **not** ship with recorded audio. The bark, howl and chime are synthesized; drop your own WAV files into `assets/audio/` to replace them.

## Quick start

Requirements: Python 3.9+ on Windows or macOS.

```bash
git clone https://github.com/aashnology/Woof.git
cd Woof
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On first launch you choose a pup and your focus and break times. After that Aspen starts straight away.

**Turn him off:** right-click Aspen and choose **Quit Aspen** (or use the tray icon menu, or press `Ctrl+C` in the terminal).

**Try it quickly:** `python main.py --test` makes the focus time 10 seconds and the break 5 seconds, so you can see a full cycle (keep moving the mouse).

Other options: `--select` (pick a different avatar), `--settings` (open the timer settings), `--focus 90 --break 10` (minutes, for one run).

## Customizing

- **Timers, size, avatar, mute:** right-click Aspen (or the tray icon).
- **Messages:** one per line in `break_prompts.txt` and `focus_prompts.txt` (lines starting with `#` are ignored). Changes apply without restarting.
- **Sounds:** replace the files in `assets/audio/`, or change `SOUND_EVENTS` in `config.py`.
- **Art:** animation frames live in `assets/images/<avatar>/`.
- **Everything else:** constants at the top of `config.py`.

## Documentation

- [User guide](docs/USER_GUIDE.md): everyday use, changing the focus time, turning Aspen off, troubleshooting.
- [Technical guide](docs/TECHNICAL_GUIDE.md): how the code works (timers, state machine, rendering, audio, assets, configuration reference).

## Credits

- Beagle, Bernese pup and fluffy pup artwork from the project's design sheet.
- Pixel font: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P), licensed under the SIL Open Font License (`assets/fonts/OFL.txt`).

## License

Released under the [MIT License](LICENSE). © 2026 Aashna Batabyal.
