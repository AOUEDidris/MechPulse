"""Unit tests for binary UDP vibration telemetry packet format and roundtrip serialization."""

from __future__ import annotations

import struct
from typing import Any, Dict
import numpy as np
import pytest

from mechpulse.core.receiver import UDPReceiverThread


EXPECTED_PACKET_SIZE = 1572
PACKET_FORMAT = "<d 4f 2I i 256f 128f"


def test_packet_size() -> None:
    """Verify that binary packet size calculation strictly matches 1572 bytes."""
    calculated_size = struct.calcsize(PACKET_FORMAT)
    assert calculated_size == EXPECTED_PACKET_SIZE
    assert UDPReceiverThread.PACKET_SIZE == EXPECTED_PACKET_SIZE


def test_pack_unpack_roundtrip() -> None:
    """Test packing sample vibration telemetry data, unpacking, and verifying field values."""
    timestamp: float = 1727600000.125
    rms_velocity: float = 2.35
    peak_accel: float = 5.82
    crest_factor: float = 2.47
    kurtosis: float = 3.12
    sample_rate: int = 1000
    sample_count: int = 256
    fault_mode: int = 2

    # Synthetic waveform and FFT spectrum values
    raw_samples: list[float] = [float(np.sin(2.0 * np.pi * 25.0 * i / 1000.0)) for i in range(256)]
    raw_spectrum: list[float] = [float(0.5 / (1.0 + i)) for i in range(128)]

    # Pack into binary payload
    payload: bytes = struct.pack(
        PACKET_FORMAT,
        timestamp,
        rms_velocity,
        peak_accel,
        crest_factor,
        kurtosis,
        sample_rate,
        sample_count,
        fault_mode,
        *raw_samples,
        *raw_spectrum,
    )

    assert len(payload) == EXPECTED_PACKET_SIZE

    # Unpack using struct directly
    unpacked = struct.unpack(PACKET_FORMAT, payload)
    assert unpacked[0] == pytest.approx(timestamp, rel=1e-6)
    assert unpacked[1] == pytest.approx(rms_velocity, rel=1e-5)
    assert unpacked[2] == pytest.approx(peak_accel, rel=1e-5)
    assert unpacked[3] == pytest.approx(crest_factor, rel=1e-5)
    assert unpacked[4] == pytest.approx(kurtosis, rel=1e-5)
    assert unpacked[5] == sample_rate
    assert unpacked[6] == sample_count
    assert unpacked[7] == fault_mode

    unpacked_samples = unpacked[8:8 + 256]
    unpacked_spectrum = unpacked[8 + 256:]

    for orig, unp in zip(raw_samples, unpacked_samples):
        assert orig == pytest.approx(unp, abs=1e-5)

    for orig, unp in zip(raw_spectrum, unpacked_spectrum):
        assert orig == pytest.approx(unp, abs=1e-5)

    # Validate parsing through receiver helper parser
    receiver = UDPReceiverThread()
    parsed: Dict[str, Any] | None = receiver._parse_packet(payload)

    assert parsed is not None
    assert parsed["timestamp"] == pytest.approx(timestamp, rel=1e-6)
    assert parsed["rms_velocity"] == pytest.approx(rms_velocity, rel=1e-5)
    assert parsed["peak_accel"] == pytest.approx(peak_accel, rel=1e-5)
    assert parsed["crest_factor"] == pytest.approx(crest_factor, rel=1e-5)
    assert parsed["kurtosis"] == pytest.approx(kurtosis, rel=1e-5)
    assert parsed["sample_rate"] == sample_rate
    assert parsed["sample_count"] == sample_count
    assert parsed["fault_mode"] == fault_mode
    assert len(parsed["samples"]) == 256
    assert len(parsed["fft_spectrum"]) == 128
    np.testing.assert_allclose(parsed["samples"], raw_samples, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(parsed["fft_spectrum"], raw_spectrum, rtol=1e-4, atol=1e-4)
