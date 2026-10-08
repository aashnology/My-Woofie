# PyInstaller recipe for My-Woofie. Build with:  python packaging/build.py
# Produces dist/My-Woofie.exe (Windows) or dist/My-Woofie.app (macOS).
import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
is_mac = sys.platform == "darwin"
is_win = sys.platform.startswith("win")

datas = [
    (os.path.join(ROOT, "assets"), "assets"),
    (os.path.join(ROOT, "break_prompts.txt"), "."),
    (os.path.join(ROOT, "focus_prompts.txt"), "."),
    (os.path.join(ROOT, "break_tips.txt"), "."),
]
hidden = ["pygame"]
if is_mac:
    hidden += ["Quartz"]          # optional fullscreen detection

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter", "unittest", "test"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="My-Woofie",
    console=False,               # no terminal window; use `python main.py` for debug logs
)
coll = COLLECT(exe, a.binaries, a.datas, name="My-Woofie")
if is_mac:
    app = BUNDLE(coll, name="My-Woofie.app", bundle_identifier="com.aashnology.my-woofie",
                 info_plist={"LSUIElement": True,          # no Dock icon, tray only
                             "NSHighResolutionCapable": True})
