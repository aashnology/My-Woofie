"""Builds docs/My-Woofie-Guide.pdf, a standalone guide to the whole project (Version 1 and Version 2).

Run:  python tools/make_guide.py        (needs: pip install reportlab pillow)
"""
import os
import sys
import unittest

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
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import config  # noqa: E402


def count_tests():
    """Number of automated tests, counted from the test folder so the guide never goes stale."""
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"))
    return suite.countTestCases()


TEST_COUNT = count_tests()

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
    canvas.drawCentredString(w / 2, h * 0.42, "Complete Project Guide: Version 1 and Version 2")
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
    canvas.drawRightString(w - 2 * cm, h - 0.72 * cm, f"Project Guide, Version {config.VERSION}")
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 1 * cm, f"{doc.page}")
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2.3 * cm, rightMargin=2.3 * cm, topMargin=2.0 * cm,
                          bottomMargin=1.8 * cm, title="My-Woofie: Complete Project Guide",
                          author="Aashna Batabyal", subject="Desktop Break Companion, Version 1 and Version 2")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=cover, autoNextPageTemplate="body"),
                          PageTemplate(id="body", frames=[frame], onPage=page)])
    W = doc.width
    s = [Spacer(1, 1), PageBreak()]

    # ---------------- 1. at a glance
    s += [P("1. My-Woofie at a Glance", "h1"),
          P("My-Woofie is a small pixel-art puppy who lives on top of your desktop. He wanders along the edge of "
            "the screen, trots after your cursor, and keeps you company while you work. Once you have worked for "
            "the focus time you chose (four hours by default), he barks, shows a speech bubble with a specific "
            "suggestion, and counts down your break. When the break is over, he calls you back with a soft chime."),
          P("He is a companion first and a timer second: small, calm, a little silly, and easy to read and change. "
            "Everything runs locally on your own computer, in plain Python with PyQt6."),
          Spacer(1, 4),
          table([["The Problem", "It is easy to lose track of time at a screen, and an ordinary timer is just as easy to dismiss and forget."],
                 ["The Idea", "A companion you actually enjoy having around, who nudges you toward real breaks and is happier when you take them."],
                 ["Who It Is For", "Anyone who works at a computer for hours at a time, such as students, developers, writers and designers."],
                 ["Privacy", "It never captures your screen, logs keystrokes, reads files or window titles, or uses the network. Activity is judged only by elapsed time and mouse movement."],
                 ["Platforms", "Windows and macOS (Python 3.9 or newer), with packaged downloads. It also runs from source on Linux."]],
                [3.2 * cm, W - 3.2 * cm], header=False),
          Spacer(1, 8),
          table([["Number", "What It Counts"],
                 ["6", "pixel-art dogs: Aspen, Biscuit, Cocoa, Bailey, Benny and Snow"],
                 ["53 x 47", "pixels: the exact on-screen size of every dog, now a fixed rule for any future avatar"],
                 ["4 h / 15 min", "default focus time and break length, both adjustable"],
                 ["13", "headline features added in Version 2"],
                 [str(TEST_COUNT), "automated tests (19 in Version 1)"],
                 ["0", "network calls, screenshots, keystrokes or window titles recorded"]],
                [3.2 * cm, W - 3.2 * cm]),
          PageBreak()]

    # ---------------- 2. pups
    s += [P("2. Meet the Pups", "h1"),
          P("My-Woofie comes with six dogs. Choose yours on first launch, and change your mind at any time from "
            "the right-click menu. Aspen, Biscuit and Cocoa are drawn in code from a colour palette, while Bailey, "
            "Benny and Snow are built from the original design sheet. Every dog has ten animation frames: idle, "
            "walking, barking, the back-to-work hop and a happy pose."),
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
          picture("actual-size.png", 10, "Every dog is exactly 53 x 47 pixels on screen, shown here at true size. Any new avatar must match this size."),
          PageBreak()]

    # ---------------- 3. V1
    s += [P("3. Version 1: The Foundation", "h1"),
          P("Version 1 delivered the complete core experience: a calm companion, a reliable timer and a retro look."),
          table([["Feature", "What It Does"],
                 ["Six Pixel-Art Dogs", "Each dog is drawn on a fixed 53 x 47 pixel canvas with ten frames, and is chosen in a retro avatar picker."],
                 ["Avatar Picker", "Choose a dog on first launch. Tick \"ask me every time\" to choose again at every start. Closing the picker without choosing is never remembered."],
                 ["Cursor Following", "He trots toward the cursor while you move the mouse, and wanders along the screen edge when you are still."],
                 ["Focus and Break Timer", "Four hours of focus and a 15-minute break by default, adjustable from a dialog, the command line or the config file."],
                 ["Presence Detection", "Only 15 continuous minutes without mouse movement resets the focus timer, because that means you were genuinely away."],
                 ["Sound", "A bark and a soft howl when the break starts and a soft chime when it ends, all generated in code, with system beeps as a fallback if audio fails."],
                 ["Speech Bubbles", "Pixel-style bubbles show rotating messages from break_prompts.txt and focus_prompts.txt, and always appear in silent mode."],
                 ["Retro Meter", "A focus meter that turns from green to amber to red, a break countdown, and a flashing back-to-work banner."],
                 ["Menu and Tray", "Pause, timer settings, change avatar, focus meter, mute, reset and quit."],
                 ["Easy to Stop", "Quit from the menu, or run python main.py --stop from any terminal. Only one copy can run at a time."],
                 ["Local Only", "Settings are saved in a local JSON file. There is no network access, screen capture or key logging."]],
                [3.8 * cm, W - 3.8 * cm]),
          Spacer(1, 6), picture("hud-and-bubble.png", 9, "The retro meter and a speech bubble during a break."),
          PageBreak()]

    # ---------------- 4. V2
    s += [P("4. Version 2: What Is New", "h1"),
          P("Version 2 turns the timer into a companion with habits, moods and things to do, while keeping the same "
            "privacy rules. Every feature below is built, tested and merged. The point releases 2.0.1 and 2.0.2 "
            "added a start-up prompt for your timers, a locked dog size, a chase that always reaches the cursor, "
            "and a more dependable bedtime nudge."),
          table([["Feature", "What It Does"],
                 ["1. Snooze with a Cost", "A \"Snooze 5 min\" button on the break card, limited per focus cycle (two by default, adjustable from 0 to 5). Each snooze lowers his mood and is counted in your stats."],
                 ["2. Smarter Breaks", "Short micro-breaks every 20 minutes: a 20-second eye rest, stretch, water sip or posture check, with Done and Skip buttons. They never appear right before a big break, while you are away, or during a fullscreen app."],
                 ["3. Break Guidance", "The break card suggests something specific, such as a stretch, a glass of water, a short walk or some slow breathing. The suggestion changes every 25 seconds and comes from break_tips.txt."],
                 ["4. Settings Window", "Right-click the dog and choose Settings. Five tabs (Timers, Pet, Sound, System and Data) cover timers, speed, volume, night behaviour, start at login and your data."],
                 ["5. Mood and Streaks", "Real breaks make him happy, while skipped breaks and snoozes make him droopy and slower. Healthy days build a streak, and one missing day is forgiven."],
                 ["6. Petting, Treats and Fetch", "Click and hold to pet him and see hearts. Give him a treat (five a day). Play fetch by dragging and throwing the ball; he chases it and brings it back to your cursor."],
                 ["7. Time of Day", "At night he curls up for a nap when the mouse has been still for a minute, in the morning he stretches and greets you, and late at night he gives a gentle bedtime nudge."],
                 ["8. Wardrobe", "A party hat, flower, beanie, bandana, top hat and crown, unlocked by streak days (1, 3, 5, 7, 10 and 14)."],
                 ["9. Fullscreen Awareness", "While a program covers a whole monitor, or in Presentation mode, he hides and alerts wait. An overdue break starts as soon as the fullscreen app closes."],
                 ["10. Multi-Monitor Support", "He wanders between monitors, chases the cursor across them, and shows alerts on the monitor your cursor is on."],
                 ["11. Start at Login and Tray", "Optional autostart on Windows, macOS and Linux. Click the tray icon for a status message, or double-click it to pause."],
                 ["12. Local-Only Stats", "A weekly summary of breaks taken and skipped, snoozes, focus time and streak. You can delete everything with one click, or with --stats and --delete-data."],
                 ["13. Packaged Builds", "A PyInstaller recipe and a GitHub Actions workflow that builds a Windows .exe and a macOS .app and attaches them to a release."]],
                [3.8 * cm, W - 3.8 * cm]),
          PageBreak(),
          P("The New Screens", "h1"),
          picture("v2/break-card.png", 11, "The break card shows a specific suggestion, a countdown, a Snooze button (with snoozes left) and an OK button."),
          picture("v2/micro-break.png", 11, "A micro-break card between big breaks, with Done and Skip buttons."),
          picture("v2/settings.png", 11, "The settings window. Every option is saved to settings.json."),
          PageBreak(),
          picture("v2/weekly-summary.png", 11.5, "The weekly summary. Green bars are breaks taken and red bars are breaks skipped. It is stored only on your computer."),
          picture("v2/wardrobe.png", 11.5, "The wardrobe. Locked items show the streak they need."),
          PageBreak(),
          P("Accessories on Every Dog", "h2"),
          P("Each accessory is drawn onto the same 53 x 47 canvas, so the window never changes size. To make room "
            "for hats, the dog is drawn a few pixels smaller. The rows are the party hat, flower, beanie, top hat, "
            "crown and bandana."),
          picture("v2/accessories.png", 13.5),
          PageBreak()]

    # ---------------- 5. a day
    s += [P("5. A Day with My-Woofie", "h1"),
          table([["What You Are Doing", "What He Does"],
                 ["Moving the mouse", "He trots after your cursor, running faster when it is far away, and keeps going until he has caught up. This works across monitors too."],
                 ["Keeping the mouse still", "He sits beside the cursor for a few seconds, then wanders slowly along the screen edge and rests now and then."],
                 ["Clicking and holding on him", "He hops happily and shows hearts, and his mood goes up."],
                 ["Every 20 minutes of focus", "A quick eye rest, stretch, water or posture card appears. Click Done or Skip."],
                 ["Working past your focus time", "He walks to the middle of the screen, barks, and shows a break card with a tip and a Snooze button while your break counts down."],
                 ["Stepping away during the break", "The break is recorded as taken, his mood rises and your streak grows."],
                 ["Working through the break", "The break is recorded as skipped and his mood drops."],
                 ["Break time is over", "A soft chime and a back-to-work bubble, then he goes back to wandering."],
                 ["Mouse still at night", "After about a minute he curls up and naps with Zzz, and wakes the moment you move the mouse."],
                 ["First activity in the morning", "A stretch and a greeting."],
                 ["Still working late at night", "A bedtime message appears in a speech bubble, and repeats every hour while you keep working."],
                 ["A presentation or fullscreen app", "He hides and holds alerts until it ends."],
                 ["Right-clicking him", "The menu opens: pause, snooze, presentation mode, treat, fetch, wardrobe, weekly summary and settings."]],
                [5.0 * cm, W - 5.0 * cm]),
          Spacer(1, 10), P("The Focus and Break Cycle", "h2"), phase_diagram(),
          P("A break counts as <b>taken</b> if the mouse was active for no more than 25% of it, and as "
            "<b>skipped</b> otherwise. Only mouse movement is used, never what is on your screen.", "body"),
          PageBreak()]

    # ---------------- 6. how it works
    s += [P("6. How It Works", "h1"),
          P("The code is split into small, readable modules so that every feature can be debugged and changed on "
            "its own in VS Code. The timer, pet, stats, mood and scheduling logic do not depend on Qt, which means "
            "they are tested with a fake clock."),
          table([["Module", "Role"],
                 ["main.py", "A thin launcher: command-line options, the single-instance check and the startup dialogs."],
                 ["companion.py", "WoofieApp, which owns every window and part and runs the 33 ms main loop."],
                 ["timer.py", "The session timer: presence detection, FOCUS / BREAK / HAUL phases, snooze, break quality and deferral."],
                 ["pet.py", "The finite state machine and movement: roam, chase, sleep, treat, fetch, alerts and multi-monitor travel."],
                 ["gui.py, retro.py", "Transparent click-through windows, sprites, meter, bubbles, emotes, toys, the break card and the retro styling."],
                 ["dialogs.py", "The settings window, weekly summary and wardrobe."],
                 ["stats.py, mood.py", "Per-day counters and streaks, plus mood, daily limits and wardrobe state."],
                 ["microbreak.py, tips.py, daypart.py", "The micro-break scheduler, the tip bank, and the night, morning and bedtime rules."],
                 ["toys.py, wardrobe.py", "Ball physics and the bone, plus the pixel-art accessories drawn onto frames."],
                 ["fullscreen.py, autostart.py, paths.py", "Fullscreen detection (by size only), start at login, and file locations for source and packaged builds."],
                 ["assets_builder.py, audio.py", "Sprite generation for all dogs, and synthesized sounds with beep fallbacks."],
                 ["settings.py, prompts.py, selector.py, timer_dialog.py, instance.py", "Saved settings, message banks, the avatar picker, the start-up timer dialog, and single-instance handling with --stop."]],
                [5.4 * cm, W - 5.4 * cm]),
          Spacer(1, 8), P("The Pet's State Machine", "h2"), state_diagram(),
          P("<b>Main loop.</b> Every 33 ms the app reads the cursor position, checks for a fullscreen app every "
            "three seconds, feeds the timer, turns timer events into statistics and mood changes, updates the "
            "micro-break scheduler and the day rhythm, moves the pet and any toys, and redraws the windows. Movement "
            "is scaled by the real time that has passed, so an uneven timer never makes him stall. The timer takes "
            "an injectable clock, so hours of behaviour can be simulated instantly in tests."),
          P("<b>Click-through windows.</b> The dog, bubble, emotes and meter ignore the mouse, so your clicks reach "
            "the apps underneath. Only the dog's own pixels, the fetch ball and the break card accept clicks, and "
            "none of them ever takes keyboard focus."),
          Spacer(1, 10)]

    # ---------------- 7. privacy
    s += [P("7. Privacy and Safety by Design", "h1"),
          P("These rules apply to both versions. They are enforced by the way the code is written, not by a setting."),
          table([["My-Woofie Never...", "How That Is Guaranteed"],
                 ["captures your screen", "No screen-capture API is imported or called anywhere."],
                 ["logs keystrokes", "Only the cursor position is read, once per tick. There is no keyboard hook."],
                 ["reads files or window titles", "No code reads another program's files, titles or names."],
                 ["uses the network", "There are no internet connections. The only socket is a local one used by --stop and the single-instance check."],
                 ["looks at your screen to detect fullscreen", "It compares the foreground window's size with the monitor size. On macOS it reads only window layer, transparency and bounds."],
                 ["sends your statistics anywhere", "stats.json holds only counters per date and stays in the project or user folder. Delete My Data removes it."],
                 ["locks or blocks you", "He nudges and you decide. Snooze, Skip and Pause are always available, although snoozes are limited per cycle by design."]],
                [5.4 * cm, W - 5.4 * cm]),
          Spacer(1, 8),
          callout("<b>One limitation to be aware of:</b> presence is judged only by time and mouse movement, so reading "
                  "or typing without touching the mouse for 15 minutes counts as being away."),
          PageBreak()]

    # ---------------- 8. install
    s += [P("8. Install, Run and Options", "h1"),
          P("You need Python 3.9 or newer on Windows or macOS.", "body"),
          code("git clone https://github.com/aashnology/My-Woofie.git\ncd My-Woofie\npython -m venv venv\n"
               "source venv/bin/activate        # Windows: venv\\Scripts\\activate\npip install -r requirements.txt\npython main.py"),
          P("When you launch, a small dialog asks how long you want to focus and how long your break should be, "
            "and then you choose a pup the first time. If you prefer to keep your saved times, untick <b>Ask Me "
            "Every Time I Start</b> in that dialog."),
          P("Where to Find the Settings", "h2"),
          callout("<b>The settings are hidden by default.</b> My-Woofie has no window, toolbar or menu bar of its own, "
                  "so nothing is on screen except the dog (and a small tray icon, on systems that show one). The "
                  "controls for time and every other option only appear after you click. Until you do, everything "
                  "stays at its defaults: a four-hour focus time, a 15-minute break and the standard behaviour."),
          Spacer(1, 6)]
    s += bullets(["<b>Right-click the dog.</b> Click directly on the dog itself, because the rest of his window lets "
                  "clicks pass through. A menu opens with <b>Settings...</b> (timers, speed, sound, night behaviour, "
                  "start at login and data), Snooze, Presentation mode, treats, fetch, wardrobe and the weekly summary.",
                  "<b>Or use the tray icon.</b> Right-click the small My-Woofie icon near the clock (on Windows it may be "
                  "behind the up-arrow) to open the same menu. A single click shows a status message and a "
                  "double-click pauses him.",
                  "<b>At every start</b> (unless you switch it off), the focus and break dialog appears by itself."])
    s += [Spacer(1, 4),
          table([["I Want To...", "Do This"],
                 ["Stop him", "Right-click him and choose Quit My-Woofie, or run python main.py --stop in any terminal."],
                 ["Choose a different dog", "Right-click him and choose Change avatar..., or run python main.py --select."],
                 ["Start over", "Right-click him and choose Reset all settings..., or run python main.py --reset."],
                 ["Change timers, speed, sound or night behaviour", "Right-click him and choose Settings..."],
                 ["Snooze a break", "Click SNOOZE on the break card, or right-click him and choose Snooze this break."],
                 ["Hold alerts for a presentation", "Right-click him and choose Presentation mode."],
                 ["See my week", "Right-click him and choose Weekly summary..., or run python main.py --stats."],
                 ["Delete my statistics", "Open Settings, then Data, then Delete My Data, or run python main.py --delete-data."],
                 ["See a full cycle quickly", "Run python main.py --test (10 seconds of focus, 5 seconds of break, with the mouse kept moving)."],
                 ["Try the night behaviour", "Run python main.py --hour 1 to pretend it is 1 AM."]],
                [5.4 * cm, W - 5.4 * cm]),
          P("All options: --select, --reset, --settings, --stop, --test, --hour H, --focus MIN, --break MIN, --stats, "
            "--delete-data and --version.", "small"),
          P("Customizing", "h2")]
    s += bullets(["<b>Messages:</b> one per line in break_prompts.txt and focus_prompts.txt (a line starting with # is a comment). Changes apply without a restart.",
                  "<b>Break tips:</b> break_tips.txt, one tip per line in the form category|text (eyes, stretch, water, posture, walk or breathe).",
                  "<b>Sounds:</b> replace the files in assets/audio/, or change SOUND_EVENTS in config.py.",
                  "<b>Everything else:</b> the constants at the top of config.py, and the defaults in settings.py."])
    s += [P("Settings Reference", "h2"),
          table([["Setting", "Default", "Meaning"],
                 ["Focus time / break length", "240 min / 15 min", "When he asks for a break, and how long it lasts."],
                 ["Snooze length / snoozes per cycle", "5 min / 2", "How far a snooze postpones the break, and how many you get."],
                 ["Micro-breaks", "On, every 20 min, 20 s", "Short eye, stretch, water and posture reminders."],
                 ["Walking speed", "3 of 5", "How fast he moves."],
                 ["Wander between monitors", "On", "Whether he visits your other screens."],
                 ["Night naps and bedtime nudge", "On; night 22:00 to 06:00; nudge from 23:00", "The time-of-day behaviour."],
                 ["Volume / mute", "80% / Off", "The sound level, or speech bubbles only."],
                 ["Hold alerts during fullscreen", "On", "Fullscreen and presentation awareness."],
                 ["Always show focus meter", "Off", "By default the meter appears only during breaks."],
                 ["Ask for focus and break time at every start", "On", "Shows the timer dialog each time you launch."],
                 ["Keep break statistics", "On", "The local-only weekly summary and streaks."],
                 ["Start at login", "Off", "Autostart on Windows, macOS and Linux."]],
                [5.0 * cm, 4.3 * cm, W - 9.3 * cm]),
          Spacer(1, 12)]

    # ---------------- 9. packaging + tests
    s += [P("9. Packaging, Testing and Quality", "h1"),
          P("Building a Download", "h2"),
          code("pip install -r requirements-dev.txt\npython packaging/build.py     # runs the tests, then PyInstaller; the result is in dist/"),
          P("Build on the system you are targeting: Windows produces a .exe and macOS produces a .app. Pushing a tag "
            "such as v2.0.2 runs .github/workflows/release.yml, which tests the code, builds both versions on "
            "GitHub and attaches them to a release. Packaged builds keep settings, stats and the editable text "
            "files in your user folder instead of the program folder."),
          P("Tests", "h2"),
          code("python -m unittest discover -s tests"),
          P(f"{TEST_COUNT} automated tests run in a couple of seconds and need no real screen. They cover the timer "
            "(the full cycle, limits, the away reset, jitter, snooze, break quality and deferral), the pet (states, "
            "chasing all the way to the cursor, sleep, treats, fetch, multi-monitor travel and bounds), stats and "
            "streaks, mood and daily limits, micro-breaks, the day rhythm, tips, ball physics, start at login, "
            "fullscreen geometry, the start-up timer prompt and the settings window. They also check that every dog "
            "stays exactly 53 x 47 pixels, with every accessory."),
          P("What Was Verified, and What Was Not", "h2"),
          table([["Verified", "Not Yet Verified on Real Hardware"],
                 ["All automated tests; headless full-cycle runs (treat, fetch, micro-break, break, back to work and "
                  "a simulated 1 AM nap and bedtime nudge); a visual check of every accessory on every dog; "
                  "a PyInstaller build and start on Linux; and a real Windows desktop test of the dog size and "
                  "start-up flow.",
                  "Real macOS desktops, real multiple monitors, real fullscreen apps, audio devices, and the "
                  "Windows and macOS builds made by the release workflow. Those builds are unsigned, so the operating "
                  "system may show a security prompt on first launch."]],
                [W / 2, W / 2]),
          PageBreak()]

    # ---------------- 10. limits + ideas
    s += [P("10. Known Limitations and Ideas for the Future", "h1"),
          P("Known Limitations", "h2")]
    s += bullets(["Presence is judged by mouse movement only, so working without touching the mouse looks like being away.",
                  "Automatic fullscreen detection works on Windows. It is off on Linux and needs the optional Quartz package on macOS, but Presentation mode works everywhere.",
                  "A micro-break that times out on its own is not counted as done. Only a click on Done is recorded.",
                  "The sleeping pose reuses his happy frame, so he naps with his tongue out.",
                  "The default sounds are synthesized, so they sound artificial next to real recordings.",
                  "Click-through window masks can behave differently on macOS."])
    s += [P("Ideas for a Future Version (Not Built)", "h2")]
    s += bullets(["Real recorded bark and chime sounds.",
                  "More dogs, and a way to add your own from a PNG sprite sheet, always at the fixed 53 x 47 size.",
                  "Optional keyboard-activity awareness that never records what is typed.",
                  "Daily goals and gentle weekly reports.",
                  "Signed installers for Windows and macOS."])
    s += [PageBreak(), P("11. Quick Demo and Summary", "h1"),
          P("The 60-Second Demo", "h2"),
          code("python main.py --test"),
          table([["Time", "What to Show"],
                 ["0 s", "Pick a dog in the retro picker, then move the mouse and watch him run after the cursor."],
                 ["6 s", "A micro-break card appears (an eye rest). Click Done and his mood goes up."],
                 ["10 s", "The break starts: he barks, the card shows a tip and a Snooze button, and the meter counts down."],
                 ["Click Snooze", "The break moves away for a few seconds and then returns. Snoozes are limited."],
                 ["During the Break", "Hold the mouse still to take the break, or keep moving to skip it."],
                 ["After the Break", "A soft chime and the back-to-work banner. Open Weekly summary to see breaks taken and skipped."],
                 ["Right-Click Him", "Give a treat, play fetch, open the wardrobe, or open Settings."]],
                [3.0 * cm, W - 3.0 * cm]),
          P("The Pitch in Three Sentences", "h2"),
          callout("Breaks only help if you actually take them, and a plain timer is easy to ignore. My-Woofie is a "
                  "pixel puppy who stays on your desktop, nudges you toward real breaks with specific suggestions, "
                  "and gets happier when you take them. It does all of this locally, with no screen capture, no key "
                  "logging and no network access, so it is safe to leave running all day."),
          Spacer(1, 10), P("License and Links", "h2"),
          P(f"My-Woofie is released under the MIT License. Copyright 2026 Aashna Batabyal. The source code is at {REPO}. "
            "The repository also contains the User Guide and Technical Guide (in docs/), the changelog and the unit tests."),
          ]
    doc.build(s)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
