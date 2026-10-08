# My-Woofie User Guide (Version 2)

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
| Holding the mouse button on him | Petting: hearts, and his mood goes up |
| Every 20 minutes of focus | A quick eye rest, stretch, water or posture card (Done or Skip) |
| Idle at night | Curls up and naps (Zzz); wakes when you move the mouse |
| First activity in the morning | A stretch and a greeting |
| Late at night | A gentle bedtime nudge, repeated hourly while you keep working |
| A fullscreen app or presentation | Hides and holds alerts until it ends |

Every dog is exactly 53 × 47 pixels. He only looks at the clock and where your mouse is. He never sees your screen, keys, files or window titles.

## 3. The right-click menu

**The settings are hidden by default.** There is no window or menu bar: only the dog (and the tray icon, where your system shows one) is on screen. To change the focus time, break length or anything else, right-click directly on the dog (the rest of his window lets clicks pass through) or on the tray icon. Until you do, everything stays at its defaults.

Right-click the dog (or the tray icon) for:

- **Pause My-Woofie** hides him until you untick it (double-clicking the tray icon does the same).
- **Snooze this break** is available during a break while snoozes remain.
- **Presentation mode** hides him and holds alerts until you untick it.
- **Give a treat** drops a bone at your cursor (5 per day).
- **Play fetch** adds a ball: drag it with the mouse and let go to throw it. He brings it back to your cursor.
- **Wardrobe...** choose an unlocked accessory.
- **Weekly summary...** breaks taken and skipped, snoozes, focus time and streak.
- **Settings...** all options in tabs: Timers, Pet, Sound, System, Data. The focus timer restarts if you change the focus or break length.
- **Change avatar...** pick another dog, or tick "ask me every time".
- **Focus and break time at every start:** a small dialog asks each time you launch. Untick **ASK ME EVERY TIME I START** (there or in Settings, System) to keep your saved times.
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

- **Menu:** right-click, then **Settings...** (Timers tab).
- **Startup:** `python main.py --settings`.
- **One run only:** `python main.py --focus 90 --break 10` (minutes). This is not saved.
- **Defaults:** edit `DEFAULT_FOCUS_MINUTES` and `DEFAULT_BREAK_MINUTES` in `config.py`.

Your saved choices live in `settings.json` next to the program.

## 5b. Breaks, snooze and micro-breaks

When the focus time is up, a card appears under the focus meter with a specific suggestion (stretch, water, a short walk) that changes every 25 seconds.

- **SNOOZE** pushes the break back by the snooze length (default 5 minutes). You get 2 snoozes per focus cycle by default; each one lowers his mood. The count resets after a real break.
- **OK, ON IT!** just closes the card; the break continues.
- A break counts as **taken** if your mouse stayed mostly still during it, and as **skipped** if you kept working. This only uses mouse movement, never what is on screen.
- **Micro-breaks** are 20-second reminders every 20 minutes (eyes, stretch, water, posture). They never appear right before a big break, while you are away, or during fullscreen. Turn them off or change their timing in Settings.

## 5c. Mood, streaks and the wardrobe

His mood goes up when you take breaks, pet him, give treats and play fetch, and down when you skip or snooze. A droopy dog walks slower and sometimes shows a sweat drop. A **healthy day** is a day with at least as many breaks taken as skipped; consecutive healthy days make a **streak** (one missing day is forgiven). Streak days unlock accessories: party hat 1, flower 3, beanie 5, bandana 7, top hat 10, crown 14. Open **Wardrobe...** to wear one; he announces new unlocks himself.

## 5d. Fullscreen, presentations and several monitors

- While another program covers a whole monitor he hides and alerts wait; when it ends, an overdue break starts straight away. This compares window sizes only. On macOS install `pyobjc-framework-Quartz` for automatic detection, or use **Presentation mode**. You can turn automatic detection off in Settings, System.
- With several monitors he wanders between them (switch off in Settings, Pet). Alerts and the focus meter appear on the monitor your cursor is on.

## 5e. Your data

Statistics (counts per day, focus minutes), mood and wardrobe progress are stored in `stats.json` and `pet_state.json` next to the program (in your user folder for packaged apps). They never leave your computer. See them with **Weekly summary...** or `python main.py --stats`. Remove everything with **Settings, Data, Delete my data** or `python main.py --delete-data`. To stop recording, untick **Keep break statistics**.

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

- **He disappeared:** a fullscreen program, Presentation mode or Pause is hiding him. Check the menu.
- **No break appeared:** snoozing postpones it; also, 15 minutes without mouse movement resets the focus timer.

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
