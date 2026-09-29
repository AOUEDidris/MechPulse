"""ISO 10816-3 evaluator module."""

import logging
from dataclasses import dataclass
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class ISOResult:
    """Represents the result of an ISO 10816-3 evaluation.

    Attributes:
        zone: The ISO zone (A, B, C, or D).
        label: A short label for the zone (e.g., 'Excellent', 'Warning').
        color: The hex color code associated with the zone.
        description: A detailed description of the machine's condition.
        recommendation: Recommended actions based on the condition.
    """
    zone: str
    label: str
    color: str
    description: str
    recommendation: str


class ISO10816Evaluator:
    """Evaluates vibration severity according to ISO 10816-3 standard.

    This standard covers rotating machinery. The thresholds used here are for
    Group 2 machines (medium-sized machines, 15kW to 300kW) on rigid foundations.
    """

    ZONE_A: ClassVar[float] = 1.4
    ZONE_B: ClassVar[float] = 2.8
    ZONE_C: ClassVar[float] = 4.5

    @classmethod
    def evaluate(cls, rms_velocity: float) -> ISOResult:
        """Evaluates the RMS velocity against ISO 10816-3 thresholds.

        Args:
            rms_velocity: The measured RMS vibration velocity in mm/s.

        Returns:
            An ISOResult containing the evaluation details.
        """
        if rms_velocity <= cls.ZONE_A:
            return ISOResult(
                zone="A",
                label="Excellent",
                color="#2ecc71",
                description="Vibration is typical for newly commissioned machinery.",
                recommendation="Continue normal operation. No action required."
            )
        elif rms_velocity <= cls.ZONE_B:
            return ISOResult(
                zone="B",
                label="Acceptable",
                color="#00b894",
                description="Vibration is acceptable for unrestricted long-term operation.",
                recommendation="Continue normal operation. Routine monitoring."
            )
        elif rms_velocity <= cls.ZONE_C:
            return ISOResult(
                zone="C",
                label="Warning",
                color="#f39c12",
                description="Vibration is unsuitable for long-term continuous operation.",
                recommendation="Plan maintenance action. Investigate root cause during next scheduled downtime."
            )
        else:
            return ISOResult(
                zone="D",
                label="Critical Danger",
                color="#e74c3c",
                description="Vibration is sufficient to cause damage to the machine.",
                recommendation="CRITICAL: Stop machine immediately to prevent severe damage."
            )
