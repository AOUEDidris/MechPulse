"""Main dashboard window for MechPulse."""

import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSplitter, QGroupBox, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

from mechpulse.core.receiver import UDPReceiverThread
from mechpulse.core.iso_evaluator import ISO10816Evaluator
from mechpulse.ui.theme import COLORS, get_zone_style
from mechpulse.ui.widgets.kpi_card import KPICard
from mechpulse.ui.widgets.waveform_plot import WaveformPlot
from mechpulse.ui.widgets.spectrum_plot import SpectrumPlot
from mechpulse.ui.widgets.event_log import EventLog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application dashboard for MechPulse."""

    # Fault mapping: 0=Normal, 1=Unbalance, 2=Misalignment, 3=BearingFault
    FAULT_MAPPING = {
        0: {"label": "Normal (طبيعي)", "color": COLORS["success"], "rec": "Continue normal operation."},
        1: {"label": "Unbalance (عدم اتزان)", "color": COLORS["warning"], "rec": "Check rotor balance and clean impellers."},
        2: {"label": "Misalignment (عدم محاذاة)", "color": "#d35400", "rec": "Perform laser alignment on coupling."},
        3: {"label": "Bearing Fault (عطل في المحمل)", "color": COLORS["danger"], "rec": "Schedule bearing replacement immediately."}
    }

    def __init__(self):
        """Initializes the main window and its UI components."""
        super().__init__()
        self.setWindowTitle("MechPulse — Real-Time Vibration Monitoring & Predictive Maintenance")
        self.resize(1300, 850)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Header
        header_layout = QHBoxLayout()
        title_label = QLabel("MechPulse Dashboard")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.conn_indicator = QLabel("● Disconnected")
        self.conn_indicator.setStyleSheet(f"color: {COLORS['danger']}; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.conn_indicator)
        main_layout.addLayout(header_layout)

        # 2. KPI Cards Row
        kpi_layout = QHBoxLayout()
        self.kpi_rms = KPICard("RMS Velocity", "0.00", "mm/s", "ISO 10816-3")
        self.kpi_peak = KPICard("Peak Accel", "0.00", "g")
        self.kpi_crest = KPICard("Crest Factor", "0.00")
        self.kpi_kurtosis = KPICard("Kurtosis", "0.00")
        
        kpi_layout.addWidget(self.kpi_rms)
        kpi_layout.addWidget(self.kpi_peak)
        kpi_layout.addWidget(self.kpi_crest)
        kpi_layout.addWidget(self.kpi_kurtosis)
        main_layout.addLayout(kpi_layout)

        # 3. Splitter for Plots
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.waveform_plot = WaveformPlot()
        self.spectrum_plot = SpectrumPlot()
        splitter.addWidget(self.waveform_plot)
        splitter.addWidget(self.spectrum_plot)
        main_layout.addWidget(splitter, stretch=2)

        # 4. Bottom Panel (Diagnostics + Event Log)
        bottom_layout = QHBoxLayout()
        
        # Diagnostics Group
        diag_group = QGroupBox("Diagnostics & AI Recommendations")
        diag_layout = QVBoxLayout(diag_group)
        self.diag_label = QLabel("Waiting for data...")
        self.diag_label.setWordWrap(True)
        self.diag_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.rec_label = QLabel("-")
        self.rec_label.setWordWrap(True)
        self.rec_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.export_btn = QPushButton("Export CSV Report")
        self.export_btn.clicked.connect(self.export_csv_report)
        
        diag_layout.addWidget(self.diag_label)
        diag_layout.addWidget(self.rec_label)
        diag_layout.addStretch()
        diag_layout.addWidget(self.export_btn)
        
        # Event Log
        self.event_log = EventLog()
        
        bottom_layout.addWidget(diag_group, stretch=1)
        bottom_layout.addWidget(self.event_log, stretch=2)
        main_layout.addLayout(bottom_layout, stretch=1)

        # Setup Receiver Thread
        self.receiver = UDPReceiverThread()
        self.receiver.connection_status.connect(self._update_connection_status)
        self.receiver.packet_received.connect(self.on_packet_received)
        self.receiver.start()

        self._last_csv_data = []

    def _update_connection_status(self, is_connected: bool) -> None:
        """Updates the header connection indicator.

        Args:
            is_connected: Boolean flag indicating active data reception.
        """
        if is_connected:
            self.conn_indicator.setText("● Connected")
            self.conn_indicator.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        else:
            self.conn_indicator.setText("● Disconnected")
            self.conn_indicator.setStyleSheet(f"color: {COLORS['danger']}; font-weight: bold;")

    def on_packet_received(self, data: dict) -> None:
        """Handles incoming parsed UDP packet data.

        Args:
            data: Dictionary of parsed packet data.
        """
        # Extract variables
        rms = data["rms_velocity"]
        peak = data["peak_accel"]
        crest = data["crest_factor"]
        kurt = data["kurtosis"]
        fault_mode = data["fault_mode"]
        samples = data["samples"]
        spectrum = data["fft_spectrum"]
        fs = data["sample_rate"]

        # Evaluate ISO 10816-3
        iso_result = ISO10816Evaluator.evaluate(rms)

        # Update KPIs
        self.kpi_rms.set_value(f"{rms:.2f}")
        self.kpi_rms.set_badge(f"Zone {iso_result.zone}", iso_result.color)
        self.kpi_peak.set_value(f"{peak:.2f}")
        self.kpi_crest.set_value(f"{crest:.2f}")
        self.kpi_kurtosis.set_value(f"{kurt:.2f}")

        # Update Plots
        self.waveform_plot.update(samples, fs)
        self.spectrum_plot.update(spectrum, fs)

        # Diagnostics mapping
        fault_info = self.FAULT_MAPPING.get(fault_mode, self.FAULT_MAPPING[0])
        
        # Update Diagnostic Panel
        diag_text = f"Condition: {fault_info['label']}"
        self.diag_label.setText(diag_text)
        self.diag_label.setStyleSheet(f"color: {fault_info['color']}; font-size: 16px; font-weight: bold;")
        self.rec_label.setText(f"Recommendation: {fault_info['rec']}\nISO Notice: {iso_result.recommendation}")

        # Event Log update
        time_str = datetime.now().strftime("%H:%M:%S")
        self.event_log.add_event(
            time_str=time_str,
            zone=iso_result.zone,
            rms=f"{rms:.2f}",
            diagnosis=fault_info["label"],
            color_hex=fault_info["color"]
        )

        # Store latest data for CSV export
        self._last_csv_data = [time_str, iso_result.zone, f"{rms:.2f}", f"{peak:.2f}", f"{crest:.2f}", f"{kurt:.2f}", fault_info["label"]]

    def export_csv_report(self) -> None:
        """Exports the latest snapshot data to a CSV file."""
        if not self._last_csv_data:
            QMessageBox.warning(self, "Export Error", "No data available to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Time,ISO Zone,RMS Velocity,Peak Accel,Crest Factor,Kurtosis,Diagnosis\n")
                    f.write(",".join(self._last_csv_data) + "\n")
                QMessageBox.information(self, "Export Successful", f"Report saved to {filename}")
            except Exception as e:
                logger.error(f"Failed to export CSV: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to save file: {e}")

    def closeEvent(self, event) -> None:
        """Handles application shutdown cleanly."""
        self.receiver.stop()
        super().closeEvent(event)
