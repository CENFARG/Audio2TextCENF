"""Animated audio waveform replicating the approved landing prototype (L9/L10).

The owner picked the prototype SVG wave (400x76 viewBox, angular spikes) and
asked for it inside the app: breathing when idle, pulsing while recording,
both in the main tab and in the recording-time popup. Tk cannot stroke a
gradient path, so each segment is colored by interpolating the prototype's
cyan → blue → violet gradient stops (theme tokens, never raw hex).

Structure:
- Pure helpers (``parse_wave_points``, ``wave_segment_color``,
  ``scale_wave_points``) — unit-tested directly, no Tk.
- ``WaveformAnimator`` — the time engine (phase, modes, scheduling) with
  injected scheduler/canceller callables so tests drive time headless.
- ``Waveform(tk.Canvas)`` — thin rendering shell; ``start``/``stop``/
  ``set_amplitude`` delegate to the animator, frames redraw one line per
  segment with ``smooth=False`` (the prototype look is angular).

Author: CENF development team.
License: Apache 2.0.
"""

from __future__ import annotations

import math
import re
import tkinter as tk
from typing import Any, Callable, Optional

from ui.theme import COLORS

# Verbatim path data from the prototype <svg class="wave" viewBox="0 0 400 76">.
WAVE_PATH_D = (
    "M0 38 L8 38 14 27 20 50 27 13 34 62 42 32 49 38 57 38 64 21 71 55 78 29 "
    "86 42 94 38 102 38 109 9 116 65 124 25 132 48 140 38 148 38 156 18 164 58 "
    "172 30 180 44 188 38 196 38 204 14 212 62 220 25 228 49 236 38 244 38 "
    "252 21 260 56 268 29 276 45 284 38 292 38 300 11 308 64 316 25 324 49 "
    "332 38 340 38 348 20 356 57 364 28 372 46 380 38 388 38 400 38"
)
WAVE_VIEWBOX_WIDTH = 400.0
WAVE_MID_Y = 38.0

# Gradient stop offsets from the prototype <linearGradient> (x1=0 → x2=1).
_BLUE_STOP = 0.55

_MODES = ("breathe", "pulse")
_BREATHE_BASE, _BREATHE_WOBBLE, _BREATHE_SPEED = 0.45, 0.2, 0.09
_PULSE_BASE, _PULSE_WOBBLE, _PULSE_SPEED = 1.0, 0.35, 0.22
_TICK_MS = 50  # ~20 fps: smooth enough for a 50-segment redraw

# Ceiling for manual or simulated spike scaling (exaggeration limit).
max_amplitude = 1.6

Number = float
Scheduler = Callable[[int, Callable[[], None]], object]
Canceller = Callable[[Any], None]


def parse_wave_points(d: str) -> list[tuple[Number, Number]]:
    """Parse the prototype SVG path into ``(x, y)`` points.

    Handles ``M``/``L`` commands plus their implicit coordinate pairs: the
    command letters carry no geometry of their own, so every numeric token
    in sequence is a coordinate. Raises ``ValueError`` on a dangling
    coordinate (odd token count).
    """
    tokens = re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", d)
    if len(tokens) % 2 != 0:
        raise ValueError(f"SVG path has an odd coordinate count: {len(tokens)}")
    it = iter(tokens)
    return [(float(x), float(y)) for x, y in zip(it, it)]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def wave_segment_color(fraction: Number) -> str:
    """Interpolate the prototype gradient at ``fraction`` (0.0 left → 1.0 right).

    Piecewise linear: cyan → blue over 0.0..0.55, blue → violet over
    0.55..1.0, clamped outside. Returns lowercase ``#rrggbb`` like CSS.
    """
    fraction = min(1.0, max(0.0, fraction))
    if fraction <= _BLUE_STOP:
        start, stop, t = COLORS["cyan"], COLORS["blue"], fraction / _BLUE_STOP
    else:
        span = 1.0 - _BLUE_STOP
        start, stop, t = (
            COLORS["blue"],
            COLORS["violet"],
            (fraction - _BLUE_STOP) / span,
        )
    r0, g0, b0 = _hex_to_rgb(start)
    r1, g1, b1 = _hex_to_rgb(stop)
    return "#{:02x}{:02x}{:02x}".format(
        round(r0 + (r1 - r0) * t), round(g0 + (g1 - g0) * t), round(b0 + (b1 - b0) * t)
    )


def scale_wave_points(
    points: list[tuple[Number, Number]], amplitude: Number, mid_y: Number
) -> list[tuple[Number, Number]]:
    """Scale spike offsets around ``mid_y`` by ``amplitude`` (0 flattens).

    ``amplitude`` 1.0 reproduces the prototype exactly; up to ~1.6
    exaggerates (see ``max_amplitude``). X coordinates pass through
    untouched so segment count and gradient mapping stay stable.
    """
    return [(x, mid_y + (y - mid_y) * amplitude) for x, y in points]


