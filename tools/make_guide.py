"""Builds docs/My-Woofie-Guide.pdf, a standalone guide to the whole project (Version 1 and Version 2).

Run:  python tools/make_guide.py        (needs: pip install reportlab pillow)
"""
import os
import sys

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
import config  # noqa: E402

IMG = os.path.join(ROOT, "docs", "images")
OUT = os.path.join(ROOT, "docs", "My-Woofie-Guide.pdf")
REPO = "github.com/aashnology/My-Woofie"

NAVY, PLUM, GOLD = colors.HexColor("#1B1B2F"), colors.HexColor("#2B2347"), colors.HexColor("#FFC53D")
CREAM, INK, GREEN, RED = colors.HexColor("#FFF4D6"), colors.HexColor("#2A1A0A"), colors.HexColor("#3FAE55"), colors.HexColor("#D9444F")
BLUE, GREY = colors.HexColor("#4DA8FF"), colors.HexColor("#6B6788")

base = getSampleStyleSheet()
S = {
    "body": ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=14.5,
                           textColor=colors.HexColor("#222222"), spaceAfter=6),
    "small": ParagraphStyle("small", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=12,
                            textColor=GREY),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24,
                         textColor=NAVY, spaceBefore=4, spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17,
                         textColor=PLUM, spaceBefore=10, spaceAfter=5),
    "cell": ParagraphStyle("cell", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12.5),
    "cellb": ParagraphStyle("cellb", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12.5),
    "head": ParagraphStyle("head", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12,
                           textColor=colors.white),
    "code": ParagraphStyle("code", parent=base["Code"], fontName="Courier", fontSize=8.5, leading=11.5,
                           backColor=colors.HexColor("#F3EFE2"), borderPadding=6, leftIndent=6, rightIndent=6,
                           spaceBefore=4, spaceAfter=8),
    "caption": ParagraphStyle("caption", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=8,
                              leading=11, textColor=GREY, alignment=TA_CENTER, spaceAfter=8),
    "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=14.5,
                             leftIndent=14, bulletIndent=3, spaceAfter=3),
    "big": ParagraphStyle("big", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=30, leading=34,
                          textColor=GOLD, alignment=TA_CENTER),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(item, S["bullet"], bulletText="\u2022") for item in items]


def code(text):
    return Paragraph(text.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>").replace(" ", "&nbsp;"),
                     S["code"])


def table(rows, widths, header=True):
    data = [[Paragraph(str(c), S["head"] if header and r == 0 else S["cell"]) for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9C3AE")),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF6E8")])]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), PLUM)]
    t.setStyle(TableStyle(style))
    return t


def picture(name, width_cm, caption=None):
    path = os.path.join(IMG, name)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    width = width_cm * cm
    items = [Image(path, width=width, height=width * h / w)]
    if caption:
        items.append(P(caption, "caption"))
    return KeepTogether(items)


def callout(text, fill=CREAM, edge=GOLD):
    t = Table([[Paragraph(text, S["cell"])]], colWidths=[16.4 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fill), ("BOX", (0, 0), (-1, -1), 1.2, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def box(d, x, y, w, h, text, fill, text_color=colors.white, size=8):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=INK, strokeWidth=1))
    lines = text.split("\n")
    top = y + h / 2 + (len(lines) - 1) * size / 2 - size * 0.35
    for i, line in enumerate(lines):
        d.add(String(x + w / 2, top - i * (size + 1.5), line, fontName="Helvetica-Bold", fontSize=size,
                     fillColor=text_color, textAnchor="middle"))


def arrow(d, x1, y1, x2, y2):
    d.add(Line(x1, y1, x2, y2, strokeColor=INK, strokeWidth=1.4))
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    d.add(Polygon([x2, y2, x2 - 7 * math.cos(ang - 0.4), y2 - 7 * math.sin(ang - 0.4),
                   x2 - 7 * math.cos(ang + 0.4), y2 - 7 * math.sin(ang + 0.4)], fillColor=INK, strokeColor=INK))


