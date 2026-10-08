"""Retro dialogs added in V2: the Settings window, the weekly summary and the wardrobe."""
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (QCheckBox, QDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

import config
import retro
import wardrobe
from gui import load_frames
from stats import format_day


def retro_style():
    font = retro.family()
    return f"""
        QDialog {{ background: #1B1B2F; }}
        QLabel {{ color: #FFF4D6; font-family: "{font}"; font-size: 10px; }}
        QLabel#title {{ color: #FFC53D; font-size: 16px; }}
        QLabel#hint {{ color: #A9A4D0; font-size: 8px; }}
        QCheckBox {{ color: #FFF4D6; font-family: "{font}"; font-size: 10px; spacing: 10px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; background: #FFF4D6; border: 4px solid #FFC53D; }}
        QCheckBox::indicator:checked {{ background: #5BD36B; }}
        QSpinBox {{ background: #FFF4D6; color: #2A1A0A; border: 4px solid #FFC53D;
                    padding: 4px; font-family: "{font}"; font-size: 12px; min-width: 90px; }}
        QSlider::groove:horizontal {{ background: #3A3560; height: 10px; }}
        QSlider::handle:horizontal {{ background: #FFC53D; width: 16px; margin: -6px 0; border: 3px solid #2A1A0A; }}
        QPushButton {{ background: #FFC53D; color: #2A1A0A; border: 4px solid #2A1A0A;
                       padding: 8px 12px; font-family: "{font}"; font-size: 10px; }}
        QPushButton:hover {{ background: #FFE08A; }}
        QPushButton#danger {{ background: #F2545B; color: #FFF4D6; }}
        QPushButton#danger:hover {{ background: #FF7A80; }}
        QTabWidget::pane {{ border: 4px solid #FFC53D; background: #2B2347; top: -2px; }}
        QTabBar::tab {{ background: #3A3560; color: #FFF4D6; font-family: "{font}"; font-size: 9px;
                        padding: 8px 12px; border: 3px solid #2A1A0A; margin-right: 3px; }}
        QTabBar::tab:selected {{ background: #FFC53D; color: #2A1A0A; }}
        QMessageBox {{ background: #1B1B2F; }}
    """


def _ask(parent, title, text):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    return box.exec() == QMessageBox.StandardButton.Yes


class SettingsWindow(QDialog):
    """Every option in one place. `values()` returns the new settings as a dict."""

    def __init__(self, current, autostart_on, autostart_supported=True, test_mode=False,
                 on_show_summary=None, on_delete_data=None, on_reset=None):
        super().__init__()
        self.setWindowTitle("My-Woofie: settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(retro_style())
        self._current = dict(current)
        self._widgets = {}
        self._callbacks = (on_show_summary, on_delete_data, on_reset)
        self.requested_reset = False

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(10)
        title = QLabel("SETTINGS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        tabs = QTabWidget()
        root.addWidget(tabs)
        tabs.addTab(self._timers_tab(test_mode), "TIMERS")
        tabs.addTab(self._pet_tab(), "PET")
        tabs.addTab(self._sound_tab(), "SOUND")
        tabs.addTab(self._system_tab(autostart_on, autostart_supported), "SYSTEM")
        tabs.addTab(self._data_tab(), "DATA")

        buttons = QHBoxLayout()
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        save = QPushButton("SAVE")
        save.setDefault(True)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)
        self.setMinimumWidth(600)

    # ----- tab builders ------------------------------------------------------------------------------
    def _page(self):
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        return page, grid

    def _spin(self, key, low, high, grid, row, label, suffix=""):
        grid.addWidget(QLabel(label), row, 0)
        spin = QSpinBox()
        spin.setRange(low, high)
        spin.setValue(int(self._current[key]))
        if suffix:
            spin.setSuffix(suffix)
        grid.addWidget(spin, row, 1)
        self._widgets[key] = spin
        return spin

    def _check(self, key, grid, row, label):
        box = QCheckBox(label)
        box.setChecked(bool(self._current[key]))
        grid.addWidget(box, row, 0, 1, 2)
        self._widgets[key] = box
        return box

    def _hint(self, grid, row, text):
        label = QLabel(text)
        label.setObjectName("hint")
        label.setWordWrap(True)
        grid.addWidget(label, row, 0, 1, 2)

    def _timers_tab(self, test_mode):
        page, grid = self._page()
        focus = self._spin("focus_minutes", 1, 720, grid, 0, "FOCUS TIME BEFORE A BREAK", " min")
        brk = self._spin("break_minutes", 1, 120, grid, 1, "BREAK LENGTH", " min")
        self._spin("snooze_minutes", 1, 30, grid, 2, "SNOOZE LENGTH", " min")
        self._spin("max_snoozes", 0, 5, grid, 3, "SNOOZES PER FOCUS CYCLE")
        self._check("micro_enabled", grid, 4, "MICRO-BREAKS ON")
        self._spin("micro_interval_minutes", 5, 120, grid, 5, "MICRO-BREAK EVERY", " min")
        self._spin("micro_seconds", 10, 120, grid, 6, "MICRO-BREAK LENGTH", " sec")
        if test_mode:
            focus.setEnabled(False)
            brk.setEnabled(False)
            self._hint(grid, 7, "Test mode is on, so the focus and break timers are fixed.")
        else:
            self._hint(grid, 7, "Micro-breaks are quick eye, stretch, water and posture checks between the big breaks. Snoozes are limited so a break cannot be put off forever.")
        return page

    def _pet_tab(self):
        page, grid = self._page()
        grid.addWidget(QLabel("WALKING SPEED"), 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(1, 5)
        slider.setValue(int(self._current["pet_speed"]))
        grid.addWidget(slider, 0, 1)
        self._widgets["pet_speed"] = slider
        self._check("roam_all_monitors", grid, 1, "WANDER BETWEEN MONITORS")
        self._check("night_sleep", grid, 2, "NIGHT NAPS AND BEDTIME NUDGE")
        self._spin("sleep_start", 0, 23, grid, 3, "NIGHT STARTS AT (HOUR, 0-23)")
        self._spin("sleep_end", 0, 23, grid, 4, "NIGHT ENDS AT (HOUR, 0-23)")
        self._spin("bedtime_hour", 0, 23, grid, 5, "BEDTIME NUDGE FROM (HOUR, 0-23)")
        self._hint(grid, 6, "Night naps only happen when the mouse has been still for a couple of minutes.")
        return page

    def _sound_tab(self):
        page, grid = self._page()
        grid.addWidget(QLabel("VOLUME"), 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(int(self._current["volume"]))
        grid.addWidget(slider, 0, 1)
        self._widgets["volume"] = slider
        self._check("muted", grid, 1, "MUTE SOUNDS (BUBBLES ONLY)")
        return page

    def _system_tab(self, autostart_on, supported):
        page, grid = self._page()
        box = QCheckBox("START MY-WOOFIE WHEN I LOG IN")
        box.setChecked(autostart_on)
        box.setEnabled(supported)
        grid.addWidget(box, 0, 0, 1, 2)
        self._widgets["autostart"] = box
        self._check("fullscreen_aware", grid, 1, "HOLD ALERTS DURING FULLSCREEN")
        self._check("hud_always", grid, 2, "ALWAYS SHOW THE FOCUS METER")
        self._check("ask_timers_each_launch", grid, 3, "ASK FOR FOCUS AND BREAK TIME AT EVERY START")
        self._hint(grid, 4, "Fullscreen detection compares window sizes only. It never reads titles "
                            "or screen contents. On macOS it needs the optional pyobjc-framework-Quartz "
                            "package, or use Presentation mode from the menu.")
        return page

    def _data_tab(self):
        page, grid = self._page()
        self._check("stats_enabled", grid, 0, "KEEP BREAK STATISTICS (LOCAL ONLY)")
        self._hint(grid, 1, "Statistics never leave this computer. Turn this off to stop recording.")
        summary = QPushButton("SHOW WEEKLY SUMMARY")
        summary.clicked.connect(lambda: self._callbacks[0] and self._callbacks[0]())
        grid.addWidget(summary, 2, 0, 1, 2)
        delete = QPushButton("DELETE MY DATA")
        delete.setObjectName("danger")
        delete.clicked.connect(self._delete)
        grid.addWidget(delete, 3, 0, 1, 2)
        reset = QPushButton("RESET ALL SETTINGS")
        reset.setObjectName("danger")
        reset.clicked.connect(self._reset)
        grid.addWidget(reset, 4, 0, 1, 2)
        return page

    def _delete(self):
        if _ask(self, "Delete my data", "Delete all statistics, mood and wardrobe progress?\nThis cannot be undone."):
            if self._callbacks[1]:
                self._callbacks[1]()

    def _reset(self):
        if _ask(self, "Reset settings", "Forget every saved setting and start setup again?"):
            self.requested_reset = True
            self.accept()

    # ----- result --------------------------------------------------------------------------------------
    def values(self):
        out = {}
        for key, widget in self._widgets.items():
            if isinstance(widget, (QCheckBox,)):
                out[key] = widget.isChecked()
            else:
                out[key] = widget.value()
        return out

    @staticmethod
    def edit(current, autostart_on, autostart_supported=True, test_mode=False, **callbacks):
        """Show the window. Returns (values, reset_requested) or None if cancelled."""
        dialog = SettingsWindow(current, autostart_on, autostart_supported, test_mode, **callbacks)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.values(), dialog.requested_reset
        return None


class StatsWindow(QDialog):
    """Seven-day bar chart of breaks taken and skipped, with the current streak."""
    W, H = 540, 430

    def __init__(self, summary, on_delete=None, unlocked_count=0):
        super().__init__()
        self.setWindowTitle("My-Woofie: weekly summary")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(retro_style())
        self.setFixedSize(self.W, self.H)
        self.summary = summary
        self.unlocked_count = unlocked_count
        self.deleted = False
        close = QPushButton("CLOSE", self)
        close.setGeometry(24, self.H - 58, 150, 38)
        close.clicked.connect(self.accept)
        delete = QPushButton("DELETE MY DATA", self)
        delete.setObjectName("danger")
        delete.setGeometry(self.W - 24 - 190, self.H - 58, 190, 38)
        delete.clicked.connect(lambda: self._delete(on_delete))

    def _delete(self, callback):
        if _ask(self, "Delete my data", "Delete all statistics, mood and wardrobe progress?\nThis cannot be undone."):
            if callback:
                callback()
            self.deleted = True
            self.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), retro.NAVY)
        retro.draw_text(p, QRect(0, 16, self.W, 30), "THIS WEEK", 16, retro.GOLD)
        days = self.summary["days"]
        top = max([r["taken"] + r["skipped"] for _, r in days] + [1])
        chart = QRect(40, 70, self.W - 80, 170)
        retro.draw_box(p, chart, retro.PLUM, retro.INK, shadow=False, px=2)
        slot = (chart.width() - 20) / len(days)
        for i, (day, record) in enumerate(days):
            x = chart.x() + 10 + i * slot
            floor = chart.bottom() - 28
            unit = (floor - chart.y() - 16) / top
            taken_h, skipped_h = record["taken"] * unit, record["skipped"] * unit
            p.fillRect(round(x + 6), round(floor - taken_h), round(slot / 2 - 8), round(taken_h), retro.GREEN)
            p.fillRect(round(x + slot / 2), round(floor - skipped_h), round(slot / 2 - 8), round(skipped_h), retro.RED)
            retro.draw_text(p, QRect(round(x), floor + 6, round(slot), 14), format_day(day), 8, retro.PAPER)
        retro.draw_text(p, QRect(40, 246, 400, 14), "GREEN = TAKEN   RED = SKIPPED", 8, retro.PAPER,
                        retro.LEFT_VCENTER)
        totals = self.summary["totals"]
        share = "NO BREAKS YET" if totals["taken_share"] is None else f"{round(totals['taken_share'] * 100)}% TAKEN"
        rows = [
            ("BREAKS TAKEN", f"{totals['taken']} OF {totals['taken'] + totals['skipped']}  ({share})"),
            ("SNOOZES", str(totals["snoozed"])),
            ("MICRO-BREAKS DONE", str(totals["micro_done"])),
            ("FOCUS TIME", f"{totals['focus_seconds'] // 3600}H {(totals['focus_seconds'] // 60) % 60}M"),
            ("STREAK", f"{self.summary['streak']} DAYS  (BEST {self.summary['best']})"),
            ("WARDROBE", f"{self.unlocked_count} OF {len(config.ACCESSORIES)} UNLOCKED"),
        ]
        for i, (label, value) in enumerate(rows):
            y = 272 + i * 16
            retro.draw_text(p, QRect(40, y, 200, 14), label, 8, retro.GOLD, retro.LEFT_VCENTER)
            retro.draw_text(p, QRect(250, y, 260, 14), value, 8, retro.PAPER, retro.LEFT_VCENTER)

    @staticmethod
    def show_summary(summary, on_delete=None, unlocked_count=0):
        dialog = StatsWindow(summary, on_delete, unlocked_count)
        dialog.exec()
        return dialog.deleted


class WardrobeDialog(QDialog):
    """Pick an accessory. Locked ones show the streak they need."""
    CARD_W, CARD_H, GAP = 118, 130, 12

    def __init__(self, avatar, current, best_streak):
        super().__init__()
        self.setWindowTitle("My-Woofie: wardrobe")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.avatar = avatar
        self.best = best_streak
        self.names = [None] + list(config.ACCESSORIES)
        self.index = self.names.index(current) if current in self.names else 0
        self.selected_name = self.names[self.index]
        self._icons = {n: wardrobe.icon(n, 3) for n in config.ACCESSORIES}
        self._previews = {}
        cols = 4
        rows = (len(self.names) + cols - 1) // cols
        self.cols = cols
        self.setFixedSize(cols * (self.CARD_W + self.GAP) + self.GAP, 190 + rows * (self.CARD_H + self.GAP) + 60)

    def _unlocked(self, name):
        return name is None or self.best >= config.ACCESSORIES[name]

    def _preview(self, name):
        if name not in self._previews:
            self._previews[name] = load_frames(self.avatar, config.SPRITE_SIZE, name)["idle"][0]
        return self._previews[name]

    def _card(self, i):
        col, row = i % self.cols, i // self.cols
        return QRect(self.GAP + col * (self.CARD_W + self.GAP), 190 + row * (self.CARD_H + self.GAP),
                     self.CARD_W, self.CARD_H)

    def _start_rect(self):
        return QRect((self.width() - 160) // 2, self.height() - 52, 160, 38)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), retro.NAVY)
        retro.draw_text(p, QRect(0, 12, self.width(), 26), "WARDROBE", 16, retro.GOLD)
        retro.draw_text(p, QRect(0, 40, self.width(), 14), f"BEST STREAK: {self.best} DAYS", 8, retro.PAPER)
        preview = self._preview(self.selected_name).scaled(
            config.SPRITE_SIZE[0] * 3, config.SPRITE_SIZE[1] * 3, Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation)
        p.drawPixmap((self.width() - preview.width()) // 2, 56, preview)
        for i, name in enumerate(self.names):
            rect = self._card(i)
            box = rect.adjusted(0, 0, -4, -4)
            unlocked = self._unlocked(name)
            border = retro.GOLD if i == self.index else retro.INK
            retro.draw_box(p, box, retro.PAPER if unlocked else retro.TRACK, border)
            label = "NONE" if name is None else wardrobe.TITLES[name]
            if name is not None:
                icon = self._icons[name]
                p.drawPixmap(rect.x() + (box.width() - icon.width()) // 2, rect.y() + 22, icon)
            retro.draw_text(p, QRect(rect.x(), rect.y() + 66, box.width(), 14), label, 8,
                            retro.INK if unlocked else retro.PAPER)
            if not unlocked:
                retro.draw_text(p, QRect(rect.x(), rect.y() + 90, box.width(), 14),
                                f"DAY {config.ACCESSORIES[name]} STREAK", 8, retro.GOLD)
            elif i == self.index:
                retro.draw_text(p, QRect(rect.x(), rect.y() + 90, box.width(), 14), "SELECTED", 8, retro.INK)
        start = self._start_rect()
        retro.draw_box(p, start.adjusted(0, 0, -4, -4), retro.GOLD, retro.INK)
        retro.draw_text(p, start.adjusted(0, 0, -4, -4), "DONE", 12, retro.INK)

    def mousePressEvent(self, event):
        point = event.position().toPoint()
        for i, name in enumerate(self.names):
            if self._card(i).contains(point) and self._unlocked(name):
                self.index = i
                self.selected_name = name
                self.update()
                return
        if self._start_rect().contains(point):
            self.accept()

    @staticmethod
    def choose(avatar, current, best_streak):
        """Returns (accessory name or None) when confirmed, or the sentinel False if dismissed."""
        dialog = WardrobeDialog(avatar, current, best_streak)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selected_name
        return False
