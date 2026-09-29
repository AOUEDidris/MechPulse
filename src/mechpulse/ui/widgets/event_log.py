"""Event log widget."""

import time
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QColor, QBrush
from mechpulse.ui.theme import COLORS

class EventLog(QTableWidget):
    """Table widget to display a log of vibration events and diagnoses."""

    def __init__(self, parent=None):
        """Initializes the EventLog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Time", "ISO Zone", "RMS (mm/s)", "Diagnosis"])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)

        self._last_event_time = 0.0

    def add_event(self, time_str: str, zone: str, rms: str, diagnosis: str, color_hex: str) -> None:
        """Adds a new event to the log. Implements rate limiting (1 event / 2s).

        Args:
            time_str: Formatted time string.
            zone: ISO zone identifier.
            rms: Formatted RMS velocity value.
            diagnosis: Text describing the diagnosis.
            color_hex: Hex color code for the row text.
        """
        current_time = time.time()
        if current_time - self._last_event_time < 2.0:
            return  # Rate limiting
        
        self._last_event_time = current_time

        row = self.rowCount()
        self.insertRow(row)

        items = [
            QTableWidgetItem(time_str),
            QTableWidgetItem(f"Zone {zone}"),
            QTableWidgetItem(rms),
            QTableWidgetItem(diagnosis)
        ]

        text_color = QColor(color_hex)
        for col, item in enumerate(items):
            item.setForeground(QBrush(text_color))
            self.setItem(row, col, item)

        self.scrollToBottom()