def phase_diagram():
    d = Drawing(16.4 * cm, 3.6 * cm)
    y = 55
    box(d, 5, y, 105, 42, "FOCUS\nmouse activity counted", GREEN)
    box(d, 175, y, 105, 42, "BREAK\nbark, card, countdown", RED)
    box(d, 345, y, 105, 42, "HAUL\nchime, back to work", GOLD, INK)
    arrow(d, 110, y + 21, 175, y + 21)
    arrow(d, 280, y + 21, 345, y + 21)
    d.add(String(142, y + 27, "focus limit", fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=INK))
    d.add(String(312, y + 27, "break over", fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=INK))
    d.add(Line(397, y, 397, 20, strokeColor=INK, strokeWidth=1.4))
    d.add(Line(397, 20, 57, 20, strokeColor=INK, strokeWidth=1.4))
    arrow(d, 57, 20, 57, y)
    d.add(String(227, 10, "after the back-to-work message, a new focus session starts", fontName="Helvetica",
                 fontSize=7, textAnchor="middle", fillColor=INK))
    d.add(Line(175, y + 8, 110, y + 8, strokeColor=BLUE, strokeWidth=1.2, strokeDashArray=[3, 2]))
    arrow(d, 118, y + 8, 110, y + 8)
    d.add(String(142, y - 6, "snooze", fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=BLUE))
    d.add(String(57, 100, "15 min without mouse movement = away, timer resets", fontName="Helvetica", fontSize=7,
                 fillColor=INK))
    return d


def state_diagram():
    d = Drawing(16.4 * cm, 5.7 * cm)
    box(d, 175, 110, 100, 34, "ROAM\nwander the edge", PLUM)
    box(d, 5, 110, 100, 34, "CHASE\nfollow the cursor", BLUE)
    box(d, 345, 110, 105, 34, "SLEEP\nnight, mouse still", GREY)
    box(d, 5, 40, 100, 34, "TREAT\nrun to the bone", GREEN)
    box(d, 175, 40, 100, 34, "FETCH\nchase, carry, deliver", GREEN)
    box(d, 345, 40, 105, 34, "BARK / HAUL\nalerts (override all)", RED)
    arrow(d, 175, 127, 105, 127)
    arrow(d, 105, 120, 175, 120)
    arrow(d, 275, 127, 345, 127)
    arrow(d, 345, 120, 275, 120)
    arrow(d, 225, 110, 225, 74)
    arrow(d, 175, 57, 105, 57)
    d.add(String(227, 20, "A break or back-to-work alert interrupts every other state, then he returns to ROAM",
                 fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=INK))
    return d


def cover(canvas, doc):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(PLUM)
    canvas.rect(0, h * 0.30, w, h * 0.34, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h * 0.30 - 5, w, 5, fill=1, stroke=0)
    canvas.rect(0, h * 0.64, w, 5, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 44)
    canvas.drawCentredString(w / 2, h * 0.52, "My-Woofie")
    canvas.setFillColor(CREAM)
    canvas.setFont("Helvetica", 15)
    canvas.drawCentredString(w / 2, h * 0.46, "A digital companion that looks after you while you work")
    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(w / 2, h * 0.42, "Complete project guide: Version 1 and Version 2")
    for i, name in enumerate(("aspen", "biscuit", "cocoa", "bailey", "benny", "snow")):
        canvas.drawImage(os.path.join(IMG, "avatars", name + ".png"), w / 2 - 3 * 2.7 * cm + i * 2.7 * cm + 0.1 * cm,
                         h * 0.70, width=2.5 * cm, height=2.5 * cm, mask="auto")
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawCentredString(w / 2, h * 0.18, f"Version {config.VERSION}")
    canvas.setFillColor(CREAM)
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(w / 2, h * 0.15, "by Aashna Batabyal")
    canvas.drawCentredString(w / 2, h * 0.125, REPO)
    canvas.restoreState()


