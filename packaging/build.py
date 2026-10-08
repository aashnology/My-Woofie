"""One-command build: python packaging/build.py

Runs the tests, makes sure the pixel art exists, then packages My-Woofie with PyInstaller.
Run it on the operating system you are building for (Windows -> .exe, macOS -> .app).
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run(*command):
    print(">", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    env = dict(os.environ, QT_QPA_PLATFORM=os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    print("> python -m unittest discover -s tests")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT, check=True, env=env)
    sys.path.insert(0, ROOT)
    from assets_builder import ensure_assets
    ensure_assets()
    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--distpath", "dist", "--workpath", "build", os.path.join("packaging", "my_woofie.spec"))
    print("\nDone. Look in the dist/ folder.")


if __name__ == "__main__":
    main()
