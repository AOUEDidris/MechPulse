"""Time-domain waveform plot widget."""

import pyqtgraph as pg
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from mechpulse.ui.theme import COLORS

class WaveformPlot(QWidget):
    """Widget displaying a time-domain vibration waveform."""

    def __init__(self, parent=None):
        """Initializes the WaveformPlot.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget(title="Time-Domain Waveform")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Acceleration', units='g')
        self.plot_widget.setLabel('bottom', 'Time', units='ms')
        self.plot_widget.setYRange(-10, 10)
        
        # Configure cyan pen
        self.pen = pg.mkPen(color=COLORS['accent'], width=1.5)
        self.curve = self.plot_widget.plot(pen=self.pen)
        
        layout.addWidget(self.plot_widget)

    def update(self, samples: np.ndarray, sample_rate: int) -> None:
        """Updates the plot with new sample data.

        Args:
            samples: The 1D numpy array of time-domain samples.
            sample_rate: The sampling rate in Hz.
        """
        if len(samples) > 0 and sample_rate > 0:
            # Calculate time vector in ms
            time_vector = np.arange(len(samples)) * 1000.0 / sample_rate
            self.curve.setData(time_vector, samples)
