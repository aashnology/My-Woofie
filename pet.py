"""Finite state machine and movement logic for Aspen."""
import logging
import math
import random
from enum import Enum

import config
from timer import Phase

log = logging.getLogger("aspen.pet")


class State(Enum):
    ROAM_STATE = "ROAM_STATE"
    CHASE_STATE = "CHASE_STATE"
    BARK_ALERT_STATE = "BARK_ALERT_STATE"
    HAUL_ALERT_STATE = "HAUL_ALERT_STATE"


class Pet:
    def __init__(self, bounds, size):
        """bounds = (left, top, right, bottom) of the screen, size = (width, height) of the sprite."""
        left, top, right, bottom = bounds
        self.w, self.h = size
        self.min_x, self.max_x = float(left), float(right - self.w)
        self.min_y, self.max_y = float(top), float(bottom - self.h)
        self.x, self.y = self.min_x, self.max_y
        self.facing = 1
        self.moving = False
        self.state = State.ROAM_STATE
        self._direction = 1
        self._s = self._nearest_s()
        self._on_perimeter = True
        self._pause_until = 0.0
        self._happy_until = 0.0

    def set_size(self, size):
        """Update the sprite size (used when the avatar changes) and keep Aspen on screen."""
        right = self.max_x + self.w
        bottom = self.max_y + self.h
        self.w, self.h = size
        self.max_x, self.max_y = right - self.w, bottom - self.h
        self.x = min(max(self.x, self.min_x), self.max_x)
        self.y = min(max(self.y, self.min_y), self.max_y)
        self._on_perimeter = False

    # ----- state machine -------------------------------------------------
    def _set_state(self, new_state):
        if new_state is self.state:
            return
        log.info("State %s -> %s", self.state.value, new_state.value)
        self.state = new_state
        if new_state is State.ROAM_STATE:
            self._on_perimeter = False

    def set_phase(self, phase):
        """Called by the app whenever the session timer changes phase."""
        if phase is Phase.BREAK:
            self._set_state(State.BARK_ALERT_STATE)
        elif phase is Phase.HAUL:
            self._set_state(State.HAUL_ALERT_STATE)
        else:
            self._set_state(State.ROAM_STATE)

    def update(self, cursor, chase_active, now):
        self.moving = False
        if self.state in (State.BARK_ALERT_STATE, State.HAUL_ALERT_STATE):
            target_x = (self.min_x + self.max_x) / 2
            target_y = self.min_y + (self.max_y - self.min_y) * 0.6
            self._step_toward(target_x, target_y, config.PET_SPEED * 2)
        elif chase_active:
            self._set_state(State.CHASE_STATE)
            self._chase(cursor)
        else:
            self._set_state(State.ROAM_STATE)
            self._roam(now)

    def pet_it(self, now):
        if self.state in (State.ROAM_STATE, State.CHASE_STATE):
            self._happy_until = now + 1.2
            log.info("Aspen got a pat")

    # ----- presentation helpers ------------------------------------------
    def animation(self, now):
        if self.state is State.BARK_ALERT_STATE:
            return "bark"
        if self.state is State.HAUL_ALERT_STATE:
            return "haul"
        if now < self._happy_until:
            return "happy"
        return "walk" if self.moving else "idle"

    def bob(self, now):
        """Vertical offset in pixels (negative = up) for hop animations, scaled to the sprite size."""
        scale = self.h / 160.0
        if self.state is State.BARK_ALERT_STATE:
            return -abs(math.sin(now * 5)) * 12 * scale
        if self.state is State.HAUL_ALERT_STATE:
            return -abs(math.sin(now * 3.5)) * 20 * scale
        if now < self._happy_until:
            return -abs(math.sin(now * 6)) * 10 * scale
        return 0.0

    # ----- movement ------------------------------------------------------
    def _step_toward(self, target_x, target_y, speed):
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return True
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        step = min(speed, dist)
        self.x = min(max(self.x + dx / dist * step, self.min_x), self.max_x)
        self.y = min(max(self.y + dy / dist * step, self.min_y), self.max_y)
        self.moving = True
        return dist <= speed

    def _chase(self, cursor):
        target_x = cursor[0] - self.w / 2
        target_y = cursor[1] - self.h / 2
        dist = math.hypot(target_x - self.x, target_y - self.y)
        if dist > config.CHASE_STOP_DISTANCE_PX:
            # an easy trot, a little quicker when the cursor is far away
            speed = config.PET_SPEED * (1 + 0.5 * min(dist / 600, 1.0))
            self._step_toward(target_x, target_y, speed)

    def _roam(self, now):
        if not self._on_perimeter:
            self._s = self._nearest_s()
            target_x, target_y = self._point_at(self._s)
            if self._step_toward(target_x, target_y, config.PET_SPEED):
                self._on_perimeter = True
            return
        if now < self._pause_until:
            return
        if random.random() < 0.01:
            self._pause_until = now + random.uniform(2.0, 6.0)
            return
        if random.random() < 0.002:
            self._direction *= -1
        self._s += self._direction * config.PET_SPEED * 0.5
        new_x, new_y = self._point_at(self._s)
        if abs(new_x - self.x) > 0.1:
            self.facing = 1 if new_x > self.x else -1
        self.x, self.y = new_x, new_y
        self.moving = True

    def _point_at(self, s):
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        s %= 2 * (width + height)
        if s < width:
            return self.min_x + s, self.min_y
        s -= width
        if s < height:
            return self.max_x, self.min_y + s
        s -= height
        if s < width:
            return self.max_x - s, self.max_y
        s -= width
        return self.min_x, self.max_y - s

    def _nearest_s(self):
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        px = min(max(self.x, self.min_x), self.max_x)
        py = min(max(self.y, self.min_y), self.max_y)
        candidates = [
            (px, self.min_y, px - self.min_x),
            (self.max_x, py, width + (py - self.min_y)),
            (px, self.max_y, width + height + (self.max_x - px)),
            (self.min_x, py, 2 * width + height + (self.max_y - py)),
        ]
        best = min(candidates, key=lambda c: (c[0] - self.x) ** 2 + (c[1] - self.y) ** 2)
        return best[2]
