"""Unit tests for the v0.18.0 animated audio waveform (S3 amendment, L9/L10).

The owner approved the landing prototype's SVG wave and asked for it inside
the app: breathing when idle, pulsing while recording, both in the main tab
and in the recording-time popup.

Coverage follows the mission's headless contract:
- pure geometry/color helpers tested directly (no Tk),
- the animation engine tested with an injected fake scheduler/canceller
  (no Tk window, no mainloop),
- the tk.Canvas shell tested against a real withdrawn Tk root when a
  display is available (skipped headless, mirroring the repo convention
  that widget rendering is not unit-tested headless).

Gradient stops come from ui.theme tokens — never raw hex in ui/.
"""

import re
import sys
from pathlib import Path
from typing import Callable, cast

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.theme import COLORS
from ui.waveform import (
    WAVE_VIEWBOX_WIDTH,
    WaveformAnimator,
    max_amplitude,
    parse_wave_points,
    scale_wave_points,
    wave_segment_color,
)

WAVE_PATH = (
    "M0 38 L8 38 14 27 20 50 27 13 34 62 42 32 49 38 57 38 64 21 71 55 78 29 "
    "86 42 94 38 102 38 109 9 116 65 124 25 132 48 140 38 148 38 156 18 164 58 "
    "172 30 180 44 188 38 196 38 204 14 212 62 220 25 228 49 236 38 244 38 252 21 "
    "260 56 268 29 276 45 284 38 292 38 300 11 308 64 316 25 324 49 332 38 340 38 "
    "348 20 356 57 364 28 372 46 380 38 388 38 400 38"
)


class FakeScheduler:
    """Deterministic after()/after_cancel() double for headless time control."""

    def __init__(self):
        self.pending: dict[int, tuple[int, object]] = {}
        self.cancelled: list[int] = []
        self._next_id: int = 0

    def schedule(self, ms: int, callback: object) -> int:
        self._next_id += 1
        self.pending[self._next_id] = (ms, callback)
        return self._next_id

    def cancel(self, after_id: int) -> None:
        self.cancelled.append(after_id)
        self.pending.pop(after_id, None)

    def run_next(self) -> None:
        """Fire the oldest pending callback (advancing fake time one tick)."""
        assert self.pending, "run_next() called with no pending callback"
        after_id = min(self.pending)
        callback = self.pending.pop(after_id)[1]
        cast(Callable[[], None], callback)()

    @property
    def issued(self) -> list[int]:
        return sorted(self.pending) + sorted(self.cancelled)


def _animator(frames: list[float], scheduler: FakeScheduler) -> WaveformAnimator:
    return WaveformAnimator(
        scheduler=scheduler.schedule,
        canceller=scheduler.cancel,
        on_frame=frames.append,
    )


# ── parse_wave_points ────────────────────────────────────────────────


class TestParseWavePoints:
    def test_yields_all_points_starting_and_ending_on_midline(self):
        # The verbatim prototype path: M point + 51 L-pairs = 52 points,
        # i.e. 51 segments (the mission's "51 points" counts segments).
        points = parse_wave_points(WAVE_PATH)
        assert len(points) == 52
        assert len(points) - 1 == 51  # segments
        assert points[0] == (0.0, 38.0)
        assert points[-1] == (400.0, 38.0)

    def test_x_coordinates_strictly_increase(self):
        xs = [x for x, _ in parse_wave_points(WAVE_PATH)]
        assert all(b > a for a, b in zip(xs, xs[1:]))

    def test_odd_token_count_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_wave_points("M0 38 L8 38 14")


# ── wave_segment_color ───────────────────────────────────────────────


def _channels(color: str) -> list[int]:
    return [int(color[i : i + 2], 16) for i in range(1, 7, 2)]


