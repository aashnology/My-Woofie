"""Finite state machine and movement logic for My-Woofie.

V2 adds multi-monitor roaming, sleep, stretch, treats and fetch on top of the V1 states.
"""
import logging
import math
import random
from enum import Enum

import config
from timer import Phase

log = logging.getLogger("woofie.pet")


class State(Enum):
    ROAM_STATE = "ROAM_STATE"
    CHASE_STATE = "CHASE_STATE"
    BARK_ALERT_STATE = "BARK_ALERT_STATE"
    HAUL_ALERT_STATE = "HAUL_ALERT_STATE"
    SLEEP_STATE = "SLEEP_STATE"
    TREAT_STATE = "TREAT_STATE"
    FETCH_STATE = "FETCH_STATE"


ALERT_STATES = (State.BARK_ALERT_STATE, State.HAUL_ALERT_STATE)


class Pet:
    def __init__(self, bounds, size):
        """bounds = (left, top, right, bottom) of the screen, size = (width, height) of the sprite."""
        self.w, self.h = size
        self.screens = [tuple(bounds)]
        self.current = 0
        self._use_screen(0)
        self.x, self.y = self.min_x, self.max_y
        self.facing = 1
        self.moving = False
        self.state = State.ROAM_STATE
        self.speed_scale = 1.0           # Settings slider and mood
        self.mood_scale = 1.0
        self._direction = 1
        self._s = self._nearest_s()
        self._on_perimeter = True
        self._pause_until = 0.0
        self._happy_until = 0.0
        self._stretch_until = 0.0
        self._hop_at = None
        self._travel_to = None
        self.alert_screen = 0
        self.roam_all_screens = True
        # toys
        self.ball = None
        self.bone = None
        self.carrying = False
        self._eat_until = 0.0
        self.events = []                 # "treat_eaten", "ball_picked", "ball_delivered"

    # ----- screens -------------------------------------------------------------------------------
    @property
    def bounds(self):
        return self.screens[self.current]

    def _use_screen(self, index):
        self.current = index
        left, top, right, bottom = self.screens[index]
        self.min_x, self.max_x = float(left), float(right - self.w)
        self.min_y, self.max_y = float(top), float(bottom - self.h)

    def set_screens(self, rects):
        """Tell the pet about every monitor (call again when monitors change)."""
        rects = [tuple(r) for r in rects] or [self.bounds]
        self.screens = rects
        index = self._screen_index((self.x + self.w / 2, self.y + self.h / 2))
        self._use_screen(index)
        self.alert_screen = min(self.alert_screen, len(rects) - 1)
        self._hop_at = None
        self._travel_to = None
        self.x, self.y = self._clamp(self.x, self.y)
        self._on_perimeter = False

    def _screen_index(self, point):
        px, py = point
        best, best_dist = 0, float("inf")
        for i, (left, top, right, bottom) in enumerate(self.screens):
            dx = max(left - px, 0, px - right)
            dy = max(top - py, 0, py - bottom)
            dist = dx * dx + dy * dy
            if dist < best_dist:
                best, best_dist = i, dist
        return best

    def _desktop(self):
        lefts, tops, rights, bottoms = zip(*self.screens)
        return min(lefts), min(tops), max(rights), max(bottoms)

    def _clamp(self, x, y):
        """Keep the sprite on the virtual desktop (all monitors together)."""
        left, top, right, bottom = self._desktop()
        return (min(max(x, left), right - self.w), min(max(y, top), bottom - self.h))

    def set_size(self, size):
        """Update the sprite size (used when the avatar changes) and keep My-Woofie on screen."""
        self.w, self.h = size
        self._use_screen(self.current)
        self.x = min(max(self.x, self.min_x), self.max_x)
        self.y = min(max(self.y, self.min_y), self.max_y)
        self._on_perimeter = False

    # ----- state machine -------------------------------------------------------------------------
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
            self._end_toys()
            self._set_state(State.BARK_ALERT_STATE)
        elif phase is Phase.HAUL:
            self._end_toys()
            self._set_state(State.HAUL_ALERT_STATE)
        else:
            self._set_state(State.ROAM_STATE)

    def _end_toys(self):
        self.bone = None
        self.carrying = False
        if self.ball is not None:
            self.ball.carried = False

    @property
    def speed(self):
        return config.PET_SPEED * self.speed_scale * self.mood_scale

    def update(self, cursor, chase_active, now):
        self.moving = False
        cursor_screen = self._screen_index(cursor)
        self.alert_screen = cursor_screen
        if self.state in ALERT_STATES:
            left, top, right, bottom = self.screens[cursor_screen]
            target_x = (left + right - self.w) / 2
            target_y = top + (bottom - self.h - top) * 0.6
            self._step_toward(target_x, target_y, config.PET_SPEED * 2)
        elif self.state is State.SLEEP_STATE:
            pass
        elif self.state is State.TREAT_STATE:
            self._treat(now)
        elif self.state is State.FETCH_STATE:
            self._fetch(cursor, now)
        elif chase_active:
            self._set_state(State.CHASE_STATE)
            self._chase(cursor)
        else:
            self._set_state(State.ROAM_STATE)
            self._roam(now)
        self._follow_screen()

    def _follow_screen(self):
        """Adopt the monitor the pet is standing on (so roaming uses that monitor's edge)."""
        if len(self.screens) < 2 or self._travel_to is not None:
            return
        index = self._screen_index((self.x + self.w / 2, self.y + self.h / 2))
        if index != self.current:
            self._use_screen(index)
            self._on_perimeter = False

    # ----- interaction -------------------------------------------------------------------------
    def pet_it(self, now):
        if self.state in (State.ROAM_STATE, State.CHASE_STATE, State.FETCH_STATE):
            self._happy_until = max(self._happy_until, now + 1.2)
            log.info("My-Woofie got a pat")

    def stretch(self, now, seconds=3.0):
        if self.state in (State.ROAM_STATE, State.CHASE_STATE):
            self._stretch_until = now + seconds
            self._pause_until = max(self._pause_until, now + seconds)

    def sleep(self):
        if self.state in ALERT_STATES or self.state is State.SLEEP_STATE:
            return
        self._end_toys()
        self._set_state(State.SLEEP_STATE)

    def wake(self):
        if self.state is State.SLEEP_STATE:
            self._set_state(State.ROAM_STATE)

    def give_treat(self, point):
        """Drop a bone at point (screen coordinates) for him to run to."""
        from toys import Bone
        if self.state in ALERT_STATES:
            return None
        left, top, right, bottom = self._desktop()
        bx = min(max(point[0] - 8, left), right - 16)
        by = min(max(point[1] - 8, top), bottom - 16)
        self.bone = Bone(bx, by)
        self._eat_until = 0.0
        self._set_state(State.TREAT_STATE)
        return self.bone

    def start_fetch(self, ball):
        if self.state in ALERT_STATES:
            return False
        self.ball = ball
        self.carrying = False
        self._set_state(State.FETCH_STATE)
        return True

    def stop_fetch(self):
        self.carrying = False
        if self.ball is not None:
            self.ball.carried = False
        self.ball = None
        if self.state is State.FETCH_STATE:
            self._set_state(State.ROAM_STATE)

    def mouth_point(self):
        """Where a carried ball sits (the front of the dog)."""
        return (self.x + self.w * (0.5 + 0.42 * self.facing), self.y + self.h * 0.72)

    # ----- presentation helpers ----------------------------------------------------------------
    def animation(self, now):
        if self.state is State.BARK_ALERT_STATE:
            return "bark"
        if self.state is State.HAUL_ALERT_STATE:
            return "haul"
        if self.state is State.SLEEP_STATE:
            return "sleep"
        if self.state is State.TREAT_STATE and now < self._eat_until:
            return "happy"
        if now < self._happy_until:
            return "happy"
        if now < self._stretch_until and not self.moving:
            return "stretch"
        return "walk" if self.moving else "idle"

    def bob(self, now):
        """Vertical offset in pixels (negative = up) for hop animations, scaled to the sprite size."""
        scale = self.h / 160.0
        if self.state is State.BARK_ALERT_STATE:
            return -abs(math.sin(now * 5)) * 12 * scale
        if self.state is State.HAUL_ALERT_STATE:
            return -abs(math.sin(now * 3.5)) * 20 * scale
        if self.state is State.SLEEP_STATE:
            return 0.0
        if now < self._happy_until or (self.state is State.TREAT_STATE and now < self._eat_until):
            return -abs(math.sin(now * 6)) * 10 * scale
        return 0.0

    # ----- movement ----------------------------------------------------------------------------
    def _step_toward(self, target_x, target_y, speed):
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return True
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        step = min(speed, dist)
        self.x, self.y = self._clamp(self.x + dx / dist * step, self.y + dy / dist * step)
        self.moving = True
        return dist <= speed

    def _chase(self, cursor):
        target_x = cursor[0] - self.w / 2
        target_y = cursor[1] - self.h / 2
        dist = math.hypot(target_x - self.x, target_y - self.y)
        if dist > config.CHASE_STOP_DISTANCE_PX:
            # an easy trot, a little quicker when the cursor is far away
            speed = self.speed * (1 + 0.5 * min(dist / 600, 1.0))
            self._step_toward(target_x, target_y, speed)

    def _treat(self, now):
        if self.bone is None:
            self._set_state(State.ROAM_STATE)
            return
        if self._eat_until:
            if now >= self._eat_until:
                self.bone = None
                self._eat_until = 0.0
                self.events.append("treat_eaten")
                self._happy_until = now + 1.5
                self._set_state(State.ROAM_STATE)
            return
        cx, cy = self.bone.center
        if self._step_toward(cx - self.w / 2, cy - self.h / 2, self.speed * 2.2) \
                or math.hypot(cx - (self.x + self.w / 2), cy - (self.y + self.h / 2)) < self.w * 0.45:
            self._eat_until = now + 2.2
            log.info("My-Woofie is eating a treat")

    def _fetch(self, cursor, now):
        ball = self.ball
        if ball is None:
            self._set_state(State.ROAM_STATE)
            return
        bx, by = ball.center
        my_x, my_y = self.x + self.w / 2, self.y + self.h / 2
        if ball.held:
            self.facing = 1 if bx > my_x else -1
            return
        if self.carrying:
            tx, ty = cursor[0] - self.w / 2 - self.facing * 30, cursor[1] - self.h / 2
            if self._step_toward(tx, ty, self.speed * 2.4) \
                    or math.hypot(cursor[0] - my_x, cursor[1] - my_y) < 70:
                self.carrying = False
                ball.drop()
                ball.place_center(*self.mouth_point())
                self._happy_until = now + 2.0
                self.events.append("ball_delivered")
                log.info("Fetch: ball delivered")
            return
        if ball.in_play:
            if math.hypot(bx - my_x, by - my_y) < self.w * 0.5 and ball.speed < 6:
                self.carrying = True
                ball.carried = True
                self.events.append("ball_picked")
                log.info("Fetch: ball picked up")
                return
            self._step_toward(bx - self.w / 2, by - self.h / 2, self.speed * 3.0)

    def _roam(self, now):
        if self._maybe_hop(now):
            return
        if not self._on_perimeter:
            self._s = self._nearest_s()
            target_x, target_y = self._point_at(self._s)
            if self._step_toward(target_x, target_y, self.speed):
                self._on_perimeter = True
            return
        if now < self._pause_until:
            return
        if random.random() < 0.01:
            self._pause_until = now + random.uniform(2.0, 6.0)
            return
        if random.random() < 0.002:
            self._direction *= -1
        self._s += self._direction * self.speed * 0.5
        new_x, new_y = self._point_at(self._s)
        if abs(new_x - self.x) > 0.1:
            self.facing = 1 if new_x > self.x else -1
        self.x, self.y = new_x, new_y
        self.moving = True

    def _maybe_hop(self, now):
        """With several monitors he occasionally wanders over to another one."""
        if len(self.screens) < 2 or not self.roam_all_screens:
            self._travel_to = None
            return False
        if self._travel_to is not None:
            left, top, right, bottom = self.screens[self._travel_to]
            target_x, target_y = (left + right - self.w) / 2, bottom - self.h
            if self._step_toward(target_x, target_y, self.speed * 1.6):
                self._use_screen(self._travel_to)
                self._travel_to = None
                self._on_perimeter = False
                self._hop_at = now + random.uniform(0.7, 1.3) * config.SCREEN_HOP_SECONDS
                log.info("My-Woofie arrived on monitor %d", self.current + 1)
            return True
        if self._hop_at is None:
            self._hop_at = now + random.uniform(0.7, 1.3) * config.SCREEN_HOP_SECONDS
        elif now >= self._hop_at:
            others = [i for i in range(len(self.screens)) if i != self.current]
            self._travel_to = random.choice(others)
            log.info("My-Woofie is heading to monitor %d", self._travel_to + 1)
            return True
        return False

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
