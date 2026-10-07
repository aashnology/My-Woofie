"""Aspen entry point.

Usage: python main.py [--select] [--settings] [--test] [--focus MIN] [--break MIN]
"""
import argparse
import logging
import signal
import sys
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QActionGroup, QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

import config
import retro
from assets_builder import AVATARS, available_avatars, ensure_assets
from audio import SoundPlayer
from gui import BubbleWindow, HudWindow, PetWindow, format_clock, load_frames
from pet import Pet
from prompts import DEFAULT_BREAK, DEFAULT_FOCUS, PromptBank
from selector import AvatarSelector
from settings import Settings
from timer import Phase, SessionTimer
from timer_dialog import TimerDialog

log = logging.getLogger("aspen.main")


def minutes_text(minutes):
    if minutes >= 60 and minutes % 60 == 0:
        hours = int(minutes // 60)
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{minutes:g} minutes"


def resolve_timers(settings, args):
    """Work out the timer lengths (seconds) for this run."""
    if config.TEST_MODE or args.test:
        return dict(focus=config.TEST_FOCUS_SECONDS, brk=config.TEST_BREAK_SECONDS,
                    away=config.TEST_AWAY_SECONDS, haul=config.TEST_HAUL_SECONDS)
    focus = args.focus or settings.get("focus_minutes", config.DEFAULT_FOCUS_MINUTES)
    brk = args.break_minutes or settings.get("break_minutes", config.DEFAULT_BREAK_MINUTES)
    return dict(focus=focus * 60, brk=brk * 60, away=config.AWAY_RESET_SECONDS,
                haul=config.HAUL_DISPLAY_SECONDS)


class AspenApp:
    def __init__(self, app, settings, avatar, timers, test_mode):
        self.app = app
        self.settings = settings
        self.avatar = avatar
        self.test_mode = test_mode
        self.size_px = int(settings.get("size_px", config.SPRITE_TARGET_PX))
        self.hud_always = bool(settings.get("hud_always", config.HUD_ALWAYS_VISIBLE))
        self.screen = app.primaryScreen().availableGeometry()
        self.frames = load_frames(avatar, self.size_px)
        sprite = self.frames["idle"][0]

        self.window = PetWindow(self.frames, AVATARS[avatar].get("facing", 1))
        self.hud = HudWindow(self.screen)
        self.bubble = BubbleWindow()
        self.pet = Pet((self.screen.left(), self.screen.top(),
                        self.screen.left() + self.screen.width(),
                        self.screen.top() + self.screen.height()),
                       (sprite.width(), sprite.height()))
        self.session = SessionTimer(timers["focus"], timers["brk"], timers["away"], timers["haul"])
        self.audio = SoundPlayer(muted=bool(settings.get("muted", False)))
        self.break_prompts = PromptBank(config.BREAK_PROMPTS_FILE, DEFAULT_BREAK, config.PROMPT_ORDER)
        self.focus_prompts = PromptBank(config.FOCUS_PROMPTS_FILE, DEFAULT_FOCUS, config.PROMPT_ORDER)
        self._bubble_until = 0.0
        self.tray = None

        self._build_menu()
        self.window.clicked.connect(lambda: self.pet.pet_it(time.monotonic()))
        self.window.menu_requested.connect(lambda pos: self._menu.exec(pos))
        self._setup_tray()

        self.window.show()
        self.clock = QTimer()
        self.clock.timeout.connect(self._tick)
        self.clock.start(config.FRAME_INTERVAL_MS)

    # ----- menu and tray -----------------------------------------------------
    def _build_menu(self):
        """One menu shared by the tray icon and a right-click on Aspen."""
        menu = QMenu()
        menu.addAction("Timer settings...").triggered.connect(self._open_timer_settings)
        menu.addAction("Change avatar...").triggered.connect(self._change_avatar)

        size_menu = menu.addMenu("Size")
        self._size_group = QActionGroup(menu)
        for label, px in config.SIZE_CHOICES.items():
            action = size_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(px == self.size_px)
            action.triggered.connect(lambda _=False, p=px: self._set_size(p))
            self._size_group.addAction(action)

        meter = menu.addAction("Always show focus meter")
        meter.setCheckable(True)
        meter.setChecked(self.hud_always)
        meter.toggled.connect(self._set_hud_always)

        mute = menu.addAction("Mute sounds (bubbles only)")
        mute.setCheckable(True)
        mute.setChecked(bool(self.settings.get("muted", False)))
        mute.toggled.connect(self._set_muted)

        menu.addSeparator()
        menu.addAction("Quit Aspen").triggered.connect(self.app.quit)
        self._menu = menu

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("System tray unavailable; right-click Aspen for the menu")
            return
        self.tray = QSystemTrayIcon(QIcon(self.frames["idle"][0]), self.app)
        self.tray.setContextMenu(self._menu)
        self.tray.setToolTip("Aspen (right-click for menu)")
        self.tray.show()

    # ----- menu actions ----------------------------------------------------------
    def _reload_frames(self):
        self.frames = load_frames(self.avatar, self.size_px)
        self.window.set_frames(self.frames, AVATARS[self.avatar].get("facing", 1))
        self.pet.set_size((self.window.width(), self.window.height()))
        if self.tray is not None:
            self.tray.setIcon(QIcon(self.frames["idle"][0]))

    def _change_avatar(self):
        chosen = AvatarSelector.choose(self.avatar)
        if chosen is None or chosen == self.avatar:
            return
        self.avatar = chosen
        self._reload_frames()
        self.settings.set("avatar", chosen)
        log.info("Avatar changed to %s", chosen)

    def _set_size(self, px):
        self.size_px = px
        self._reload_frames()
        self.settings.set("size_px", px)
        log.info("Size set to %dpx", px)

    def _set_hud_always(self, value):
        self.hud_always = value
        self.settings.set("hud_always", value)

    def _set_muted(self, muted):
        self.audio.muted = muted
        self.settings.set("muted", muted)
        log.info("Sounds %s", "muted" if muted else "unmuted")

    def _open_timer_settings(self):
        if self.test_mode:
            self._say("Test mode is on, so the timers are fixed.")
            return
        current = (self.settings.get("focus_minutes", config.DEFAULT_FOCUS_MINUTES),
                   self.settings.get("break_minutes", config.DEFAULT_BREAK_MINUTES))
        chosen = TimerDialog.choose(*current)
        if chosen is None:
            return
        focus, brk = chosen
        self.settings.set("focus_minutes", focus)
        self.settings.set("break_minutes", brk)
        self.session.set_limits(focus * 60, brk * 60)
        self.session.restart_focus()
        self.pet.set_phase(Phase.FOCUS)
        self._say(f"Got it! First break in {minutes_text(focus)}.")

    # ----- main loop ---------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        point = QCursor.pos()
        cursor = (point.x(), point.y())

        changed = self.session.update(cursor)
        if changed is not None:
            self._on_phase(changed)

        chasing = self.session.seconds_since_move() < config.CHASE_WINDOW_SECONDS
        self.pet.update(cursor, chasing, now)
        y = self.pet.y + self.pet.bob(now)
        self.window.sync(self.pet.x, y, self.pet.animation(now), self.pet.facing, now)

        if self.bubble.isVisible():
            if now >= self._bubble_until:
                self.bubble.hide()
            else:
                self.bubble.follow(self.pet.x, y, self.window.width(), self.screen)
        self._update_hud(now)

    def _update_hud(self, now):
        phase = self.session.phase
        if not config.SHOW_HUD or (phase is Phase.FOCUS and not self.hud_always):
            if self.hud.isVisible():
                self.hud.hide()
            return
        if not self.hud.isVisible():
            self.hud.show()
        if phase is Phase.FOCUS:
            limit = self.session.focus_limit
            elapsed = min(self.session.focus_elapsed(), limit)
            fraction = elapsed / limit
            color = retro.GREEN if fraction < 0.6 else retro.AMBER if fraction < 0.85 else retro.RED
            self.hud.set_state("FOCUS", fraction, format_clock(limit - elapsed), color)
        elif phase is Phase.BREAK:
            remaining = self.session.break_remaining()
            self.hud.set_state("BREAK", remaining / self.session.break_limit,
                               format_clock(remaining), retro.BLUE)
        else:
            flash = int(now * 2) % 2 == 0
            self.hud.set_state("BACK TO WORK!", None, "", retro.GOLD if flash else retro.PAPER)

    # ----- phase changes -------------------------------------------------------------
    def _on_phase(self, phase):
        self.pet.set_phase(phase)
        if phase is Phase.BREAK:
            self.audio.play_event("break_start")
            self._say(self.break_prompts.next())
        elif phase is Phase.HAUL:
            self.audio.play_event("break_end")
            text = self._say(self.focus_prompts.next())
            if self.tray is not None:
                self.tray.showMessage("Aspen", text, QSystemTrayIcon.MessageIcon.Information, 8000)

    def _say(self, text):
        """Show a speech bubble. Always shown in silent mode; otherwise per ALWAYS_SHOW_BUBBLES."""
        if config.ALWAYS_SHOW_BUBBLES or self.audio.silent:
            self.bubble.say(text)
            self._bubble_until = time.monotonic() + config.BUBBLE_SECONDS
        return text


def pick_avatar(settings, force_select):
    saved = settings.get("avatar")
    if saved in available_avatars() and not force_select:
        return saved
    current = saved if saved in available_avatars() else config.DEFAULT_AVATAR
    chosen = AvatarSelector.choose(current) or current
    settings.set("avatar", chosen)
    return chosen


def ask_timers_if_needed(settings, args, test_mode):
    """First launch (or --settings): let the user choose focus and break lengths."""
    if test_mode or (settings.get("focus_minutes") is not None and not args.settings):
        return
    chosen = TimerDialog.choose(settings.get("focus_minutes", config.DEFAULT_FOCUS_MINUTES),
                                settings.get("break_minutes", config.DEFAULT_BREAK_MINUTES))
    focus, brk = chosen or (settings.get("focus_minutes", config.DEFAULT_FOCUS_MINUTES),
                            settings.get("break_minutes", config.DEFAULT_BREAK_MINUTES))
    settings.set("focus_minutes", focus)
    settings.set("break_minutes", brk)


def parse_args():
    parser = argparse.ArgumentParser(prog="aspen", description="Aspen, your digital desktop companion.")
    parser.add_argument("--select", action="store_true", help="choose a different avatar")
    parser.add_argument("--settings", action="store_true", help="open the timer settings at startup")
    parser.add_argument("--test", action="store_true", help="10 s focus / 5 s break, for debugging")
    parser.add_argument("--focus", type=float, metavar="MIN", help="focus minutes for this run only")
    parser.add_argument("--break", dest="break_minutes", type=float, metavar="MIN",
                        help="break minutes for this run only")
    return parser.parse_known_args()


def main():
    args, qt_args = parse_args()
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO),
                        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                        datefmt="%H:%M:%S")
    app = QApplication([sys.argv[0]] + qt_args)
    app.setQuitOnLastWindowClosed(False)
    retro.load_font()
    ensure_assets()
    settings = Settings(config.SETTINGS_FILE)
    test_mode = config.TEST_MODE or args.test
    avatar = pick_avatar(settings, force_select=args.select)
    ask_timers_if_needed(settings, args, test_mode)
    timers = resolve_timers(settings, args)
    log.info("Starting Aspen: avatar=%s, focus=%ss, break=%ss, test_mode=%s",
             avatar, timers["focus"], timers["brk"], test_mode)
    aspen = AspenApp(app, settings, avatar, timers, test_mode)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    code = app.exec()
    log.info("Aspen stopped")
    sys.exit(code)


if __name__ == "__main__":
    main()
