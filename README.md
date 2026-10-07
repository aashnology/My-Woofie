# 🐶 Aspen

**A digital companion that lives on your desktop and looks after you while you work.**

![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green) ![License: MIT](https://img.shields.io/badge/license-MIT-yellow)

## Introduction

Long stretches at a screen are easy to lose track of. Aspen is a pixel-art puppy who sits on top of your desktop, trots after your cursor, and keeps quiet company while you work. After **4 hours of continuous computer use** he barks, shows a speech bubble and counts down a break. When the break is over, he calls you back with a gentle chime.

He is a companion first and a timer second: friendly, a little silly, and built to be easy to read, change and run locally.

![Choose your pup](docs/images/selector.png)

## Meet the pups

Pick your favorite on first launch (you can change it any time from the tray menu).

| | | |
|:---:|:---:|:---:|
| <img src="docs/images/avatars/aspen.png" width="140"><br>**Aspen**<br>Golden retriever | <img src="docs/images/avatars/biscuit.png" width="140"><br>**Biscuit**<br>Cream puppy | <img src="docs/images/avatars/cocoa.png" width="140"><br>**Cocoa**<br>Chocolate lab |
| <img src="docs/images/avatars/bailey.png" width="140"><br>**Bailey**<br>Beagle | <img src="docs/images/avatars/benny.png" width="140"><br>**Benny**<br>Bernese pup | <img src="docs/images/avatars/snow.png" width="140"><br>**Snow**<br>Fluffy white pup |

## What Aspen does

- **Follows your cursor.** He roams the screen edge when you are idle, then trots (or runs, if you are far away) toward the cursor whenever you move the mouse.
- **Tracks continuous use.** A focus timer runs while you are at the computer. It resets only after 15 minutes without mouse movement, which means you really were away.
- **Nudges you to take a break.** At the limit he runs to mid-screen, barks, and shows a speech bubble with a break message.
- **Counts down your break** on a retro game-style HUD and calls you back with a soft chime and a "back to work" message.
- **Speaks in text when it is quiet.** Mute him from the tray menu or set `AUDIO_ENABLED = False` and every alert appears as a speech bubble instead.
- **Rotates your own messages.** Edit `break_prompts.txt` and `focus_prompts.txt` to change what he says.
- **Reacts to pats.** Click him and he hops happily. Clicks anywhere else pass through to your apps.
- **Remembers your choices.** Avatar and mute state are saved locally.

![HUD and speech bubble](docs/images/hud-and-bubble.png)

## What Aspen does not do

- He does **not** capture your screen, log keystrokes, read your files or record window titles.
- He does **not** use the network. No accounts, analytics, or cloud services.
- He does **not** lock your screen or block your input. He nudges; you decide.
- He does **not** know what you are doing. Presence comes only from elapsed time and mouse movement, so reading or typing without touching the mouse for 15 minutes counts as being away.
- He does **not** follow you across multiple monitors (the primary screen only) or start automatically at login.
- He does **not** ship with recorded audio. The bark, howl and chime are synthesized; drop your own WAV files in `assets/audio/` to replace them.

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

The project ships in `TEST_MODE`: the 4-hour timer is 10 seconds and the break is 5 seconds, so you can watch the full cycle in about 20 seconds (keep moving the mouse). Set `TEST_MODE = False` in `config.py` for real use. Quit from the tray icon menu or with `Ctrl+C`.

Use `python main.py --select` to reopen the avatar picker.

## Customizing

- **Messages:** one per line in `break_prompts.txt` and `focus_prompts.txt` (lines starting with `#` are ignored). Changes apply without restarting. Set `PROMPT_ORDER` to `"sequential"` or `"random"` in `config.py`.
- **Sounds:** `assets/audio/puppy_bark.wav` and `soft_howl.wav` play when the break starts, and `soft_chime.wav` when it ends. Replace any file, or change the mapping in `SOUND_EVENTS`.
- **Art:** animation frames live in `assets/images/<avatar>/`. Replace any PNG to restyle a frame.
- **Everything else:** timers, speed, HUD and bubble settings are constants at the top of `config.py`.

## Learn more

How the code works (timer logic, state machine, rendering, audio, assets pipeline and a configuration reference) is documented in [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md).

## Credits

- Beagle, Bernese pup and fluffy pup artwork from the project's design sheet.
- Pixel font: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P), licensed under the SIL Open Font License (`assets/fonts/OFL.txt`).

## License

Released under the [MIT License](LICENSE). © 2026 Aashna Batabyal.
