"""Reusable KPI card widget for the dashboard."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from mechpulse.ui.theme import COLORS

class KPICard(QFrame):
    """A widget displaying a Key Performance Indicator with a value and unit.

    Displays a title, a large value, an optional unit, and an optional badge.
    """

    def __init__(self, title: str, default_value: str = "-", unit: str = "", badge_text: str = "", parent=None):
        """Initializes the KPICard.

        Args:
            title: The title of the KPI.
            default_value: The initial value to display.
            unit: The unit of measurement.
            badge_text: Initial text for the badge.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setStyleSheet(f"""
            #kpiCard {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header layout for title and badge
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.badge_label = QLabel(badge_text)
        self.badge_label.setStyleSheet(f"background-color: {COLORS['border']}; color: {COLORS['text_primary']}; padding: 2px 6px; border-radius: 4px; font-size: 11px;")
        self.badge_label.setVisible(bool(badge_text))
        header_layout.addWidget(self.badge_label)

        layout.addLayout(header_layout)

        # Value layout
        value_layout = QHBoxLayout()
        self.value_label = QLabel(default_value)
        self.value_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; font-size: 28px;")
        value_layout.addWidget(self.value_label)

        if unit:
            self.unit_label = QLabel(unit)
            self.unit_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; margin-top: 10px;")
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
            value_layout.addWidget(self.unit_label)
            
        value_layout.addStretch()
        layout.addLayout(value_layout)
        layout.addStretch()

    def set_value(self, val: str) -> None:
        """Updates the displayed value.

        Args:
            val: The new value string to display.
        """
        self.value_label.setText(val)

    def set_badge(self, text: str, color: str = "") -> None:
        """Updates the badge text and optional color.

        Args:
            text: The text to show in the badge.
            color: The background color for the badge.
        """
        if text:
            self.badge_label.setText(text)
            self.badge_label.setVisible(True)
            if color:
                self.badge_label.setStyleSheet(f"background-color: {color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;")
        else:
            self.badge_label.setVisible(False)
