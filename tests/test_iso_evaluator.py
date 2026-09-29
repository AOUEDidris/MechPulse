"""Unit tests for ISO 10816-3 vibration severity evaluator."""

from __future__ import annotations

import pytest
from mechpulse.core.iso_evaluator import ISO10816Evaluator, ISOResult


def test_zone_a() -> None:
    """Test vibration evaluation in Zone A (Good / Excellent condition)."""
    result: ISOResult = ISO10816Evaluator.evaluate(0.5)
    assert result.zone == "A"
    assert result.label == "Excellent"


def test_zone_b() -> None:
    """Test vibration evaluation in Zone B (Acceptable long-term operation)."""
    result: ISOResult = ISO10816Evaluator.evaluate(2.0)
    assert result.zone == "B"
    assert result.label == "Acceptable"


def test_zone_c() -> None:
    """Test vibration evaluation in Zone C (Unsuitable for long-term continuous operation)."""
    result: ISOResult = ISO10816Evaluator.evaluate(3.5)
    assert result.zone == "C"
    assert result.label == "Warning"


def test_zone_d() -> None:
    """Test vibration evaluation in Zone D (Critical Danger / machine shutdown required)."""
    result: ISOResult = ISO10816Evaluator.evaluate(6.0)
    assert result.zone == "D"
    assert result.label == "Critical Danger"


def test_boundary_a_b() -> None:
    """Test threshold boundary between Zone A and Zone B (1.4 mm/s should be Zone A)."""
    result: ISOResult = ISO10816Evaluator.evaluate(1.4)
    assert result.zone == "A"


def test_boundary_b_c() -> None:
    """Test threshold boundary between Zone B and Zone C (2.8 mm/s should be Zone B)."""
    result: ISOResult = ISO10816Evaluator.evaluate(2.8)
    assert result.zone == "B"


def test_boundary_c_d() -> None:
    """Test threshold boundary between Zone C and Zone D (4.5 mm/s should be Zone C)."""
    result: ISOResult = ISO10816Evaluator.evaluate(4.5)
    assert result.zone == "C"


def test_zero() -> None:
    """Test zero vibration amplitude evaluation (0.0 mm/s should be Zone A)."""
    result: ISOResult = ISO10816Evaluator.evaluate(0.0)
    assert result.zone == "A"


def test_extreme() -> None:
    """Test extreme catastrophic vibration velocity (100.0 mm/s should be Zone D)."""
    result: ISOResult = ISO10816Evaluator.evaluate(100.0)
    assert result.zone == "D"
