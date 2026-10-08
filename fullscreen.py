"""Fullscreen / presentation awareness (V2).

My-Woofie holds back alerts while another program covers a whole monitor (a presentation, a
video call share, a game or a movie). Only window SIZES are compared with monitor sizes. No window
title, program name or screen content is ever read.

Windows uses user32 through ctypes. macOS needs the optional `pyobjc-framework-Quartz` package;
without it, use "Presentation mode" in the menu, which does the same thing by hand.
"""
import logging
import sys

log = logging.getLogger("woofie.fullscreen")


def covers(window, monitor, tolerance=1):
    """True if the window rectangle (l, t, r, b) covers the monitor rectangle."""
    return (window[0] <= monitor[0] + tolerance and window[1] <= monitor[1] + tolerance
            and window[2] >= monitor[2] - tolerance and window[3] >= monitor[3] - tolerance)


def _windows_fullscreen():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    class MonitorInfo(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    hwnd = user32.GetForegroundWindow()
    if not hwnd or hwnd in (user32.GetDesktopWindow(), user32.GetShellWindow()):
        return False
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False
    info = MonitorInfo()
    info.cbSize = ctypes.sizeof(MonitorInfo)
    monitor = user32.MonitorFromWindow(hwnd, 2)       # MONITOR_DEFAULTTONEAREST
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return False
    m = info.rcMonitor
    return covers((rect.left, rect.top, rect.right, rect.bottom), (m.left, m.top, m.right, m.bottom))


def _mac_fullscreen():
    import Quartz  # optional: pip install pyobjc-framework-Quartz

    displays = []
    err, ids, count = Quartz.CGGetActiveDisplayList(16, None, None)
    for display_id in (ids or [])[:count]:
        b = Quartz.CGDisplayBounds(display_id)
        displays.append((b.origin.x, b.origin.y, b.origin.x + b.size.width, b.origin.y + b.size.height))
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly,
                                                Quartz.kCGNullWindowID) or []
    for window in windows:
        # Only the layer, transparency and bounds are read; names are never touched.
        if window.get("kCGWindowLayer") != 0 or float(window.get("kCGWindowAlpha", 1)) <= 0:
            continue
        b = window.get("kCGWindowBounds")
        if not b:
            continue
        rect = (b["X"], b["Y"], b["X"] + b["Width"], b["Y"] + b["Height"])
        if any(covers(rect, display) for display in displays):
            return True
    return False


class FullscreenDetector:
    def __init__(self):
        self.available = False
        self._probe = None
        if sys.platform.startswith("win"):
            self._probe = _windows_fullscreen
            self.available = True
        elif sys.platform == "darwin":
            try:
                import Quartz  # noqa: F401
                self._probe = _mac_fullscreen
                self.available = True
            except ImportError:
                log.info("Quartz not installed; use Presentation mode in the menu on macOS")
        else:
            log.info("Automatic fullscreen detection is not available on this system")
        self._failed = False

    def is_fullscreen(self):
        """True when a program covers a whole monitor. Never raises."""
        if self._probe is None or self._failed:
            return False
        try:
            return bool(self._probe())
        except Exception as exc:  # a failed probe must never take the pet down
            log.warning("Fullscreen detection failed (%s); turning it off", exc)
            self._failed = True
            return False
