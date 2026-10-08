"""Start My-Woofie when you log in (V2). Windows, macOS and Linux.

Windows: a value under HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run (no admin needed).
macOS:   a LaunchAgent plist in ~/Library/LaunchAgents.
Linux:   a .desktop file in ~/.config/autostart.
Nothing is installed system-wide and disabling removes exactly what enabling added.
"""
import logging
import os
import sys
from xml.sax.saxutils import escape

import paths

log = logging.getLogger("woofie.autostart")

NAME = "My-Woofie"
MAC_LABEL = "com.aashnology.my-woofie"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def command_line():
    """The program and arguments that start My-Woofie (a list)."""
    if paths.is_frozen():
        return [sys.executable]
    script = os.path.join(paths.resource_dir(), "main.py")
    python = sys.executable
    if sys.platform.startswith("win"):                # no console window at login
        windowless = os.path.join(os.path.dirname(python), "pythonw.exe")
        if os.path.isfile(windowless):
            python = windowless
    return [python, script]


def _quote(part):
    return f'"{part}"' if " " in part else part


def mac_plist(command):
    args = "\n".join(f"        <string>{escape(part)}</string>" for part in command)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n'
            f"    <key>Label</key>\n    <string>{MAC_LABEL}</string>\n"
            f"    <key>ProgramArguments</key>\n    <array>\n{args}\n    </array>\n"
            "    <key>RunAtLoad</key>\n    <true/>\n"
            "</dict>\n</plist>\n")


def linux_desktop(command):
    return ("[Desktop Entry]\nType=Application\nName=My-Woofie\n"
            "Comment=Desktop break companion\n"
            f"Exec={' '.join(_quote(p) for p in command)}\n"
            "X-GNOME-Autostart-enabled=true\nTerminal=false\n")


def _mac_path(home):
    return os.path.join(home, "Library", "LaunchAgents", MAC_LABEL + ".plist")


def _linux_path(home):
    return os.path.join(home, ".config", "autostart", "my-woofie.desktop")


def is_enabled(platform=None, home=None):
    platform = platform or sys.platform
    home = home or os.path.expanduser("~")
    try:
        if platform.startswith("win"):
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, NAME)
            return True
        if platform == "darwin":
            return os.path.isfile(_mac_path(home))
        return os.path.isfile(_linux_path(home))
    except (OSError, ImportError):
        return False


def set_enabled(enabled, platform=None, home=None, command=None):
    """Turn start-at-login on or off. Returns True on success."""
    platform = platform or sys.platform
    home = home or os.path.expanduser("~")
    command = command or command_line()
    try:
        if platform.startswith("win"):
            import winreg
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                if enabled:
                    winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, " ".join(_quote(p) for p in command))
                else:
                    try:
                        winreg.DeleteValue(key, NAME)
                    except FileNotFoundError:
                        pass
            return True
        if platform == "darwin":
            path, text = _mac_path(home), mac_plist(command)
        else:
            path, text = _linux_path(home), linux_desktop(command)
        if enabled:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        elif os.path.isfile(path):
            os.remove(path)
        log.info("Start at login %s", "enabled" if enabled else "disabled")
        return True
    except (OSError, ImportError) as exc:
        log.warning("Could not change start at login: %s", exc)
        return False
