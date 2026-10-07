# Aspen User Guide

Everything you need to use Aspen day to day. For how the code works, see the [Technical Guide](TECHNICAL_GUIDE.md).

## 1. Starting Aspen

```bash
python main.py
```

The first time, two small windows appear:

1. **Choose your pup:** click a dog (or use the arrow keys) and press **START**.
2. **Timer settings:** choose how long you want to focus before a break, and how long the break should be. Use the preset buttons (25, 45, 60, 90, 120, 240 minutes) or type your own number. Press **SAVE**.

Aspen then appears on your desktop. Next time he starts right away with your saved choices.

## 2. What Aspen does while you work

| What you are doing | What Aspen does |
|---|---|
| Moving the mouse | Ambles toward your cursor and sits near it |
| Keeping the mouse still | Wanders slowly along the screen edge and rests now and then |
| Working past your focus time | Walks to mid-screen, barks, shows a speech bubble and counts down your break |
| Break time is over | Plays a soft chime, shows a "back to work" bubble and goes back to wandering |
| Clicking him | Happy hop |

Aspen only looks at the clock and where your mouse is. He never sees your screen, keys, files or window titles.

## 3. The right-click menu

Right-click Aspen (or the tray icon) for:

- **Timer settings...** change focus and break minutes. The focus timer restarts when you save.
- **Change avatar...** pick another dog.
- **Size** Tiny, Small (default), Medium or Large.
- **Always show focus meter** shows the retro meter at the top of the screen all the time. By default it only appears during breaks.
- **Mute sounds (bubbles only)** silences audio; Aspen speaks with speech bubbles instead.
- **Quit Aspen** closes him completely.

## 4. Changing the focus time

Any of these work:

- **Menu:** right-click Aspen, then **Timer settings...**.
- **Startup:** run `python main.py --settings` to open the dialog when launching.
- **One run only:** `python main.py --focus 90 --break 10` (minutes). This is not saved.
- **Defaults for everyone:** edit `DEFAULT_FOCUS_MINUTES` and `DEFAULT_BREAK_MINUTES` in `config.py`.

Your saved choice lives in `settings.json` next to the program. Delete that file to start fresh.

## 5. Turning Aspen off

| How | Steps |
|---|---|
| Menu (easiest) | Right-click Aspen, then **Quit Aspen** |
| Tray icon | Right-click the tray icon (Windows: bottom-right, you may need the ^ arrow; macOS: the menu bar), then **Quit Aspen** |
| Terminal | Click the terminal window where you started him and press `Ctrl+C` |
| Close the terminal | Closing the terminal window stops him too |
| Last resort | Windows: Task Manager, end the `python` process. macOS: Activity Monitor, quit `Python` |

Aspen does not start automatically when you log in, so once he is closed he stays closed until you run `python main.py` again.

## 6. Making him smaller, calmer or quieter

- **Smaller or larger:** right-click, then **Size**.
- **Even calmer:** lower `PET_SPEED` (default 2) or raise `ANIMATION_FRAME_MS` (default 400) in `config.py`.
- **Quieter:** use **Mute sounds** from the menu, or set `AUDIO_ENABLED = False`.
- **No speech bubbles with sound on:** set `ALWAYS_SHOW_BUBBLES = False` (bubbles then only appear when muted).
- **Hide the HUD entirely:** set `SHOW_HUD = False`.

## 7. Changing what Aspen says

Open `break_prompts.txt` (shown when it is time for a break) or `focus_prompts.txt` (shown when it is time to get back to work). One message per line; lines starting with `#` are ignored. Save the file and the next bubble uses your text. Set `PROMPT_ORDER` to `"random"` in `config.py` to shuffle.

## 8. Trying it out quickly

```bash
python main.py --test
```

The focus time becomes 10 seconds and the break 5 seconds. Keep moving the mouse and you will see the bark, bubble, countdown and chime within about 20 seconds. If the mouse is still for 8 seconds in test mode, the focus timer resets (this is the "you were away" rule).

## 9. Troubleshooting

| Problem | Try this |
|---|---|
| Aspen does not appear | Check the terminal for errors; run `pip install -r requirements.txt` again. Make sure only one copy is running. |
| He is too small or too big | Right-click, then **Size**. |
| No sound | Check **Mute sounds** is off, your system volume, and that `pygame` installed. Without it Aspen falls back to system beeps. |
| No tray icon | Right-click Aspen himself; the same menu appears. |
| He barks too early or too late | Right-click, then **Timer settings...**. |
| He never barks | The focus timer resets after 15 minutes of no mouse movement. Reading or typing without moving the mouse counts as away. |
| Clicks seem to hit Aspen | Only the dog's own pixels catch clicks. On macOS, click-through can behave differently. |
| Want to reset everything | Delete `settings.json` and restart. |

## 10. Privacy

Aspen never captures the screen, logs keystrokes, reads files, records window titles or uses the network. Details are in the [Technical Guide](TECHNICAL_GUIDE.md#1-design-principles).