class TestWaveSegmentColor:
    def test_endpoints_match_theme_tokens_exactly(self):
        assert wave_segment_color(0.0) == COLORS["cyan"].lower()
        assert wave_segment_color(0.55) == COLORS["blue"].lower()
        assert wave_segment_color(1.0) == COLORS["violet"].lower()

    def test_returns_lowercase_hex_everywhere(self):
        for fraction in (0.0, 0.2, 0.55, 0.8, 1.0):
            assert re.fullmatch(r"#[0-9a-f]{6}", wave_segment_color(fraction))

    def test_first_ramp_blends_between_cyan_and_blue(self):
        lo, hi = _channels(COLORS["cyan"]), _channels(COLORS["blue"])
        mid = _channels(wave_segment_color(0.275))
        assert all(a < m < b or a > m > b for a, m, b in zip(lo, mid, hi))

    def test_second_ramp_blends_between_blue_and_violet(self):
        lo, hi = _channels(COLORS["blue"]), _channels(COLORS["violet"])
        mid = _channels(wave_segment_color(0.775))
        assert all(min(a, b) <= m <= max(a, b) for a, m, b in zip(lo, mid, hi))

    def test_fraction_clamped_out_of_range(self):
        assert wave_segment_color(-0.5) == COLORS["cyan"].lower()
        assert wave_segment_color(1.5) == COLORS["violet"].lower()


# ── scale_wave_points ────────────────────────────────────────────────


class TestScaleWavePoints:
    def test_zero_amplitude_flattens_to_midline(self):
        scaled = scale_wave_points(parse_wave_points(WAVE_PATH), 0.0, mid_y=38.0)
        assert all(y == 38.0 for _, y in scaled)
        assert [x for x, _ in scaled] == [x for x, _ in parse_wave_points(WAVE_PATH)]

    def test_offsets_scale_around_midline_and_x_is_untouched(self):
        scaled = scale_wave_points(parse_wave_points(WAVE_PATH), 2.0, mid_y=38.0)
        original = parse_wave_points(WAVE_PATH)
        assert scaled[2] == (14.0, 38.0 + (27.0 - 38.0) * 2.0)  # spike up
        assert scaled[3] == (20.0, 38.0 + (50.0 - 38.0) * 2.0)  # spike down
        assert [x for x, _ in scaled] == [x for x, _ in original]

    def test_midline_points_never_move(self):
        scaled = scale_wave_points(parse_wave_points(WAVE_PATH), 1.6, mid_y=38.0)
        original = parse_wave_points(WAVE_PATH)
        for (_, y0), (_, y1) in zip(original, scaled):
            if y0 == 38.0:
                assert y1 == 38.0


def test_max_amplitude_constant_is_the_clamp_ceiling():
    assert max_amplitude == 1.6


# ── WaveformAnimator (injected time, no Tk) ──────────────────────────


class TestWaveformAnimatorLifecycle:
    def test_start_schedules_exactly_one_callback(self):
        scheduler = FakeScheduler()
        animator = _animator([], scheduler)
        animator.start()
        assert len(scheduler.pending) == 1
        assert animator.running

    def test_start_twice_does_not_double_schedule(self):
        scheduler = FakeScheduler()
        animator = _animator([], scheduler)
        animator.start()
        animator.start()
        assert len(scheduler.pending) == 1

    def test_mode_switch_while_running_keeps_single_loop(self):
        scheduler = FakeScheduler()
        animator = _animator([], scheduler)
        animator.start("breathe")
        animator.start("pulse")
        assert len(scheduler.pending) == 1
        assert animator.mode == "pulse"

    def test_unknown_mode_raises_value_error(self):
        animator = _animator([], FakeScheduler())
        with pytest.raises(ValueError):
            animator.start("wiggle")

    def test_stop_cancels_every_scheduled_id(self):
        scheduler = FakeScheduler()
        frames: list[float] = []
        animator = _animator(frames, scheduler)
        animator.start()
        for _ in range(5):
            scheduler.run_next()  # each tick reschedules: ids keep accumulating
        scheduled_ids = set(scheduler.issued)
        animator.stop()
        assert set(scheduler.cancelled) == scheduled_ids
        assert scheduler.pending == {}
        assert not animator.running

    def test_stop_without_start_is_a_noop(self):
        scheduler = FakeScheduler()
        animator = _animator([], scheduler)
        animator.stop()
        assert scheduler.cancelled == []

    def test_tick_reschedules_while_running(self):
        scheduler = FakeScheduler()
        animator = _animator([], scheduler)
        animator.start()
        scheduler.run_next()
        assert len(scheduler.pending) == 1


