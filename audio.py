"""Sound playback. Sounds are preloaded; if pygame or a file is unavailable, system beeps are used."""
import logging
import os
import threading
from functools import partial

from PyQt6.QtCore import QTimer

import config

log = logging.getLogger("woofie.audio")


class SoundPlayer:
    def __init__(self, muted=False, volume=0.8):
        self.muted = muted
        self.volume = volume            # 0..1, from the Settings window; scales every sound
        self._pygame = None
        self._winsound = None
        self._sounds = {}
        try:
            import winsound
            self._winsound = winsound
        except ImportError:
            pass
        if not config.AUDIO_ENABLED:
            log.info("Audio disabled in config")
            return
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame
            pygame.mixer.init()
            self._pygame = pygame
            self._preload()
        except Exception as exc:  # pygame missing or no audio device
            log.warning("pygame.mixer unavailable (%s); using system beeps", exc)

    @property
    def silent(self):
        """True when My-Woofie should communicate visually only."""
        return self.muted or not config.AUDIO_ENABLED

    def _path(self, stem):
        return os.path.join(config.AUDIO_DIR, stem + ".wav")

    def _preload(self):
        stems = {stem for events in config.SOUND_EVENTS.values() for stem, _ in events}
        for stem in stems:
            path = self._path(stem)
            if not os.path.isfile(path):
                log.warning("Sound file missing: %s", path)
                continue
            try:
                sound = self._pygame.mixer.Sound(path)
                sound.set_volume(config.SOUND_VOLUMES.get(stem, 0.7))
                self._sounds[stem] = sound
            except Exception as exc:
                log.warning("Could not load %s: %s", path, exc)

    def play_event(self, event):
        """Play every sound mapped to an event, honouring each sound's delay."""
        for stem, delay_ms in config.SOUND_EVENTS.get(event, []):
            if delay_ms <= 0:
                self.play(stem)
            else:
                QTimer.singleShot(delay_ms, partial(self.play, stem))

    def play(self, stem):
        if self.silent:
            return
        sound = self._sounds.get(stem)
        if sound is not None:
            try:
                sound.set_volume(min(1.0, config.SOUND_VOLUMES.get(stem, 0.7) * self.volume / 0.8))
                sound.play()
                return
            except Exception as exc:
                log.warning("Playback of %s failed: %s", stem, exc)
        self._beep(stem)

    def _beep(self, stem):
        if self._winsound is not None:
            try:
                path = self._path(stem)
                if os.path.isfile(path):
                    self._winsound.PlaySound(path, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
                else:
                    threading.Thread(target=self._winsound.Beep, args=(900, 300), daemon=True).start()
                return
            except Exception:
                pass
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.beep()
        except Exception:
            print("\a", end="", flush=True)
