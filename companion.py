"""The My-Woofie application object: wires the timer, the pet, the windows and the V2 features together."""
import logging
import math
import time
from datetime import datetime

from PyQt6.QtCore import QRect, QTimer
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

import autostart
import config
import daypart
import retro
import wardrobe
from assets_builder import AVATARS
from audio import SoundPlayer
from dialogs import SettingsWindow, StatsWindow, WardrobeDialog
from fullscreen import FullscreenDetector
from gui import (AlertPanel, BubbleWindow, EmoteWindow, HudWindow, PetWindow, ToyWindow,
                 format_clock, load_frames)
from microbreak import MicroBreaks
from mood import PetState
from pet import ALERT_STATES, Pet, State
from prompts import DEFAULT_BREAK, DEFAULT_FOCUS, PromptBank
from selector import AvatarSelector
from settings import DEFAULTS
from stats import Stats
from timer import Phase, SessionTimer
from timer_dialog import TimerDialog
from tips import TipBank
from toys import Ball

log = logging.getLogger("woofie.app")

BREAK_TIP_KINDS = ("stretch", "water", "walk", "breathe", "eyes")
TIP_ROTATE_SECONDS = 25.0


def minutes_text(minutes):
    if minutes >= 60 and minutes % 60 == 0:
        hours = int(minutes // 60)
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{minutes:g} minutes"


def qrect_tuple(rect):
    return (rect.left(), rect.top(), rect.left() + rect.width(), rect.top() + rect.height())


class WoofieApp:
    def __init__(self, app, settings, avatar, timers, test_mode):
        self.app = app
        self.settings = settings
        self.avatar = avatar
        self.test_mode = test_mode
        self.timers = timers
        self.hud_always = bool(settings.pref("hud_always"))
        self.stats = Stats(config.STATS_FILE, enabled=bool(settings.pref("stats_enabled")))
        self.state = PetState(config.PET_STATE_FILE)
        self.stats.touch()
        self.fullscreen = FullscreenDetector()
        self.presentation_mode = False
        self._fullscreen_now = False
        self._next_fullscreen_poll = 0.0
        self._hidden = False

        self.screens = self._screen_rects()
        self.frames = load_frames(avatar, accessory=self.state.accessory)
        sprite = self.frames["idle"][0]
        self.window = PetWindow(self.frames, AVATARS[avatar].get("facing", 1))
        self.active_rect = self.app.primaryScreen().availableGeometry()
        self.hud = HudWindow(self.active_rect)
        self.bubble = BubbleWindow()
        self.emote = EmoteWindow()
        self.panel = AlertPanel()
        self.ball_window = ToyWindow("ball")
        self.bone_window = ToyWindow("bone")
        self.pet = Pet(self.screens[0], (sprite.width(), sprite.height()))
        self.pet.set_screens(self.screens)
        self.session = SessionTimer(timers["focus"], timers["brk"], timers["away"], timers["haul"],
                                    max_snoozes=timers["max_snoozes"])
        self.micro = MicroBreaks(timers["micro_interval"], timers["micro_seconds"],
                                 enabled=bool(settings.pref("micro_enabled")))
        self.rhythm = daypart.DayRhythm(settings.pref("sleep_start"), settings.pref("sleep_end"),
                                        settings.pref("bedtime_hour"), enabled=bool(settings.pref("night_sleep")))
        self.audio = SoundPlayer(muted=bool(settings.pref("muted")), volume=settings.pref("volume") / 100.0)
        self.break_prompts = PromptBank(config.BREAK_PROMPTS_FILE, DEFAULT_BREAK, config.PROMPT_ORDER)
        self.focus_prompts = PromptBank(config.FOCUS_PROMPTS_FILE, DEFAULT_FOCUS, config.PROMPT_ORDER)
        self.tips = TipBank(config.BREAK_TIPS_FILE, config.PROMPT_ORDER)

        self.ball = None
        self._current_tip = None
        self._micro_tip = None
        self._fetch_last = 0.0
        self._press_started = None
        self._next_pat = 0.0
        self._bubble_until = 0.0
        self._next_tip_at = 0.0
        self._focus_acc = 0.0
        self._last_tick = time.monotonic()
        self._next_save = self._last_tick + 60
        self._next_mood_emote = self._last_tick + 240
        self._last_bedtime = None
        self.paused = False
        self.tray = None
        self._menu = None

        self.pet.roam_all_screens = bool(settings.pref("roam_all_monitors"))
        self._build_menu()
        self._connect_signals()
        self._setup_tray()
        self.window.show()
        self.clock = QTimer()
        self.clock.timeout.connect(self._tick)
        self.clock.start(config.FRAME_INTERVAL_MS)
        if not settings.get("hint_shown"):
            QTimer.singleShot(1500, self._show_first_hint)
        else:
            QTimer.singleShot(1500, self._announce_unlocks)

    # ----- setup ---------------------------------------------------------------------------------
    def _connect_signals(self):
        self.window.pressed.connect(self._on_press)
        self.window.released.connect(self._on_release)
        self.window.menu_requested.connect(lambda pos: self._menu.exec(pos))
        self.panel.snooze_clicked.connect(self._snooze)
        self.panel.dismiss_clicked.connect(self.panel.hide)
        self.panel.done_clicked.connect(lambda: self._end_micro(done=True))
        self.panel.skip_clicked.connect(lambda: self._end_micro(done=False))
        self.ball_window.grabbed.connect(self._ball_grabbed)
        self.ball_window.dragged.connect(self._ball_dragged)
        self.ball_window.released.connect(self._ball_thrown)
        self.app.screenAdded.connect(lambda _s: self._refresh_screens())
        self.app.screenRemoved.connect(lambda _s: self._refresh_screens())
        self.app.primaryScreenChanged.connect(lambda _s: self._refresh_screens())
        self.app.aboutToQuit.connect(self._save_all)

    def _screen_rects(self):
        return [qrect_tuple(screen.availableGeometry()) for screen in self.app.screens()] or \
               [qrect_tuple(self.app.primaryScreen().availableGeometry())]

    def _refresh_screens(self):
        self.screens = self._screen_rects()
        self.pet.set_screens(self.screens)
        log.info("Monitors changed: %d screen(s)", len(self.screens))

    def _show_first_hint(self):
        self._say("Hi! Right-click me for settings, treats, fetch, or to quit.")
        self.settings.set("hint_shown", True)
        self._announce_unlocks()

    def _build_menu(self):
        """One menu shared by the tray icon and a right-click on My-Woofie."""
        menu = QMenu()
        self.pause_action = menu.addAction("Pause My-Woofie (hide him for now)")
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(self.paused)
        self.pause_action.toggled.connect(self._set_paused)

        self.snooze_action = menu.addAction("Snooze this break")
        self.snooze_action.triggered.connect(lambda _=False: self._snooze())
        self.presentation_action = menu.addAction("Presentation mode (hold alerts, hide him)")
        self.presentation_action.setCheckable(True)
        self.presentation_action.setChecked(self.presentation_mode)
        self.presentation_action.toggled.connect(self._set_presentation)
        menu.addSeparator()

        menu.addAction("Give a treat").triggered.connect(lambda _=False: self._give_treat())
        self.fetch_action = menu.addAction("Play fetch")
        self.fetch_action.setCheckable(True)
        self.fetch_action.setChecked(self.ball is not None)
        self.fetch_action.toggled.connect(self._set_fetch)
        menu.addAction("Wardrobe...").triggered.connect(lambda _=False: self._open_wardrobe())
        menu.addAction("Weekly summary...").triggered.connect(lambda _=False: self._show_summary())
        menu.addSeparator()

        menu.addAction("Settings...").triggered.connect(lambda _=False: self._open_settings())
        menu.addAction("Change avatar...").triggered.connect(lambda _=False: self._change_avatar())
        meter = menu.addAction("Always show focus meter")
        meter.setCheckable(True)
        meter.setChecked(self.hud_always)
        meter.toggled.connect(self._set_hud_always)
        mute = menu.addAction("Mute sounds (bubbles only)")
        mute.setCheckable(True)
        mute.setChecked(bool(self.settings.pref("muted")))
        mute.toggled.connect(self._set_muted)
        menu.addAction("Reset all settings...").triggered.connect(lambda _=False: self._reset_settings())
        menu.addSeparator()
        menu.addAction("Quit My-Woofie (stop the program)").triggered.connect(self.app.quit)
        menu.aboutToShow.connect(self._refresh_menu)
        self._menu = menu

    def _refresh_menu(self):
        self.snooze_action.setEnabled(self.session.can_snooze())
        left = self.session.snoozes_left()
        self.snooze_action.setText(f"Snooze this break ({left} left)" if self.session.phase is Phase.BREAK
                                   else "Snooze this break (only during a break)")
        self.fetch_action.blockSignals(True)
        self.fetch_action.setChecked(self.ball is not None)
        self.fetch_action.blockSignals(False)

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("System tray unavailable; right-click My-Woofie for the menu")
            return
        self.tray = QSystemTrayIcon(QIcon(self.frames["idle"][0]), self.app)
        self.tray.setContextMenu(self._menu)
        self.tray.activated.connect(self._on_tray)
        self._update_tooltip()
        self.tray.show()

    def _update_tooltip(self):
        if self.tray is not None:
            self.tray.setToolTip(f"My-Woofie: feeling {self.state.mood.level}, "
                                 f"{self.stats.streak()}-day streak (click for status)")

    def _on_tray(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._say_status()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.pause_action.setChecked(not self.paused)

    def _say_status(self):
        phase = self.session.phase
        if self.paused:
            text = "I'm paused. Double-click my tray icon to wake me up."
        elif phase is Phase.FOCUS:
            left = max(0.0, self.session.focus_limit - self.session.focus_elapsed())
            text = f"{format_clock(left)} until the next break. I'm feeling {self.state.mood.level}."
        elif phase is Phase.BREAK:
            text = f"Break time! {format_clock(self.session.break_remaining())} left."
        else:
            text = "Break's over. Back to it!"
        self.bubble_force(text)

    # ----- menu actions ----------------------------------------------------------------------------
    def _reload_frames(self):
        self.frames = load_frames(self.avatar, accessory=self.state.accessory)
        self.window.set_frames(self.frames, AVATARS[self.avatar].get("facing", 1))
        self.pet.set_size((self.window.width(), self.window.height()))
        if self.tray is not None:
            self.tray.setIcon(QIcon(self.frames["idle"][0]))

    def _change_avatar(self):
        ask = bool(self.settings.get("ask_avatar_each_launch", False))
        chosen = AvatarSelector.choose(self.avatar, ask)
        if chosen is None:
            return
        avatar, ask = chosen
        self.settings.set("ask_avatar_each_launch", ask)
        if avatar != self.avatar:
            self.avatar = avatar
            self._reload_frames()
            self.settings.set("avatar", avatar)
            log.info("Avatar changed to %s", avatar)

    def _reset_settings(self):
        """Forget every saved choice and run the setup screens again."""
        self.settings.clear()
        self._apply_settings(restart_timers=True)
        log.info("Settings reset")
        chosen = AvatarSelector.choose(config.DEFAULT_AVATAR, False)
        if chosen is not None:
            self.avatar = chosen[0]
            self.settings.set("avatar", chosen[0])
            self.settings.set("ask_avatar_each_launch", chosen[1])
            self._reload_frames()
        self._open_timer_quick_setup()
        self._rebuild_menu()

    def _rebuild_menu(self):
        self._build_menu()
        if self.tray is not None:
            self.tray.setContextMenu(self._menu)

    def _open_timer_quick_setup(self):
        if self.test_mode:
            self._say("Test mode is on, so the timers are fixed.")
            return
        chosen = TimerDialog.choose(self.settings.pref("focus_minutes"), self.settings.pref("break_minutes"))
        if chosen is None:
            return
        self.settings.update_many({"focus_minutes": chosen[0], "break_minutes": chosen[1]})
        self._apply_settings(restart_timers=True)
        self._say(f"Got it! First break in {minutes_text(chosen[0])}.")

    def _set_paused(self, paused):
        self.paused = paused
        if paused:
            self._hide_overlays(True)
        else:
            self.session.restart_focus()
            self.micro.reset()
            self.pet.set_phase(Phase.FOCUS)
            self._hide_overlays(False)
        log.info("My-Woofie %s", "paused" if paused else "resumed")

    def _set_presentation(self, on):
        self.presentation_mode = on
        log.info("Presentation mode %s", "on" if on else "off")

    def _set_hud_always(self, value):
        self.hud_always = value
        self.settings.set("hud_always", value)

    def _set_muted(self, muted):
        self.audio.muted = muted
        self.settings.set("muted", muted)
        log.info("Sounds %s", "muted" if muted else "unmuted")

    def _open_settings(self):
        current = {key: self.settings.pref(key) for key in DEFAULTS}
        result = SettingsWindow.edit(current, autostart.is_enabled(), True, self.test_mode,
                                     on_show_summary=self._show_summary, on_delete_data=self._delete_data)
        if result is None:
            return
        values, reset = result
        if reset:
            self._reset_settings()
            return
        start_at_login = values.pop("autostart", None)
        if start_at_login is not None and start_at_login != autostart.is_enabled():
            if not autostart.set_enabled(start_at_login):
                self._say("I couldn't change the start-at-login setting on this computer.")
        changed = {k: v for k, v in values.items() if self.settings.pref(k) != v}
        self.settings.update_many(values)
        self._apply_settings(restart_timers=any(k in changed for k in ("focus_minutes", "break_minutes")))
        self._rebuild_menu()
        self._say("Settings saved.")

    def _apply_settings(self, restart_timers=False):
        """Push the saved settings into the running parts."""
        pref = self.settings.pref
        if not self.test_mode:
            self.session.set_limits(pref("focus_minutes") * 60, pref("break_minutes") * 60)
            self.timers["snooze"] = pref("snooze_minutes") * 60
            self.micro.configure(pref("micro_interval_minutes") * 60, pref("micro_seconds"),
                                 bool(pref("micro_enabled")))
        else:
            self.micro.enabled = bool(pref("micro_enabled"))
        self.session.max_snoozes = pref("max_snoozes")
        if restart_timers:
            self.session.restart_focus()
            self.micro.reset()
            self.pet.set_phase(Phase.FOCUS)
        self.audio.muted = bool(pref("muted"))
        self.audio.volume = pref("volume") / 100.0
        self.hud_always = bool(pref("hud_always"))
        self.stats.enabled = bool(pref("stats_enabled"))
        self.pet.roam_all_screens = bool(pref("roam_all_monitors"))
        self.rhythm = daypart.DayRhythm(pref("sleep_start"), pref("sleep_end"), pref("bedtime_hour"),
                                        enabled=bool(pref("night_sleep")))

    # ----- statistics, wardrobe, data -----------------------------------------------------------------
    def _show_summary(self):
        self.stats.save()
        best = self.stats.best_streak()
        StatsWindow.show_summary(self.stats.week_summary(), self._delete_data, len(self.state.unlocked(best)))

    def _delete_data(self):
        self.stats.delete_all()
        self.state.delete()
        self._reload_frames()
        self._update_tooltip()
        self._say("All statistics and progress deleted.")

    def _open_wardrobe(self):
        best = self.stats.best_streak()
        choice = WardrobeDialog.choose(self.avatar, self.state.accessory, best)
        if choice is False:
            return
        if self.state.wear(choice, best):
            self._reload_frames()
            self.state.save()
            self.emote.show_emote("sparkle", time.monotonic(), 2.5)
            self._say("Looking good!" if choice else "Back to my usual look.")

    def _announce_unlocks(self):
        fresh = self.state.new_unlocks(self.stats.best_streak())
        if not fresh:
            return
        self.state.mark_seen(fresh)
        names = ", ".join(wardrobe.TITLES[n] for n in fresh)
        self.emote.show_emote("star", time.monotonic(), 4.0)
        self._say(f"New in the wardrobe: {names}! Right-click me to try it on.")

    # ----- snooze --------------------------------------------------------------------------------------
    def _snooze(self):
        if not self.session.snooze(self.timers["snooze"]):
            self._say("No snoozes left this time. Let's take that break!")
            return
        self.pet.set_phase(Phase.FOCUS)
        self.panel.hide()
        self.micro.reset()
        self._handle_timer_events()
        self._say(f"Okay, {minutes_text(self.timers['snooze'] / 60)} more. Then it's break time!")

    # ----- overlays ---------------------------------------------------------------------------------------
    def _hide_overlays(self, hidden):
        """Hide or restore every window (pause, fullscreen, presentation mode)."""
        self._hidden = hidden
        if hidden:
            for widget in (self.window, self.hud, self.bubble, self.emote, self.panel,
                           self.ball_window, self.bone_window):
                widget.hide()
            return
        self.window.show()
        if self.ball is not None:
            self.ball_window.show()
        if self.pet.bone is not None:
            self.bone_window.show()
        if self.session.phase is Phase.BREAK:
            self._show_break_panel()
        elif self.micro.active:
            self._show_micro_panel()

    def _poll_fullscreen(self, now):
        if now < self._next_fullscreen_poll:
            return
        self._next_fullscreen_poll = now + config.FULLSCREEN_POLL_SECONDS
        aware = bool(self.settings.pref("fullscreen_aware"))
        self._fullscreen_now = aware and self.fullscreen.is_fullscreen()

    def _deferred(self):
        return self.presentation_mode or self._fullscreen_now

    def bubble_force(self, text):
        self.bubble.say(text)
        self._bubble_until = time.monotonic() + config.BUBBLE_SECONDS

    def _say(self, text):
        """Show a speech bubble. Always shown in silent mode; otherwise per ALWAYS_SHOW_BUBBLES."""
        if config.ALWAYS_SHOW_BUBBLES or self.audio.silent:
            self.bubble_force(text)
        return text

    # ----- input: petting ---------------------------------------------------------------------------------
    def _on_press(self):
        now = time.monotonic()
        self._press_started = now
        self._next_pat = now + config.PET_HOLD_SECONDS
        self.pet.pet_it(now)
        if self.pet.state is State.SLEEP_STATE:
            self.pet.wake()
            self.emote.clear()

    def _on_release(self):
        self._press_started = None

    def _pet_tick(self, now):
        if self._press_started is None or now < self._next_pat:
            return
        self._next_pat = now + config.PET_TICK_SECONDS
        self.pet.pet_it(now)
        self.emote.show_emote("heart", now, 1.6)
        if self.state.pat():
            self.stats.record("pets")

    # ----- treats and fetch -----------------------------------------------------------------------------------
    def _give_treat(self):
        if self.session.phase is not Phase.FOCUS:
            self._say("Not now, it's break time!")
            return
        if self.state.treats_left() <= 0:
            self._say("I'm full for today! Maybe tomorrow.")
            return
        if self.pet.state is State.SLEEP_STATE:
            self.pet.wake()
            self.emote.clear()
        point = QCursor.pos()
        bone = self.pet.give_treat((point.x(), point.y()))
        if bone is None:
            return
        self.state.give_treat()
        self.stats.record("treats")
        self.bone_window.place(bone.x, bone.y)
        self.bone_window.show()
        log.info("Treat given (%d left today)", self.state.treats_left())

    def _set_fetch(self, on):
        if on:
            self._start_fetch()
        else:
            self._stop_fetch(say="That was fun!")

    def _start_fetch(self):
        if self.session.phase is not Phase.FOCUS:
            self._say("Not now, it's break time!")
            self.fetch_action.setChecked(False)
            return
        if self.pet.state is State.SLEEP_STATE:
            self.pet.wake()
            self.emote.clear()
        self.ball = Ball(0, 0)
        self.ball.place_center(self.pet.x + self.pet.w / 2 + 70 * self.pet.facing, self.pet.y + self.pet.h * 0.5)
        if not self.pet.start_fetch(self.ball):
            self.ball = None
            self.fetch_action.setChecked(False)
            return
        self._fetch_last = time.monotonic()
        self.ball_window.place(self.ball.x, self.ball.y)
        self.ball_window.show()
        self._say("Grab the ball with your mouse and throw it!")
        log.info("Fetch started")

    def _stop_fetch(self, say=None):
        if self.ball is None:
            return
        self.pet.stop_fetch()
        self.ball = None
        self.ball_window.hide()
        if self.fetch_action.isChecked():
            self.fetch_action.blockSignals(True)
            self.fetch_action.setChecked(False)
            self.fetch_action.blockSignals(False)
        if say:
            self._say(say)
        log.info("Fetch ended")

    def _ball_grabbed(self):
        if self.ball is not None:
            self.ball.grab()
            self._fetch_last = time.monotonic()

    def _ball_dragged(self, x, y):
        if self.ball is not None:
            self.ball.x, self.ball.y = x, y

    def _ball_thrown(self, vx, vy):
        if self.ball is not None:
            self.ball.release(vx, vy)
            self._fetch_last = time.monotonic()

    def _desktop_rect(self):
        lefts, tops, rights, bottoms = zip(*self.screens)
        return min(lefts), min(tops), max(rights), max(bottoms)

    def _sync_toys(self, now):
        if self.ball is not None:
            if now - self._fetch_last > config.FETCH_IDLE_TIMEOUT_SECONDS:
                self._stop_fetch(say="Okay, I'll rest now. Ask me for fetch any time!")
            else:
                self.ball.update(self._desktop_rect())
                if self.ball.carried:
                    self.ball.place_center(*self.pet.mouth_point())
                if not self.ball.held:
                    self.ball_window.place(self.ball.x, self.ball.y)
        if self.pet.bone is not None and self.bone_window.isVisible() is False and not self._hidden:
            self.bone_window.show()
        if self.pet.bone is None and self.bone_window.isVisible():
            self.bone_window.hide()

    def _handle_pet_events(self, now):
        for event in self.pet.events:
            if event == "treat_eaten":
                self.emote.show_emote("heart", now, 2.0)
            elif event == "ball_delivered":
                self._fetch_last = now
                self.emote.show_emote("heart", now, 2.0)
                if self.state.fetch_done():
                    self.stats.record("fetches")
        self.pet.events.clear()

    # ----- timer events and phases ------------------------------------------------------------------------------
    def _handle_timer_events(self):
        now = time.monotonic()
        for event in self.session.pop_events():
            if event == "taken":
                self.stats.record("taken")
                self.state.mood.apply("break_taken")
                self.emote.show_emote("heart", now, 3.0)
                self._announce_unlocks()
            elif event == "skipped":
                self.stats.record("skipped")
                self.state.mood.apply("break_skipped")
                self.emote.show_emote("sweat", now, 3.0)
            elif event == "snoozed":
                self.stats.record("snoozed")
                self.state.mood.apply("snoozed")
            elif event == "away":
                self.stats.record("away")
                self.state.mood.apply("away")
                self.micro.reset()
        self._update_tooltip()

    def _on_phase(self, phase):
        self.pet.set_phase(phase)
        self._end_micro(done=None, silent=True)
        self.micro.reset()
        self._stop_fetch()
        self.emote.clear()
        if phase is Phase.BREAK:
            self.audio.play_event("break_start")
            self._say(self.break_prompts.next())
            self._next_tip_at = time.monotonic() + TIP_ROTATE_SECONDS
            self._show_break_panel(new_tip=True)
        elif phase is Phase.HAUL:
            self.panel.hide()
            self.audio.play_event("break_end")
            text = self._say(self.focus_prompts.next())
            if self.tray is not None:
                self.tray.showMessage("My-Woofie", text, QSystemTrayIcon.MessageIcon.Information, 8000)
        else:
            self.panel.hide()

    def _show_break_panel(self, new_tip=False):
        if new_tip or self._current_tip is None:
            self._current_tip = self.tips.any_next(BREAK_TIP_KINDS)
        title, text = self._current_tip
        self.panel.move_to_screen(self.active_rect)
        self.panel.show_break(title, text, self.session.snoozes_left(), self.timers["snooze"] / 60.0)

    # ----- micro-breaks ----------------------------------------------------------------------------------------------
    def _show_micro_panel(self):
        title, text = self._micro_tip
        self.panel.move_to_screen(self.active_rect)
        self.panel.show_micro(title, text)

    def _update_micro(self, now):
        if self.micro.active:
            self.panel.set_time(f"{math.ceil(self.micro.remaining())}S")
            if self.micro.finished():
                self._end_micro(done=None)
            return
        kind = self.micro.update(self.session.focus_elapsed(), self.session.focus_limit,
                                 self.session.seconds_since_move(), deferred=self._deferred(),
                                 in_focus=self.session.phase is Phase.FOCUS)
        if kind is None:
            return
        self._micro_tip = self.tips.next(kind)
        self.audio.play_event("micro")
        self._show_micro_panel()

    def _end_micro(self, done, silent=False):
        """done=True/False for a click on DONE/SKIP, None when it simply timed out or was replaced."""
        if not self.micro.active:
            return
        self.micro.end()
        self.panel.hide()
        if done is True:
            self.stats.record("micro_done")
            self.state.mood.apply("micro_done")
        elif done is False:
            self.stats.record("micro_skipped")
            self.state.mood.apply("micro_skipped")

    # ----- time of day ---------------------------------------------------------------------------------------------------
    def _update_rhythm(self, now):
        if self.session.phase is not Phase.FOCUS or self.pet.state in ALERT_STATES:
            return
        wall = datetime.now()
        idle = self.session.seconds_since_move()
        sleeping = self.pet.state is State.SLEEP_STATE
        if sleeping:
            if idle < 1.0:
                self.pet.wake()
                self.emote.clear()
            return
        if self.rhythm.should_sleep(wall, idle) and self.pet.state in (State.ROAM_STATE, State.CHASE_STATE):
            self.pet.sleep()
            self.emote.show_emote("z1", now, 1e9)
            return
        if idle > 30:
            return
        if self.rhythm.morning_due(wall, self.settings.get("last_greeting")):
            self.settings.set("last_greeting", wall.date().isoformat())
            self.pet.stretch(now, 3.0)
            self._say(daypart.pick(daypart.MORNING_MESSAGES, wall.day))
        elif self.rhythm.bedtime_due(wall, self._last_bedtime):
            self._last_bedtime = wall
            self.emote.show_emote("z2", now, 3.0)
            self._say(daypart.pick(daypart.BEDTIME_MESSAGES, wall.hour))

    def _update_mood_display(self, now):
        if now < self._next_mood_emote or self.emote.active or self.pet.state in ALERT_STATES:
            return
        self._next_mood_emote = now + 240
        level = self.state.mood.level
        if level in ("droopy", "sad"):
            self.emote.show_emote("sweat", now, 3.0)
        elif level == "ecstatic":
            self.emote.show_emote("sparkle", now, 3.0)

    # ----- main loop ------------------------------------------------------------------------------------------------------------
    def _tick(self):
        if self.paused:
            return
        now = time.monotonic()
        dt = min(now - self._last_tick, 1.0)
        self._last_tick = now
        point = QCursor.pos()
        cursor = (point.x(), point.y())

        self._poll_fullscreen(now)
        deferred = self._deferred()
        self.session.defer_alerts = deferred
        changed = self.session.update(cursor)
        self._handle_timer_events()
        if changed is not None:
            self._on_phase(changed)
        self._track_focus_time(dt)
        if now >= self._next_save:
            self._next_save = now + 60
            self._save_all()

        if deferred:
            if not self._hidden:
                self._hide_overlays(True)
            return
        if self._hidden:
            self._hide_overlays(False)

        self.active_rect = self._rect_at(cursor)
        self._update_micro(now)
        self._update_rhythm(now)
        self._update_mood_display(now)
        self._pet_tick(now)

        sleeping = self.pet.state is State.SLEEP_STATE
        chasing = self.session.seconds_since_move() < config.CHASE_WINDOW_SECONDS and not sleeping
        self.pet.speed_scale = self.settings.speed_factor()
        self.pet.mood_scale = self.state.mood.speed_factor
        self.pet.update(cursor, chasing, now)
        self._handle_pet_events(now)
        self._sync_toys(now)
        y = self.pet.y + self.pet.bob(now)
        self.window.sync(self.pet.x, y, self.pet.animation(now), self.pet.facing, now)

        if self.bubble.isVisible():
            if now >= self._bubble_until:
                self.bubble.hide()
            else:
                self.bubble.follow(self.pet.x, y, self.window.width(), self._rect_at(
                    (self.pet.x + self.pet.w / 2, self.pet.y + self.pet.h / 2)))
        self.emote.tick(now, self.pet.x, y, self.window.width(), sleeping=sleeping)
        self._update_panel(now)
        self._update_hud(now)

    def _rect_at(self, point):
        index = self.pet._screen_index(point)
        left, top, right, bottom = self.screens[index]
        return QRect(left, top, right - left, bottom - top)

    def _track_focus_time(self, dt):
        """Count focus minutes (only while the mouse has moved in the last minute)."""
        if self.session.phase is Phase.FOCUS and self.session.seconds_since_move() < 60:
            self._focus_acc += dt
            if self._focus_acc >= 5:
                self.stats.add_focus_seconds(self._focus_acc)
                self._focus_acc = 0.0

    def _save_all(self):
        self.stats.add_focus_seconds(self._focus_acc)
        self._focus_acc = 0.0
        self.stats.save()
        self.state.save()

    def _update_panel(self, now):
        if self.session.phase is Phase.BREAK:
            self.panel.set_time(format_clock(self.session.break_remaining()))
            self.panel.set_snooze_left(self.session.snoozes_left(), self.timers["snooze"] / 60.0)
            if self.panel.isVisible() and now >= self._next_tip_at:
                self._next_tip_at = now + TIP_ROTATE_SECONDS
                self._current_tip = self.tips.any_next(BREAK_TIP_KINDS)
                self.panel.set_tip(*self._current_tip)
        if self.panel.isVisible():
            self.panel.move_to_screen(self.active_rect)

    def _update_hud(self, now):
        phase = self.session.phase
        if not config.SHOW_HUD or (phase is Phase.FOCUS and not self.hud_always):
            if self.hud.isVisible():
                self.hud.hide()
            return
        self.hud.move_to_screen(self.active_rect)
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
