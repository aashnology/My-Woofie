"""Aspen entry point. Run with: python main.py   (add --select to re-open the avatar picker)"""
import logging
import signal
import sys
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QCursor, QIcon
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

log = logging.getLogger("aspen.main")


class AspenApp:
    def __init__(self, app, settings, avatar):
        self.app = app
        self.settings = settings
        self.avatar = avatar
        self.screen = app.primaryScreen().availableGeometry()
        self.frames = load_frames(avatar)
        sprite = self.frames["idle"][0]

        self.window = PetWindow(self.frames, AVATARS[avatar].get("facing", 1))
        self.hud = HudWindow(self.screen) if config.SHOW_HUD else None
        self.bubble = BubbleWindow()
        self.pet = Pet((self.screen.left(), self.screen.top(),
                        self.screen.left() + self.screen.width(),
                        self.screen.top() + self.screen.height()),
                       (sprite.width(), sprite.height()))
        self.session = SessionTimer()
        self.audio = SoundPlayer(muted=bool(settings.get("muted", False)))
        self.break_prompts = PromptBank(config.BREAK_PROMPTS_FILE, DEFAULT_BREAK, config.PROMPT_ORDER)
        self.focus_prompts = PromptBank(config.FOCUS_PROMPTS_FILE, DEFAULT_FOCUS, config.PROMPT_ORDER)
        self._bubble_until = 0.0
        self.tray = None
        self.window.clicked.connect(lambda: self.pet.pet_it(time.monotonic()))
        self._setup_tray()

        self.window.show()
        if self.hud is not None:
            self.hud.show()
        self.clock = QTimer()
        self.clock.timeout.connect(self._tick)
        self.clock.start(config.FRAME_INTERVAL_MS)

    # ----- tray ------------------------------------------------------------
    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("System tray unavailable; use 'python main.py --select' to change avatar")
            return
        self.tray = QSystemTrayIcon(QIcon(self.frames["idle"][0]), self.app)
        menu = QMenu()
        change = QAction("Change avatar...", menu)
        change.triggered.connect(self._change_avatar)
        mute = QAction("Mute sounds (show speech bubbles only)", menu)
        mute.setCheckable(True)
        mute.setChecked(self.audio.muted)
        mute.toggled.connect(self._set_muted)
        quit_action = QAction("Quit Aspen", menu)
        quit_action.triggered.connect(self.app.quit)
        for action in (change, mute, quit_action):
            menu.addAction(action)
        self._menu = menu
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Aspen")
        self.tray.show()

    def _change_avatar(self):
        chosen = AvatarSelector.choose(self.avatar)
        if chosen is None or chosen == self.avatar:
            return
        self.avatar = chosen
        self.frames = load_frames(chosen)
        self.window.set_frames(self.frames, AVATARS[chosen].get("facing", 1))
        self.pet.set_size((self.window.width(), self.window.height()))
        if self.tray is not None:
            self.tray.setIcon(QIcon(self.frames["idle"][0]))
        self.settings.set("avatar", chosen)
        log.info("Avatar changed to %s", chosen)

    def _set_muted(self, muted):
        self.audio.muted = muted
        self.settings.set("muted", muted)
        log.info("Sounds %s", "muted" if muted else "unmuted")

    # ----- main loop -------------------------------------------------------
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
        if self.hud is None:
            return
        phase = self.session.phase
        if phase is Phase.FOCUS:
            limit = config.FOCUS_TIME_LIMIT_SECONDS
            elapsed = min(self.session.focus_elapsed(), limit)
            fraction = elapsed / limit
            color = retro.GREEN if fraction < 0.6 else retro.AMBER if fraction < 0.85 else retro.RED
            self.hud.set_state("FOCUS", fraction, format_clock(limit - elapsed), color)
        elif phase is Phase.BREAK:
            remaining = self.session.break_remaining()
            self.hud.set_state("BREAK", remaining / config.BREAK_TIME_LIMIT_SECONDS,
                               format_clock(remaining), retro.BLUE)
        else:
            flash = int(now * 2) % 2 == 0
            self.hud.set_state("BACK TO WORK!", None, "", retro.GOLD if flash else retro.PAPER)

    # ----- phase changes ---------------------------------------------------
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


def main():
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO),
                        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                        datefmt="%H:%M:%S")
    log.info("Starting Aspen (TEST_MODE=%s, focus=%ss, break=%ss)", config.TEST_MODE,
             config.FOCUS_TIME_LIMIT_SECONDS, config.BREAK_TIME_LIMIT_SECONDS)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    retro.load_font()
    ensure_assets()
    settings = Settings(config.SETTINGS_FILE)
    avatar = pick_avatar(settings, force_select="--select" in sys.argv)
    log.info("Avatar: %s", avatar)
    aspen = AspenApp(app, settings, avatar)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    code = app.exec()
    log.info("Aspen stopped")
    sys.exit(code)


if __name__ == "__main__":
    main()
