"""Toys for My-Woofie (V2): the fetch ball and the treat bone. Pure physics, no Qt.

Coordinates are screen pixels. `rect` arguments are (left, top, right, bottom).
"""
import math

import config


class Ball:
    """A ball you can pick up with the mouse and throw. It slides, slows down and bounces."""

    def __init__(self, x, y):
        self.size = config.BALL_SIZE
        self.x, self.y = float(x), float(y)       # top-left corner
        self.vx = self.vy = 0.0
        self.held = False                          # the user is dragging it
        self.carried = False                       # the dog has it in his mouth
        self.in_play = False                       # thrown and not yet brought back

    @property
    def center(self):
        return self.x + self.size / 2, self.y + self.size / 2

    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    def place_center(self, cx, cy):
        self.x, self.y = cx - self.size / 2, cy - self.size / 2

    def grab(self):
        self.held, self.carried = True, False
        self.vx = self.vy = 0.0
        self.in_play = False

    def release(self, vx, vy):
        """Let go of the ball with the velocity of the drag (pixels per frame)."""
        self.held = False
        self.vx, self.vy = vx, vy
        self.in_play = True

    def drop(self):
        """The dog delivered it: it rests where he stands until you throw it again."""
        self.carried = False
        self.in_play = False
        self.vx = self.vy = 0.0

    def update(self, rect):
        """Advance one frame inside rect. Held or carried balls are positioned by their owner."""
        if self.held or self.carried:
            return
        self.x += self.vx
        self.y += self.vy
        left, top, right, bottom = rect
        if self.x < left:
            self.x, self.vx = left, abs(self.vx) * config.BALL_BOUNCE
        elif self.x > right - self.size:
            self.x, self.vx = right - self.size, -abs(self.vx) * config.BALL_BOUNCE
        if self.y < top:
            self.y, self.vy = top, abs(self.vy) * config.BALL_BOUNCE
        elif self.y > bottom - self.size:
            self.y, self.vy = bottom - self.size, -abs(self.vy) * config.BALL_BOUNCE
        self.vx *= config.BALL_FRICTION
        self.vy *= config.BALL_FRICTION
        if self.speed < 0.15:
            self.vx = self.vy = 0.0


class Bone:
    """A treat lying on the screen until the dog has eaten it."""

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.size = 16

    @property
    def center(self):
        return self.x + self.size / 2, self.y + self.size / 2


def velocity_from_samples(samples, frame_ms=None):
    """Throw velocity (pixels per frame) from recent (time_seconds, x, y) drag samples."""
    frame_s = (frame_ms or config.FRAME_INTERVAL_MS) / 1000.0
    if len(samples) < 2:
        return 0.0, 0.0
    t0, x0, y0 = samples[0]
    t1, x1, y1 = samples[-1]
    span = t1 - t0
    if span <= 0:
        return 0.0, 0.0
    vx, vy = (x1 - x0) / span * frame_s, (y1 - y0) / span * frame_s
    top = 28.0                                   # keep throws from teleporting across the screen
    speed = math.hypot(vx, vy)
    if speed > top:
        vx, vy = vx / speed * top, vy / speed * top
    return vx, vy
