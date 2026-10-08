"""My-Woofie entry point.

Usage: python main.py [--select] [--reset] [--settings] [--test] [--focus MIN] [--break MIN]
                      [--stop] [--stats] [--delete-data] [--version]
"""
import argparse
import logging
import os
import signal
import sys

import config
from stats import Stats

log = logging.getLogger("woofie.main")


def resolve_timers(settings, args):
    """Work out the timer lengths (seconds) for this run."""
    pref = settings.pref
    if config.TEST_MODE or args.test:
        return dict(focus=config.TEST_FOCUS_SECONDS, brk=config.TEST_BREAK_SECONDS,
                    away=config.TEST_AWAY_SECONDS, haul=config.TEST_HAUL_SECONDS,
                    snooze=config.TEST_SNOOZE_SECONDS, max_snoozes=pref("max_snoozes"),
                    micro_interval=config.TEST_MICRO_INTERVAL_SECONDS,
                    micro_seconds=config.TEST_MICRO_SECONDS)
    focus = args.focus or pref("focus_minutes")
    brk = args.break_minutes or pref("break_minutes")
    return dict(focus=focus * 60, brk=brk * 60, away=config.AWAY_RESET_SECONDS,
                haul=config.HAUL_DISPLAY_SECONDS, snooze=pref("snooze_minutes") * 60,
                max_snoozes=pref("max_snoozes"), micro_interval=pref("micro_interval_minutes") * 60,
                micro_seconds=pref("micro_seconds"))


def pick_avatar(settings, force_select):
    """Use the saved avatar, or show the picker (first run, --select, or 'ask me every time')."""
    from assets_builder import available_avatars
    from selector import AvatarSelector
    saved = settings.get("avatar")
    ask = bool(settings.get("ask_avatar_each_launch", False))
    if saved in available_avatars() and not (force_select or ask):
        return saved
    current = saved if saved in available_avatars() else config.DEFAULT_AVATAR
    chosen = AvatarSelector.choose(current, ask)
    if chosen is None:  # dismissed: use the default for now but do not remember it
        return current
    settings.set("avatar", chosen[0])
    settings.set("ask_avatar_each_launch", chosen[1])
    return chosen[0]


def ask_timers_if_needed(settings, args, test_mode):
    """First launch (or --settings): let the user choose focus and break lengths."""
    from timer_dialog import TimerDialog
    if test_mode or (settings.get("focus_minutes") is not None and not args.settings):
        return
    chosen = TimerDialog.choose(settings.pref("focus_minutes"), settings.pref("break_minutes"))
    focus, brk = chosen or (settings.pref("focus_minutes"), settings.pref("break_minutes"))
    settings.update_many({"focus_minutes": focus, "break_minutes": brk})


def parse_args():
    parser = argparse.ArgumentParser(prog="my-woofie", description="My-Woofie, your digital desktop companion.")
    parser.add_argument("--reset", action="store_true", help="forget saved settings and run setup again")
    parser.add_argument("--version", action="version", version=f"My-Woofie {config.VERSION}")
    parser.add_argument("--stop", action="store_true", help="stop a running My-Woofie and exit")
    parser.add_argument("--select", action="store_true", help="choose a different avatar")
    parser.add_argument("--settings", action="store_true", help="open the timer settings at startup")
    parser.add_argument("--test", action="store_true", help="10 s focus / 5 s break, for debugging")
    parser.add_argument("--stats", action="store_true", help="print the last 7 days of break statistics and exit")
    parser.add_argument("--delete-data", action="store_true",
                        help="delete all statistics and progress (mood, wardrobe) and exit")
    parser.add_argument("--focus", type=float, metavar="MIN", help="focus minutes for this run only")
    parser.add_argument("--break", dest="break_minutes", type=float, metavar="MIN",
                        help="break minutes for this run only")
    return parser.parse_known_args()


def command_line_only(args):
    """Commands that need no window. Returns True if one was handled."""
    if args.stats:
        print(Stats(config.STATS_FILE).summary_text())
        return True
    if args.delete_data:
        Stats(config.STATS_FILE).delete_all()
        if os.path.isfile(config.PET_STATE_FILE):
            os.remove(config.PET_STATE_FILE)
        print("All My-Woofie statistics and progress were deleted.")
        return True
    return False


def main():
    args, qt_args = parse_args()
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO),
                        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                        datefmt="%H:%M:%S")
    if command_line_only(args):
        return

    from PyQt6.QtWidgets import QApplication
    import retro
    from assets_builder import ensure_assets
    from companion import WoofieApp
    from instance import InstanceServer, send_command
    from settings import Settings

    app = QApplication([sys.argv[0]] + qt_args)
    app.setQuitOnLastWindowClosed(False)
    if args.stop:
        print("Told My-Woofie to stop." if send_command("quit") else "My-Woofie is not running.")
        return
    if send_command("ping"):
        print("My-Woofie is already running. Stop him with: python main.py --stop")
        return
    server = InstanceServer(app)
    server.command_received.connect(lambda command: app.quit() if command == "quit" else None)
    retro.load_font()
    ensure_assets()
    if args.reset and os.path.isfile(config.SETTINGS_FILE):
        os.remove(config.SETTINGS_FILE)
        log.info("Saved settings removed")
    settings = Settings(config.SETTINGS_FILE)
    test_mode = config.TEST_MODE or args.test
    avatar = pick_avatar(settings, force_select=args.select)
    ask_timers_if_needed(settings, args, test_mode)
    timers = resolve_timers(settings, args)
    log.info("Starting My-Woofie %s: avatar=%s, focus=%ss, break=%ss, test_mode=%s",
             config.VERSION, avatar, timers["focus"], timers["brk"], test_mode)
    app.woofie = WoofieApp(app, settings, avatar, timers, test_mode)  # keep a reference alive
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    code = app.exec()
    log.info("My-Woofie stopped")
    sys.exit(code)


if __name__ == "__main__":
    main()
