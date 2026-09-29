"""Unit tests for vibration digital twin signal simulator."""

from __future__ import annotations

import numpy as np
import pytest

from mechpulse.core.simulator import VibrationSimulator


def test_normal_signal_low_rms() -> None:
    """Verify that Normal operating mode produces low RMS vibration velocity (< 2.0 mm/s)."""
    sim = VibrationSimulator()
    samples: np.ndarray = sim.generate_signal(fault_mode=0)

    assert isinstance(samples, np.ndarray)
    assert len(samples) == 256

    # RMS velocity scaled per simulator calculation
    rms_velocity = float(np.sqrt(np.mean(np.square(samples))) * 1.5)
    assert rms_velocity < 2.0


def test_unbalance_signal_high_rms() -> None:
    """Verify that Unbalance fault mode produces high RMS vibration velocity (> 2.5 mm/s)."""
    sim = VibrationSimulator()
    samples: np.ndarray = sim.generate_signal(fault_mode=1)

    assert isinstance(samples, np.ndarray)
    assert len(samples) == 256

    # RMS velocity scaled per simulator calculation
    rms_velocity = float(np.sqrt(np.mean(np.square(samples))) * 1.5)
    assert rms_velocity > 2.5
