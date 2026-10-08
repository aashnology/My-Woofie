# 🐶 My-Woofie

**A digital companion that lives on your desktop and looks after you while you work.**

![Version 2.0](https://img.shields.io/badge/version-2.0-orange) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green) ![License: MIT](https://img.shields.io/badge/license-MIT-yellow)

## Introduction

Long stretches at a screen are easy to lose track of. My-Woofie is a tiny pixel-art puppy who sits on top of your desktop, ambles after your cursor, and keeps quiet company while you work. After the focus time you choose (4 hours by default) he barks, shows a speech bubble and counts down a break. When the break is over, he calls you back with a gentle chime.

He is a companion first and a timer second: small, calm, a little silly, and easy to read, change and run locally. This is **Version 2**: snooze, micro-breaks, a settings window, mood and streaks, treats and fetch, a wardrobe, multi-monitor support, local stats and packaged downloads.

![Choose your pup](docs/images/selector.png)

## Meet the pups

Six dogs are part of My-Woofie. Pick yours on first launch, and change your mind any time from the right-click menu.

| | | |
|:---:|:---:|:---:|
| <img src="docs/images/avatars/aspen.png" width="140"><br>**Aspen**<br>Golden retriever | <img src="docs/images/avatars/biscuit.png" width="140"><br>**Biscuit**<br>Cream puppy | <img src="docs/images/avatars/cocoa.png" width="140"><br>**Cocoa**<br>Chocolate lab |
| <img src="docs/images/avatars/bailey.png" width="140"><br>**Bailey**<br>Beagle | <img src="docs/images/avatars/benny.png" width="140"><br>**Benny**<br>Bernese pup | <img src="docs/images/avatars/snow.png" width="140"><br>**Snow**<br>Fluffy white pup |

On your desktop every dog is exactly **53 × 47 pixels**, shown here at true size:

![Actual size](docs/images/actual-size.png)

## What My-Woofie does

- **Stays small and calm.** Every dog is a fixed 53 × 47 pixels, roughly twice a mouse cursor, and moves slowly so he does not pull your attention.
- **Follows your cursor.** He wanders the screen edge when you are idle, and ambles toward the cursor while you move the mouse.
- **Uses a focus time you choose.** Set your own focus and break lengths (default 4 hours and 15 minutes) in the timer settings.
- **Tracks continuous use.** The focus timer resets only after 15 minutes without mouse movement, which means you really were away.
- **Nudges you to take a break.** At the limit he barks, shows a speech bubble and counts down the break on a retro game-style HUD, then calls you back with a soft chime.
- **Speaks in text when it is quiet.** Mute him and every alert appears as a speech bubble instead.
- **Rotates your own messages.** Edit `break_prompts.txt` and `focus_prompts.txt` to change what he says.
- **Lets you pick, switch or reset your dog.** Choose on first launch, tick "ask me every time" to choose at every start, or reset everything from the menu.
- **Is easy to stop.** Right-click and choose Quit, or run `python main.py --stop` from any terminal. You can also pause him.

![HUD and speech bubble](docs/images/hud-and-bubble.png)

## New in Version 2

| Feature | What it does |
|---|---|
| **Snooze with a cost** | "Snooze 5 min" on the break card, limited per focus cycle (default 2). Each snooze lowers his mood. |
| **Micro-breaks** | Every 20 minutes of focus: a 20-second eye rest, stretch, water sip or posture check. Done or Skip. |
| **Break guidance** | The break card suggests something specific (stretch, water, a short walk), rotating from `break_tips.txt`. |
| **Settings window** | Right-click, **Settings...**: timers, speed, sound, night behaviour, start at login, data. |
| **Mood and streaks** | Take real breaks and he is happy; skip them and he droops and walks slower. Healthy days build a streak. |
| **Petting, treats, fetch** | Click and hold to pet. **Give a treat** (5 a day). **Play fetch**: grab the ball, throw it, he brings it back. |
| **Time of day** | Naps when you are idle at night, stretches in the morning, a gentle bedtime nudge when it gets late. |
| **Wardrobe** | Party hat, flower, beanie, bandana, top hat and crown, unlocked by your streak (1, 3, 5, 7, 10, 14 days). |
| **Fullscreen awareness** | Alerts wait and he hides while a program covers a whole monitor, or in **Presentation mode**. |
| **Multi-monitor** | He wanders between monitors and answers alerts on the monitor your cursor is on. |
| **Start at login + tray** | Optional autostart on Windows, macOS and Linux. Tray click shows status, double-click pauses. |
| **Local stats** | Weekly summary of breaks taken and skipped. Stored only on your computer, one-click **Delete my data**. |
| **Packaged builds** | `python packaging/build.py` makes a Windows `.exe` or macOS `.app`; a GitHub Actions workflow attaches them to Releases. |

## What My-Woofie does not do

- He does **not** capture your screen, log keystrokes, read your files or record window titles.
- He does **not** use the network. No accounts, analytics or cloud services.
- He does **not** lock your screen or block your input. He nudges; you decide.
- He does **not** know what you are doing. Presence comes only from elapsed time and mouse movement, so reading or typing without touching the mouse for 15 minutes counts as being away.
- He does **not** read window titles or program names. Fullscreen detection compares window sizes with monitor sizes only.
- He does **not** ship with recorded audio. The bark, howl and chime are synthesized; drop your own WAV files into `assets/audio/` to replace them.

## Quick start

Requirements: Python 3.9+ on Windows or macOS.

```bash
git clone https://github.com/aashnology/My-Woofie.git
cd My-Woofie
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On first launch you choose a pup and your focus and break times. After that he starts straight away.

| I want to... | Do this |
|---|---|
| Stop him | Right-click him, **Quit My-Woofie**. Or in any terminal: `python main.py --stop` |
| Choose a different dog | Right-click, **Change avatar...** (or `python main.py --select`) |
| Be asked every launch | Tick **ASK ME EVERY TIME** in the picker |
| Start over | Right-click, **Reset all settings...** (or `python main.py --reset`) |
| Change timers, speed, sound or night behaviour | Right-click, **Settings...** |
| Snooze a break | Click **SNOOZE** on the break card (or right-click, **Snooze this break**) |
| Hold alerts for a presentation | Right-click, **Presentation mode** |
| See my week | Right-click, **Weekly summary...** (or `python main.py --stats`) |
| Delete my statistics | **Settings, DATA, Delete my data** (or `python main.py --delete-data`) |
| See a full cycle quickly | `python main.py --test` (10 s focus, 5 s break; keep moving the mouse) |

All options: `--select`, `--reset`, `--settings`, `--stop`, `--test`, `--focus MIN`, `--break MIN`, `--stats`, `--delete-data`, `--version`.

On macOS, optional automatic fullscreen detection needs `pip install pyobjc-framework-Quartz`; without it use Presentation mode.

## Customizing

- **Break tips:** `break_tips.txt`, one per line as `category|text` (eyes, stretch, water, posture, walk, breathe).
- **Messages:** one per line in `break_prompts.txt` and `focus_prompts.txt` (lines starting with `#` are ignored). Changes apply without restarting.
- **Sounds:** replace the files in `assets/audio/`, or change `SOUND_EVENTS` in `config.py`.
- **Art:** animation frames live in `assets/images/<avatar>/`.
- **Everything else:** constants at the top of `config.py`.

## Building a download

```bash
pip install -r requirements-dev.txt
python packaging/build.py     # runs the tests, then PyInstaller; result in dist/
```

Build on the system you are targeting. Pushing a tag such as `v2.0.0` runs `packaging/release-workflow.yml` (copy it to `.github/workflows/release.yml` once; GitHub needs the `workflow` permission to add it), which builds both and attaches them to a GitHub Release. Packaged builds keep settings, stats and editable text files in your user folder (`%APPDATA%\\My-Woofie`, `~/Library/Application Support/My-Woofie`).

## Tests

```bash
python -m unittest discover -s tests
```

## Documentation

- [User guide](docs/USER_GUIDE.md): everyday use, changing the focus time, resetting, turning him off, troubleshooting.
- [Technical guide](docs/TECHNICAL_GUIDE.md): how the code works (timers, state machine, rendering, audio, assets, configuration reference).
- [Changelog](CHANGELOG.md): what is in each version.

## License

Released under the [MIT License](LICENSE). © 2026 Aashna Batabyal.
