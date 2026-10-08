"""Where My-Woofie finds its bundled files and where it keeps the user's own data.

Running from source (python main.py) everything lives in the project folder, exactly as in V1.
Running from a packaged app (PyInstaller) the bundled assets are read-only, so settings, stats
and the editable message files move to a per-user folder.
"""
import os
import shutil
import sys

APP_FOLDER = "My-Woofie"


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def resource_dir():
    """Folder that holds assets/ and the default text files."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Folder for settings.json, stats.json and the pet's saved state."""
    if not is_frozen():
        return resource_dir()
    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        root = os.path.expanduser("~/Library/Application Support")
    else:
        root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    folder = os.path.join(root, APP_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def user_file(name):
    """Path of an editable text file. In a packaged app it is copied to the user folder once."""
    bundled = os.path.join(resource_dir(), name)
    if not is_frozen():
        return bundled
    target = os.path.join(data_dir(), name)
    if not os.path.isfile(target) and os.path.isfile(bundled):
        try:
            shutil.copyfile(bundled, target)
        except OSError:
            return bundled
    return target