def page(canvas, doc):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 1.1 * cm, w, 1.1 * cm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2 * cm, h - 0.72 * cm, "My-Woofie")
    canvas.setFillColor(CREAM)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 2 * cm, h - 0.72 * cm, f"Project guide, version {config.VERSION}")
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 1 * cm, f"{doc.page}")
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2.3 * cm, rightMargin=2.3 * cm, topMargin=2.0 * cm,
                          bottomMargin=1.8 * cm, title="My-Woofie: complete project guide",
                          author="Aashna Batabyal", subject="Desktop break companion, Version 1 and Version 2")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=cover, autoNextPageTemplate="body"),
                          PageTemplate(id="body", frames=[frame], onPage=page)])
    W = doc.width
    s = [Spacer(1, 1), PageBreak()]

    # ---------------- 1. at a glance
    s += [P("1. My-Woofie at a glance", "h1"),
          P("My-Woofie is a small pixel-art puppy who lives on top of your desktop. He wanders the screen edge, "
            "ambles after your cursor, and keeps quiet company while you work. After the focus time you choose "
            "(4 hours by default) he barks, shows a speech bubble with a specific suggestion, and counts down a "
            "break. When the break is over he calls you back with a soft chime."),
          P("He is a companion first and a timer second: small, calm, a little silly, and easy to read, change and "
            "run locally. Everything runs on your own computer, in plain Python with PyQt6."),
          Spacer(1, 4),
          table([["The problem", "Long stretches at a screen are easy to lose track of, and ordinary timers are easy to dismiss and forget."],
                 ["The idea", "A companion you actually like having around, who nudges you toward real breaks, and who is happier when you take them."],
                 ["Who it is for", "Anyone who works at a computer for hours: students, developers, writers, designers."],
                 ["Privacy", "No screen capture, no key logging, no file reading, no window titles, no network. Activity is just elapsed time and mouse movement."],
                 ["Platforms", "Windows and macOS (Python 3.9+), with packaged downloads; also runs from source on Linux."]],
                [3.2 * cm, W - 3.2 * cm], header=False),
          Spacer(1, 8),
          table([["Number", "What it counts"],
                 ["6", "pixel-art dogs (Aspen, Biscuit, Cocoa, Bailey, Benny, Snow)"],
                 ["53 x 47", "pixels: the exact on-screen size of every dog"],
                 ["4 h / 15 min", "default focus time and break length (both adjustable)"],
                 ["13", "headline features added in Version 2"],
                 ["101", "automated tests (19 in Version 1)"],
                 ["0", "network calls, screenshots, keystrokes or window titles recorded"]],
                [3.2 * cm, W - 3.2 * cm]),
          PageBreak()]

    # ---------------- 2. pups
    s += [P("2. Meet the pups", "h1"),
          P("Six dogs are part of My-Woofie. Pick yours on first launch, and change your mind at any time from "
            "the right-click menu. Aspen, Biscuit and Cocoa are drawn in code from a palette. Bailey, Benny and "
            "Snow are built from the original design sheet. Every dog has ten animation frames: idle, walking, "
            "barking, the back-to-work hop and a happy pose."),
          ]
    grid = [[Image(os.path.join(IMG, "avatars", f"{n}.png"), width=4.4 * cm, height=4.4 * cm) for n in row]
            for row in (("aspen", "biscuit", "cocoa"), ("bailey", "benny", "snow"))]
    names = [[P(f"<b>{a}</b><br/>{b}", "cell") for a, b in row]
             for row in ((("Aspen", "Golden retriever"), ("Biscuit", "Cream puppy"), ("Cocoa", "Chocolate lab")),
                         (("Bailey", "Beagle"), ("Benny", "Bernese pup"), ("Snow", "Fluffy white pup")))]
    rows = [grid[0], names[0], grid[1], names[1]]
    t = Table(rows, colWidths=[W / 3] * 3)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    s += [t, Spacer(1, 6), picture("selector.png", 15.5, "The retro avatar picker, with the \"ask me every time\" option."),
          picture("actual-size.png", 10, "Every dog is exactly 53 x 47 pixels on screen, shown here at true size."),
          PageBreak()]

    # ---------------- 3. V1
    s += [P("3. Version 1: the foundation", "h1"),
          P("Version 1 delivered the complete core experience: a calm companion, a reliable timer, and a retro look."),
          table([["Feature", "What it does"],
                 ["Six pixel-art dogs", "Fixed 53 x 47 pixel canvas, ten frames each, picked in a retro avatar selector."],
                 ["Avatar picker", "Choose on first launch; tick \"ask me every time\" to choose at every start. Dismissing is never remembered."],
                 ["Cursor following", "Slow, calm movement. He trots toward the cursor while you move the mouse and roams the screen edge when you are still."],
                 ["Focus and break timer", "4 hours of focus, 15-minute break by default, adjustable by dialog, command line or config."],
                 ["Presence detection", "Only 15 continuous minutes without mouse movement resets the focus timer, which means you were genuinely away."],
                 ["Sound", "Bark and soft howl on break start, soft chime on break end, synthesized in code, with system-beep fallbacks if audio fails."],
                 ["Speech bubbles", "Pixel bubbles with rotating messages from break_prompts.txt and focus_prompts.txt. Always shown in silent mode."],
                 ["Retro HUD", "Focus meter that turns green, amber, red; break countdown; flashing back-to-work banner."],
                 ["Menu and tray", "Pause, timer settings, change avatar, focus meter, mute, reset, quit."],
                 ["Easy to stop", "Quit from the menu, or python main.py --stop from any terminal. Single-instance protection."],
                 ["Local only", "Settings saved in a local JSON file. No network, no screen capture, no key logging."]],
                [3.8 * cm, W - 3.8 * cm]),
          Spacer(1, 6), picture("hud-and-bubble.png", 9, "The retro HUD and a speech bubble during a break."),
          PageBreak()]

    # ---------------- 4. V2
    s += [P("4. Version 2: what is new", "h1"),
          P("Version 2 turns the timer into a companion with habits, moods and things to do, while keeping the "
            "same privacy rules. Every feature below is built, tested and merged."),
          table([["Feature", "What it does"],
                 ["1. Snooze with a cost", "\"Snooze 5 min\" on the break card, limited per focus cycle (default 2, adjustable 0 to 5). Each snooze lowers his mood and is counted in the stats."],
                 ["2. Smarter breaks", "Short micro-breaks every 20 minutes: a 20-second eye rest, stretch, water sip or posture check, with Done and Skip. They never fire right before a big break, while you are away, or in fullscreen."],
                 ["3. Break guidance", "The break card suggests something specific (stretch, water, a short walk, breathing), rotating every 25 seconds from break_tips.txt."],
                 ["4. Settings window", "Right-click, Settings: five tabs (Timers, Pet, Sound, System, Data) with timers, speed, volume, night behaviour, start at login and data controls."],
                 ["5. Mood and streaks", "Real breaks make him happy; skipped breaks and snoozes make him droopy and slower. Healthy days build a streak (one missing day is forgiven)."],
                 ["6. Petting, treats, fetch", "Click and hold to pet him (hearts). Give a treat (5 a day). Play fetch: drag and throw the ball, he chases it and brings it back to your cursor."],
                 ["7. Time of day", "Curls up for a nap when you are idle at night, stretches and greets you in the morning, and gives a gentle bedtime nudge when it is late."],
                 ["8. Wardrobe", "Party hat, flower, beanie, bandana, top hat and crown, unlocked by streak days (1, 3, 5, 7, 10, 14)."],
                 ["9. Fullscreen awareness", "While a program covers a whole monitor, or in Presentation mode, he hides and alerts wait. An overdue break fires as soon as it ends."],
                 ["10. Multi-monitor", "He wanders between monitors, chases the cursor across them, and shows alerts on the monitor your cursor is on."],
                 ["11. Start at login and tray", "Optional autostart on Windows, macOS and Linux. Click the tray icon for status, double-click to pause."],
                 ["12. Local-only stats", "Weekly summary of breaks taken and skipped, snoozes, focus time and streak. One-click Delete my data, --stats and --delete-data."],
                 ["13. Packaged builds", "PyInstaller recipe and a GitHub Actions workflow that builds a Windows .exe and a macOS .app and attaches them to a Release."]],
                [3.8 * cm, W - 3.8 * cm]),
          PageBreak(),
          P("The new screens", "h1"),
          picture("v2/break-card.png", 11, "The break card: a specific suggestion, a countdown, Snooze (with snoozes left) and OK."),
          picture("v2/micro-break.png", 11, "A micro-break card between big breaks: Done or Skip."),
          picture("v2/settings.png", 11, "The settings window. The same options are saved to settings.json."),
          PageBreak(),
          picture("v2/weekly-summary.png", 11.5, "The weekly summary: green bars are breaks taken, red are skipped. Stored only on your computer."),
          picture("v2/wardrobe.png", 11.5, "The wardrobe. Locked items show the streak they need."),
          PageBreak(),
          P("Accessories on every dog", "h2"),
          P("Each accessory is drawn onto the same 53 x 47 canvas, so the window never changes size. The dog "
            "is drawn a few pixels smaller to make room for hats. Rows: party hat, flower, beanie, top hat, "
            "crown, bandana."),
          picture("v2/accessories.png", 13.5),
          PageBreak()]

    # ---------------- 5. a day
    s += [P("5. A day with My-Woofie", "h1"),
          table([["What you are doing", "What he does"],
                 ["Moving the mouse", "Ambles toward your cursor and sits near it (on whichever monitor you are using)."],
                 ["Keeping the mouse still", "Wanders slowly along the screen edge and rests now and then."],
                 ["Clicking and holding on him", "Petting: happy hop, hearts, his mood goes up."],
                 ["Every 20 minutes of focus", "A quick eye rest, stretch, water or posture card appears. Click Done or Skip."],
                 ["Working past your focus time", "Walks to mid-screen, barks, shows a break card with a tip and a Snooze button, and counts down your break."],
                 ["You step away during the break", "The break is recorded as taken, his mood rises, and the streak grows."],
                 ["You keep working through it", "The break is recorded as skipped and his mood drops."],
                 ["Break time is over", "Soft chime, a back-to-work bubble, then back to wandering."],
                 ["Idle at night", "Curls up and naps with Zzz; wakes the moment you move the mouse."],
                 ["First activity in the morning", "A stretch and a greeting."],
                 ["Late at night, still working", "A gentle bedtime nudge, repeated every hour."],
                 ["A presentation or fullscreen app", "Hides and holds alerts until it ends."],
                 ["You right-click him", "Menu: pause, snooze, presentation mode, treat, fetch, wardrobe, weekly summary, settings."]],
                [5.0 * cm, W - 5.0 * cm]),
          Spacer(1, 10), P("The focus and break cycle", "h2"), phase_diagram(),
          P("A break counts as <b>taken</b> if the mouse was active for no more than 25% of it, and as "
            "<b>skipped</b> otherwise. Only mouse movement is used, never what is on screen.", "body"),
          PageBreak()]

    # ---------------- 6. how it works
    s += [P("6. How it works", "h1"),
          P("The code is split into small, readable modules so every feature can be debugged and changed on its "
            "own in VS Code. The timer, pet, stats, mood and scheduling logic have no Qt dependency, so they are "
            "tested with a fake clock."),
          table([["Module", "Role"],
                 ["main.py", "Thin launcher: command-line options, single-instance check, startup dialogs."],
                 ["companion.py", "WoofieApp: owns every window and part and runs the 33 ms main loop."],
                 ["timer.py", "Session timer: presence detection, FOCUS / BREAK / HAUL, snooze, break quality, deferral."],
                 ["pet.py", "Finite state machine and movement: roam, chase, sleep, treat, fetch, alerts, multi-monitor."],
                 ["gui.py, retro.py", "Transparent click-through windows, sprites, HUD, bubbles, emotes, toys, break card; retro pixel styling."],
                 ["dialogs.py", "Settings window, weekly summary, wardrobe."],
                 ["stats.py, mood.py", "Per-day counters and streaks; mood, daily limits, wardrobe state."],
                 ["microbreak.py, tips.py, daypart.py", "Micro-break scheduler, tip bank, night / morning / bedtime rules."],
                 ["toys.py, wardrobe.py", "Ball physics and bone; pixel-art accessories drawn onto frames."],
                 ["fullscreen.py, autostart.py, paths.py", "Fullscreen detection (sizes only), start at login, source vs packaged file locations."],
                 ["assets_builder.py, audio.py", "Sprite generation for all dogs; synthesized sounds with beep fallbacks."],
                 ["settings.py, prompts.py, selector.py, timer_dialog.py, instance.py", "Saved settings, message banks, avatar picker, first-run timer dialog, single instance and --stop."]],
                [5.4 * cm, W - 5.4 * cm]),
          Spacer(1, 8), P("The pet's state machine", "h2"), state_diagram(),
          P("<b>Main loop.</b> Every 33 ms the app reads the cursor position, polls fullscreen state every 3 "
            "seconds, feeds the timer, turns timer events into statistics and mood changes, updates the "
            "micro-break scheduler and the day rhythm, moves the pet, moves toys and then redraws windows. "
            "The timer takes an injectable clock, so hours of behaviour are simulated instantly in tests."),
          P("<b>Click-through windows.</b> The dog, bubble, emotes and HUD ignore the mouse, so clicks pass to "
            "the apps underneath. Only the dog's own pixels (a mask), the fetch ball and the break card accept clicks, "
            "and they never steal keyboard focus."),
          Spacer(1, 10)]

    # ---------------- 7. privacy
    s += [P("7. Privacy and safety by design", "h1"),
          P("These rules apply to both versions and are enforced by how the code is written, not by a setting."),
          table([["My-Woofie never...", "How it is guaranteed"],
                 ["captures the screen", "No screen-capture API is imported or called anywhere."],
                 ["logs keystrokes", "Only the cursor position is read, once per tick. There is no keyboard hook."],
                 ["reads files or window titles", "No code reads other programs' files, titles or names."],
                 ["uses the network", "No sockets to the internet. The only socket is a local one used for --stop and single-instance checks."],
                 ["detects fullscreen by looking at your screen", "It compares the foreground window's size with the monitor size. On macOS it reads only window layer, transparency and bounds."],
                 ["sends your statistics anywhere", "stats.json holds integer counters per date and stays in the project or user folder. Delete my data removes it."],
                 ["locks or blocks you", "He nudges; you decide. Snooze, Skip and Pause are always available (snooze is limited per cycle by design)."]],
                [5.4 * cm, W - 5.4 * cm]),
          Spacer(1, 8),
          callout("<b>A limit you should know:</b> presence comes only from time and mouse movement, so reading or "
                  "typing without touching the mouse for 15 minutes counts as being away."),
          PageBreak()]

    # ---------------- 8. install
    s += [P("8. Install, run and options", "h1"),
          P("Requirements: Python 3.9 or newer on Windows or macOS.", "body"),
          code("git clone https://github.com/aashnology/My-Woofie.git\ncd My-Woofie\npython -m venv venv\n"
               "source venv/bin/activate        # Windows: venv\\Scripts\\activate\npip install -r requirements.txt\npython main.py"),
          P("On first launch you choose a pup and your focus and break times. After that he starts straight away."),
          table([["I want to...", "Do this"],
                 ["Stop him", "Right-click, Quit My-Woofie. Or python main.py --stop in any terminal."],
                 ["Choose a different dog", "Right-click, Change avatar... (or python main.py --select)."],
                 ["Start over", "Right-click, Reset all settings... (or python main.py --reset)."],
                 ["Change timers, speed, sound, night behaviour", "Right-click, Settings..."],
                 ["Snooze a break", "Click SNOOZE on the break card, or right-click, Snooze this break."],
                 ["Hold alerts for a presentation", "Right-click, Presentation mode."],
                 ["See my week", "Right-click, Weekly summary... (or python main.py --stats)."],
                 ["Delete my statistics", "Settings, Data, Delete my data (or python main.py --delete-data)."],
                 ["See a full cycle quickly", "python main.py --test (10 s focus, 5 s break; keep moving the mouse)."]],
                [5.4 * cm, W - 5.4 * cm]),
          P("All options: --select, --reset, --settings, --stop, --test, --focus MIN, --break MIN, --stats, "
            "--delete-data, --version.", "small"),
          P("Customizing", "h2")]
    s += bullets(["<b>Messages:</b> one per line in break_prompts.txt and focus_prompts.txt (# starts a comment). Changes apply without restarting.",
                  "<b>Break tips:</b> break_tips.txt, one per line as category|text (eyes, stretch, water, posture, walk, breathe).",
                  "<b>Sounds:</b> replace the files in assets/audio/, or change SOUND_EVENTS in config.py.",
                  "<b>Everything else:</b> constants at the top of config.py, and the defaults in settings.py."])
    s += [P("Settings reference", "h2"),
          table([["Setting", "Default", "Meaning"],
                 ["Focus time / break length", "240 min / 15 min", "When he asks for a break, and how long it lasts."],
                 ["Snooze length / snoozes per cycle", "5 min / 2", "How far a snooze postpones the break, and how many you get."],
                 ["Micro-breaks", "on, every 20 min, 20 s", "Short eye / stretch / water / posture reminders."],
                 ["Walking speed", "3 of 5", "Scales how fast he moves."],
                 ["Wander between monitors", "on", "Whether he visits your other screens."],
                 ["Night naps and bedtime nudge", "on; night 22:00 to 06:00; nudge from 23:00", "Time-of-day behaviour."],
                 ["Volume / mute", "80% / off", "Sound level, or speech bubbles only."],
                 ["Hold alerts during fullscreen", "on", "Fullscreen and presentation awareness."],
                 ["Always show focus meter", "off", "HUD only during breaks by default."],
                 ["Keep break statistics", "on", "Local-only weekly summary and streaks."],
                 ["Start at login", "off", "Autostart on Windows, macOS and Linux."]],
                [5.0 * cm, 4.3 * cm, W - 9.3 * cm]),
          Spacer(1, 12)]

    # ---------------- 9. packaging + tests
    s += [P("9. Packaging, testing and quality", "h1"),
          P("Building a download", "h2"),
          code("pip install -r requirements-dev.txt\npython packaging/build.py     # runs the tests, then PyInstaller; result in dist/"),
          P("Build on the system you are targeting: Windows gives a .exe, macOS gives a .app. Pushing a tag "
            "such as v2.0.0 runs .github/workflows/release.yml, which tests the code and builds both versions "
            "on GitHub, then attaches them to a Release. Packaged builds keep settings, stats and the editable "
            "text files in your user folder instead of the program folder."),
          P("Tests", "h2"),
          code("python -m unittest discover -s tests"),
          P("101 automated tests run in about a second with no real screen needed. They cover the timer (cycle, "
            "limits, away reset, jitter, snooze, break quality, deferral), the pet (states, chasing, sleep, "
            "treats, fetch, multi-monitor, bounds), stats and streaks, mood and daily limits, micro-breaks, day "
            "rhythm, tips, ball physics, start at login, fullscreen geometry, the settings window, and that "
            "every dog stays exactly 53 x 47 pixels with every accessory."),
          P("What was verified, and what was not", "h2"),
          table([["Verified here", "Not yet verified on real hardware"],
                 ["All 101 tests; headless full-cycle runs (treat, fetch, micro-break, break, haul); "
                  "visual checks of every accessory on every dog; a PyInstaller build and start on Linux.",
                  "Real Windows and macOS desktops (click-through masks, tray notifications, audio devices), "
                  "real multiple monitors, real fullscreen apps, and the Windows / macOS CI builds, which are "
                  "unsigned so the OS may show a security prompt on first launch."]],
                [W / 2, W / 2]),
          PageBreak()]

    # ---------------- 10. limits + ideas
    s += [P("10. Known limitations and ideas for next", "h1"),
          P("Known limitations", "h2")]
    s += bullets(["Presence is mouse-only by design, so working without touching the mouse looks like being away.",
                  "Automatic fullscreen detection works on Windows; it is off on Linux and needs the optional Quartz package on macOS. Presentation mode works everywhere.",
                  "A micro-break that times out on its own is not counted as done; only a click on Done is recorded.",
                  "The sleep pose reuses his happy frame, so he naps with his tongue out.",
                  "The default sounds are synthesized and sound artificial compared with real recordings.",
                  "Window masks for click-through can behave differently on macOS."])
    s += [P("Ideas for a future version (not built)", "h2")]
    s += bullets(["Real recorded bark and chime sounds.",
                  "More dogs, and a way to add your own from a PNG sprite sheet.",
                  "Optional keyboard-activity awareness that never records what is typed.",
                  "Per-day goals and gentle weekly reports.",
                  "Signed installers for Windows and macOS."])
    s += [PageBreak(), P("11. Hackathon quick reference", "h1"),
          P("The 60-second demo", "h2"),
          code("python main.py --test"),
          table([["Time", "What to show"],
                 ["0 s", "Pick a dog in the retro picker. Move the mouse and watch him follow the cursor."],
                 ["6 s", "A micro-break card appears (eye rest). Click Done: mood goes up."],
                 ["10 s", "The break starts: he barks, the card shows a tip and a Snooze button, the HUD counts down."],
                 ["Click Snooze", "The break moves away for a few seconds, then returns. Snoozes are limited."],
                 ["During the break", "Hold the mouse still to take the break, or keep moving to skip it."],
                 ["After the break", "Soft chime and back-to-work banner. Open Weekly summary to see taken versus skipped."],
                 ["Right-click", "Give a treat, play fetch (throw the ball), open the wardrobe, open Settings."]],
                [3.0 * cm, W - 3.0 * cm]),
          P("The pitch in three sentences", "h2"),
          callout("Breaks only work if you actually take them, and a plain timer is easy to ignore. My-Woofie is a "
                  "pixel puppy who stays on your desktop, nudges you toward real breaks with specific suggestions, "
                  "and gets happier when you take them. It does all of this locally, with no screen capture, no key "
                  "logging and no network, so it is safe to leave running all day."),
          Spacer(1, 10), P("License and links", "h2"),
          P(f"Released under the MIT License. Copyright 2026 Aashna Batabyal. Source: {REPO}. "
            "The repository also contains the User Guide and Technical Guide (docs/), the changelog, and the unit tests."),
          ]
    doc.build(s)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