class WaveformAnimator:
    """Time engine for the wave: modes, phase drift, leak-free scheduling.

    ``scheduler(ms, callback) -> after_id`` and ``canceller(after_id)``
    default to the owning widget's ``after``/``after_cancel`` but are
    injected in tests with fakes, so no Tk window or mainloop is needed.
    Every scheduled id is tracked and cancelled by ``stop()`` — nothing
    leaks when widgets are destroyed mid-animation.
    """

    def __init__(
        self,
        scheduler: Scheduler,
        canceller: Canceller,
        on_frame: Callable[[Number], None],
        interval_ms: int = _TICK_MS,
    ) -> None:
        self._scheduler = scheduler
        self._canceller = canceller
        self._on_frame = on_frame
        self._interval_ms = interval_ms
        self._phase = 0.0
        self._mode: str = "breathe"
        self._running = False
        self._pending: set[object] = set()
        self._manual_amplitude: Optional[Number] = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def mode(self) -> str:
        return self._mode

    def start(self, mode: str = "breathe") -> None:
        """Animate in ``mode``; idempotent — never double-schedules.

        Calling ``start`` again while running only switches the mode
        (recording ticks hit this path every second), keeping exactly one
        pending callback at all times.
        """
        if mode not in _MODES:
            raise ValueError(f"unknown waveform mode: {mode!r} (expected {_MODES})")
        if self._running:
            self._mode = mode
            return
        self._mode = mode
        self._running = True
        self._schedule_tick()

    def stop(self) -> None:
        """Cancel every pending callback; safe to call when not running."""
        for after_id in list(self._pending):
            self._canceller(after_id)
        self._pending.clear()
        self._running = False

    def set_amplitude(self, level: Optional[Number]) -> None:
        """Override the simulated drift with a manual level (0..1.6).

        ``None`` returns to the simulated breathing/pulsing drift. This is
        the hook for real microphone coupling in a future version.
        """
        self._manual_amplitude = None if level is None else self._clamp(level)

    @staticmethod
    def _clamp(level: Number) -> Number:
        return min(max_amplitude, max(0.0, level))

    def _simulated_level(self) -> Number:
        if self._mode == "pulse":
            base, wobble, speed = _PULSE_BASE, _PULSE_WOBBLE, _PULSE_SPEED
        else:
            base, wobble, speed = _BREATHE_BASE, _BREATHE_WOBBLE, _BREATHE_SPEED
        return base + wobble * math.sin(self._phase * speed)

    def _schedule_tick(self) -> None:
        after_id = self._scheduler(self._interval_ms, self.tick)
        self._pending.add(after_id)

    def tick(self) -> None:
        """Advance one frame: emit the level, drift the phase, reschedule."""
        self._pending.clear()  # the fired id is consumed; a new one lands below
        level = (
            self._manual_amplitude
            if self._manual_amplitude is not None
            else self._simulated_level()
        )
        self._phase += 1.0
        self._on_frame(level)
        if self._running:
            self._schedule_tick()


class Waveform(tk.Canvas):
    """Canvas rendering of the prototype wave (one line per segment).

    Colors each segment by its midpoint's position across the viewBox so
    the cyan → blue → violet gradient reads left to right like the SVG.
    ``scheduler``/``canceller`` default to this widget's ``after``/
    ``after_cancel``; ``start()``/``stop()``/``set_amplitude()`` delegate
    to the animator. A ``<Destroy>`` bind cancels the loop, so destroying
    the window (main tab or recording popup) never leaks callbacks.
    """

    def __init__(
        self,
        parent: tk.Misc,
        width: int = 400,
        height: int = 76,
        bg: Optional[str] = None,
        line_width: int = 2,
        scheduler: Optional[Scheduler] = None,
        canceller: Optional[Canceller] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg if bg is not None else COLORS["bg"],
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._points = parse_wave_points(WAVE_PATH_D)
        self._line_width = line_width
        self._render_width = float(width)
        self._animator = WaveformAnimator(
            scheduler=scheduler if scheduler is not None else self.after,
            canceller=canceller if canceller is not None else self.after_cancel,
            on_frame=self._render,
        )
        self.bind("<Destroy>", self._on_destroy)

    def start(self, mode: str = "breathe") -> None:
        """Begin animating (``"breathe"`` idle / ``"pulse"`` recording)."""
        self._animator.start(mode)
        self._render(self._current_level())

    def stop(self) -> None:
        """Cancel every pending animation callback."""
        self._animator.stop()

    def set_amplitude(self, level: Optional[Number]) -> None:
        """Pin the spike scale manually (real-mic coupling hook)."""
        self._animator.set_amplitude(level)

    def _current_level(self) -> Number:
        if self._animator._manual_amplitude is not None:
            return self._animator._manual_amplitude
        return self._animator._simulated_level()

    def _render(self, level: Number) -> None:
        """Redraw all segments at ``level`` (delete + create_line)."""
        self.delete("all")
        mid_y = float(self.winfo_reqheight()) / 2.0
        scaled = scale_wave_points(self._points, level, mid_y)
        x_scale = self._render_width / WAVE_VIEWBOX_WIDTH
        for (x0, y0), (x1, y1) in zip(scaled, scaled[1:]):
            fraction = ((x0 + x1) / 2.0) / WAVE_VIEWBOX_WIDTH
            self.create_line(
                x0 * x_scale,
                y0,
                x1 * x_scale,
                y1,
                fill=wave_segment_color(fraction),
                width=self._line_width,
                smooth=False,
                capstyle="round",
            )

    def _on_destroy(self, _event: object) -> None:
        self._animator.stop()
