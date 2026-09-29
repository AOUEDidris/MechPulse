"""FFT spectrum plot widget."""

import pyqtgraph as pg
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from mechpulse.ui.theme import COLORS

class SpectrumPlot(QWidget):
    """Widget displaying the frequency-domain FFT spectrum."""

    def __init__(self, parent=None):
        """Initializes the SpectrumPlot.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget(title="FFT Spectrum")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_widget.setXRange(0, 300)
        self.plot_widget.setYRange(0, 6)

        # Yellow/orange pen with fill brush
        self.pen = pg.mkPen(color=COLORS['warning'], width=1.5)
        self.brush = pg.mkBrush(color=COLORS['warning'] + '40') # Add transparency
        self.curve = self.plot_widget.plot(pen=self.pen, fillLevel=0, brush=self.brush)

        # InfiniteLines for key frequencies
        self._add_marker(25, "1X (25Hz)", COLORS['danger'])
        self._add_marker(50, "2X (50Hz)", COLORS['info'])
        self._add_marker(120, "BPFO (120Hz)", "#9b59b6") # Purple

        layout.addWidget(self.plot_widget)

    def _add_marker(self, freq: float, label: str, color: str) -> None:
        """Helper to add an infinite line marker to the plot.

        Args:
            freq: The frequency to mark.
            label: Text label for the marker.
            color: Color of the dashed line.
        """
        pen = pg.mkPen(color=color, style=pg.QtCore.Qt.PenStyle.DashLine)
        line = pg.InfiniteLine(pos=freq, angle=90, pen=pen, label=label, labelOpts={'position':0.9, 'color': color})
        self.plot_widget.addItem(line)

    def update(self, spectrum: np.ndarray, sample_rate: int) -> None:
        """Updates the plot with new spectrum data.

        Args:
            spectrum: The 1D numpy array of FFT magnitude bins.
            sample_rate: The sampling rate in Hz.
        """
        if len(spectrum) > 0 and sample_rate > 0:
            # Nyquist frequency is sample_rate / 2.
            # Bins are evenly spaced up to Nyquist.
            freq_vector = np.linspace(0, sample_rate / 2, len(spectrum))
            self.curve.setData(freq_vector, spectrum)
