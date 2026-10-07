# My-Woofie User Guide (Version 1)

Everything you need to use My-Woofie day to day. For how the code works, see the [Technical Guide](TECHNICAL_GUIDE.md).

## 1. Starting My-Woofie

```bash
python main.py
```

The first time, two small windows appear:

1. **Choose your pup:** click a dog (or use the arrow keys) and press **START**. Tick **ASK ME EVERY TIME** if you want to choose again at every launch.
2. **Timer settings:** choose how long you want to focus before a break, and how long the break should be. Use the preset buttons (25, 45, 60, 90, 120, 240 minutes) or type your own number. Press **SAVE**.

Closing the picker without pressing START is not remembered, so you will be asked again next time. After you do choose, he starts right away with your saved choices.

## 2. What he does while you work

| What you are doing | What he does |
|---|---|
| Moving the mouse | Ambles toward your cursor and sits near it |
| Keeping the mouse still | Wanders slowly along the screen edge and rests now and then |
| Working past your focus time | Walks to mid-screen, barks, shows a speech bubble and counts down your break |
| Break time is over | Plays a soft chime, shows a "back to work" bubble and goes back to wandering |
| Clicking him | Happy hop |

Every dog is exactly 53 × 47 pixels. He only looks at the clock and where your mouse is. He never sees your screen, keys, files or window titles.

## 3. The right-click menu

Right-click the dog (or the tray icon) for:

- **Pause My-Woofie** hides him until you untick it.
- **Timer settings...** change focus and break minutes. The focus timer restarts when you save.
- **Change avatar...** pick another dog, or tick "ask me every time".
- **Always show focus meter** shows the retro meter at the top of the screen all the time. By default it only appears during breaks.
- **Mute sounds (bubbles only)** silences audio; he speaks with speech bubbles instead.
- **Reset all settings...** forgets everything saved and runs the setup screens again.
- **Quit My-Woofie (stop the program)** closes him completely.

## 4. Choosing or changing your dog

- **Any time:** right-click, **Change avatar...**.
- **From the terminal:** `python main.py --select`.
- **Every launch:** tick **ASK ME EVERY TIME** in the picker.
- **Start completely fresh:** right-click, **Reset all settings...**, or run `python main.py --reset`.

If he always starts as the same dog, it is because that choice was saved. Use one of the options above to choose again.

## 5. Changing the focus time

- **Menu:** right-click, then **Timer settings...**.
- **Startup:** `python main.py --settings`.
- **One run only:** `python main.py --focus 90 --break 10` (minutes). This is not saved.
- **Defaults:** edit `DEFAULT_FOCUS_MINUTES` and `DEFAULT_BREAK_MINUTES` in `config.py`.

Your saved choices live in `settings.json` next to the program.

## 6. Turning him off

| How | Steps |
|---|---|
| Menu (easiest) | Right-click the dog, then **Quit My-Woofie** |
| Command line | In any terminal, in the project folder: `python main.py --stop` |
| Tray icon | Right-click the tray icon (Windows: bottom-right, maybe behind the ^ arrow; macOS: menu bar), then **Quit** |
| Terminal | Click the terminal where you started him and press `Ctrl+C`, or close that terminal |
| Last resort | Windows: Task Manager, end the `python` process. macOS: Activity Monitor, quit `Python` |

Running `python main.py` while he is already running does nothing but tell you so, so you never get two dogs. He does not start automatically when you log in.

Tip: on Windows, `pythonw main.py` runs him without a terminal window; use `python main.py --stop` to stop him.

## 7. Making him quieter

- **Quieter:** use **Mute sounds** from the menu, or set `AUDIO_ENABLED = False`.
- **Calmer:** lower `PET_SPEED` (default 2) or raise `ANIMATION_FRAME_MS` (default 400) in `config.py`.
- **No bubbles with sound on:** set `ALWAYS_SHOW_BUBBLES = False` (bubbles then appear only when muted).
- **Hide the HUD entirely:** set `SHOW_HUD = False`.

## 8. Changing what he says

Open `break_prompts.txt` (shown when it is time for a break) or `focus_prompts.txt` (shown when it is time to get back to work). One message per line; lines starting with `#` are ignored. Save the file and the next bubble uses your text. Set `PROMPT_ORDER` to `"random"` in `config.py` to shuffle.

## 9. Trying it out quickly

```bash
python main.py --test
```

The focus time becomes 10 seconds and the break 5 seconds. Keep moving the mouse and you will see the bark, bubble, countdown and chime within about 20 seconds. If the mouse is still for 8 seconds in test mode, the focus timer resets (the "you were away" rule).

## 10. Troubleshooting

| Problem | Try this |
|---|---|
| I never get to choose my dog | Right-click, **Change avatar...**, or run `python main.py --select` / `--reset` |
| He does not appear | Check the terminal for errors; run `pip install -r requirements.txt` again; make sure he is not paused |
| "already running" message | He is running; use `python main.py --stop` first |
| No sound | Check **Mute sounds**, your system volume, and that `pygame` installed. Without it he falls back to system beeps |
| No tray icon | Right-click the dog himself; the same menu appears |
| He barks too early or late | Right-click, **Timer settings...** |
| He never barks | The focus timer resets after 15 minutes of no mouse movement. Reading or typing without moving the mouse counts as away |
| Want to reset everything | `python main.py --reset` |

## 11. Privacy

My-Woofie never captures the screen, logs keystrokes, reads files, records window titles or uses the network. The only local control channel is a same-machine socket used by `--stop`.