class TestWaveformAnimatorFrames:
    def test_tick_drives_on_frame_with_clamped_levels(self):
        scheduler = FakeScheduler()
        frames: list[float] = []
        animator = _animator(frames, scheduler)
        animator.start("pulse")
        for _ in range(40):
            scheduler.run_next()
        assert len(frames) == 40
        assert all(0.0 <= level <= max_amplitude for level in frames)
        assert len(set(frames)) > 1  # the wave actually animates

    def test_set_amplitude_overrides_simulation(self):
        scheduler = FakeScheduler()
        frames: list[float] = []
        animator = _animator(frames, scheduler)
        animator.start()
        animator.set_amplitude(0.0)
        scheduler.run_next()
        assert frames[-1] == 0.0  # flattened: future real-mic coupling point

    def test_set_amplitude_clamps_to_ceiling(self):
        scheduler = FakeScheduler()
        frames: list[float] = []
        animator = _animator(frames, scheduler)
        animator.start()
        animator.set_amplitude(9.0)
        scheduler.run_next()
        assert frames[-1] == max_amplitude

    def test_clearing_amplitude_returns_to_simulated_drift(self):
        scheduler = FakeScheduler()
        frames: list[float] = []
        animator = _animator(frames, scheduler)
        animator.start()
        animator.set_amplitude(0.0)
        scheduler.run_next()
        animator.set_amplitude(None)
        scheduler.run_next()
        assert frames[-1] > 0.0  # breathing simulation resumed


# ── Waveform canvas shell (real Tk when a display exists) ────────────


def _tk_root():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        return root
    except Exception:  # pragma: no cover - headless CI
        return None


@pytest.fixture
def tk_root():
    root = _tk_root()
    if root is None:
        pytest.skip("tkinter display unavailable (headless CI)")
    yield root
    root.destroy()


class TestWaveformCanvas:
    def test_start_renders_one_line_per_segment(self, tk_root):
        from ui.waveform import Waveform

        scheduler = FakeScheduler()
        wave = Waveform(
            tk_root, height=64, scheduler=scheduler.schedule, canceller=scheduler.cancel
        )
        wave.start("pulse")
        scheduler.run_next()
        assert len(wave.find_all()) == len(parse_wave_points(WAVE_PATH)) - 1
        wave.stop()

    def test_destroy_cancels_pending_callbacks(self, tk_root):
        from ui.waveform import Waveform

        scheduler = FakeScheduler()
        wave = Waveform(
            tk_root, height=64, scheduler=scheduler.schedule, canceller=scheduler.cancel
        )
        wave.start()
        wave.destroy()
        assert scheduler.pending == {}
        assert set(scheduler.cancelled) == set(scheduler.issued)

    def test_set_amplitude_delegates_and_clamps(self, tk_root):
        from ui.waveform import Waveform

        scheduler = FakeScheduler()
        frames: list[float] = []
        wave = Waveform(
            tk_root, height=64, scheduler=scheduler.schedule, canceller=scheduler.cancel
        )
        wave._animator._on_frame = frames.append
        wave.set_amplitude(42.0)
        wave.start()
        scheduler.run_next()
        assert frames[-1] == max_amplitude
        wave.stop()


def test_viewbox_constant_matches_prototype():
    assert WAVE_VIEWBOX_WIDTH == 400.0
