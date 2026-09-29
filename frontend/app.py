"""
============================================================================
 MechPulse — Industrial Vibration Monitoring Dashboard
 Real-Time PySide6 + PyQtGraph Frontend with ISO 10816-3 Evaluation
============================================================================

 This application receives binary UDP packets from the C++ backend engine
 (or its built-in Python Digital Twin simulator), displays live waveform &
 FFT spectrum plots, evaluates machine health per ISO 10816-3, and provides
 automated fault diagnosis for maintenance engineers.

 Usage:
   python app.py              # Listen for C++ engine packets
   python app.py --simulate   # Run with built-in simulator (no C++ needed)

 Author:  MechPulse Team
 License: MIT
============================================================================
"""

import sys
import os
import csv
import time
import math
import struct
import socket
import logging
import argparse
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# ============================================================================
#  SECTION 1: Configuration & Constants
# ============================================================================

APP_NAME = "MechPulse"
APP_VERSION = "1.0.0"
APP_TITLE = f"MechPulse v{APP_VERSION} — Real-Time Vibration Monitoring & Predictive Maintenance"
WINDOW_SIZE = (1300, 850)

UDP_HOST = "127.0.0.1"
UDP_PORT = 9876
SAMPLE_RATE = 1000       # Hz
BLOCK_SIZE = 256         # samples per packet
RUNNING_SPEED_HZ = 25.0  # 1500 RPM

# Binary packet format matching C++ struct (1572 bytes total)
PACKET_FORMAT = "<d 4f 2I i 256f 128f"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
assert PACKET_SIZE == 1572, f"Packet size mismatch: {PACKET_SIZE} != 1572"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MechPulse")

# PyQtGraph dark theme
pg.setConfigOption("background", "#131620")
pg.setConfigOption("foreground", "#94a3b8")
pg.setConfigOption("antialias", True)

# ============================================================================
#  SECTION 2: ISO 10816-3 Machine Health Evaluator
# ============================================================================

@dataclass
class ISOResult:
    """Result of ISO 10816-3 vibration severity evaluation."""
    zone: str
    label: str
    color: str
    description_ar: str
    description_en: str
    recommendation: str


class ISO10816Evaluator:
    """
    Evaluates vibration velocity (RMS mm/s) per ISO 10816-3 / ISO 20816-3.

    Machine Group 2: Medium machines (15kW — 300kW), rigid foundation.
    Zones A (excellent) through D (critical danger).
    """
    ZONE_A = 1.4   # mm/s RMS — Excellent (newly commissioned)
    ZONE_B = 2.8   # mm/s RMS — Acceptable (unrestricted long-term operation)
    ZONE_C = 4.5   # mm/s RMS — Unsatisfactory (limited operation, plan maintenance)
    # > 4.5 mm/s   — Zone D: Danger (immediate shutdown required)

    @classmethod
    def evaluate(cls, rms: float) -> ISOResult:
        if rms <= cls.ZONE_A:
            return ISOResult("A", "ZONE A — EXCELLENT", "#2ecc71",
                "حالة الآلة ممتازة ومثالية للتشغيل المستمر.",
                "Machine condition is excellent — ideal for continuous operation.",
                "Continue routine monitoring.")
        elif rms <= cls.ZONE_B:
            return ISOResult("B", "ZONE B — ACCEPTABLE", "#00b894",
                "مستوى الاهتزاز طبيعي ومقبول للتشغيل طويل الأمد.",
                "Vibration level is normal and acceptable for long-term operation.",
                "No maintenance action required.")
        elif rms <= cls.ZONE_C:
            return ISOResult("C", "ZONE C — WARNING", "#f39c12",
                "الاهتزاز غير مُرضٍ. يُحتمل وجود بداية اختلال توازن أو تآكل.",
                "Vibration is unsatisfactory. Possible early unbalance or wear.",
                "Schedule preventive maintenance at next planned shutdown.")
        else:
            return ISOResult("D", "ZONE D — CRITICAL DANGER", "#e74c3c",
                "مستوى اهتزاز خطير جداً يتجاوز الحدود الآمنة!",
                "Vibration exceeds safe limits — catastrophic failure risk!",
                "IMMEDIATE SHUTDOWN REQUIRED to prevent bearing/shaft failure!")

# ============================================================================
#  SECTION 3: UDP Receiver Thread
# ============================================================================

class UDPReceiver(QtCore.QThread):
    """Background thread receiving binary vibration packets via UDP."""
    packet_received = QtCore.Signal(dict)
    connection_changed = QtCore.Signal(bool)

    def __init__(self, host: str = UDP_HOST, port: int = UDP_PORT):
        super().__init__()
        self.host = host
        self.port = port
        self._running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
            sock.settimeout(1.0)
            logger.info(f"Listening on {self.host}:{self.port}")
            self.connection_changed.emit(True)
        except OSError as e:
            logger.error(f"Bind failed: {e}")
            self.connection_changed.emit(False)
            return

        while self._running:
            try:
                data, _ = sock.recvfrom(PACKET_SIZE + 256)
                if len(data) >= PACKET_SIZE:
                    u = struct.unpack(PACKET_FORMAT, data[:PACKET_SIZE])
                    self.packet_received.emit({
                        "timestamp":    u[0],
                        "rms_velocity": u[1],
                        "peak_accel":   u[2],
                        "crest_factor": u[3],
                        "kurtosis":     u[4],
                        "sample_rate":  u[5],
                        "sample_count": u[6],
                        "fault_mode":   u[7],
                        "samples":      np.array(u[8:264], dtype=np.float32),
                        "fft_spectrum": np.array(u[264:392], dtype=np.float32),
                    })
                    self.connection_changed.emit(True)
            except socket.timeout:
                self.connection_changed.emit(False)
            except Exception as e:
                if self._running:
                    logger.warning(f"Receive error: {e}")

        sock.close()
        logger.info("Receiver stopped.")

    def stop(self):
        self._running = False
        self.wait()

# ============================================================================
#  SECTION 4: Python Digital Twin Simulator (no C++ needed for demos)
# ============================================================================

class DigitalTwinSimulator:
    """
    Generates the same vibration signals as the C++ engine and streams them
    via UDP. Used for instant demos without needing a C++ compiler.
    """
    def __init__(self, host: str = UDP_HOST, port: int = UDP_PORT):
        self.host = host
        self.port = port
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._hanning = np.hanning(BLOCK_SIZE).astype(np.float32)

    def run(self, auto_cycle: bool = True):
        logger.info(f"Digital Twin Simulator streaming to {self.host}:{self.port}")
        t = 0.0
        dt = 1.0 / SAMPLE_RATE
        counter = 0
        fault = 0
        names = ["NORMAL", "UNBALANCE (1X)", "MISALIGNMENT (2X)", "BEARING (BPFO)"]

        while self._running:
            counter += 1
            if auto_cycle and counter % 120 == 0:
                fault = (fault + 1) % 4
                logger.info(f"Simulator switched to: {names[fault]}")

            t_block = t + np.arange(BLOCK_SIZE) * dt
            f1 = RUNNING_SPEED_HZ
            noise = np.random.normal(0, 0.25, BLOCK_SIZE).astype(np.float32)

            if fault == 0:
                samples = (0.8 * np.sin(2*np.pi*f1*t_block) + noise).astype(np.float32)
            elif fault == 1:
                samples = (4.8*np.sin(2*np.pi*f1*t_block) + 0.4*np.sin(2*np.pi*2*f1*t_block) + noise).astype(np.float32)
            elif fault == 2:
                samples = (2.5*np.sin(2*np.pi*f1*t_block) + 4.2*np.sin(2*np.pi*2*f1*t_block) + 1.2*np.sin(2*np.pi*3*f1*t_block) + noise).astype(np.float32)
            else:
                mod = np.sin(2*np.pi*4.8*f1*t_block)
                pulses = np.where(mod > 0.85, 7.5*(mod-0.85), 0.0)
                samples = (1.2*np.sin(2*np.pi*f1*t_block) + pulses + np.random.normal(0,0.5,BLOCK_SIZE)).astype(np.float32)

            t += BLOCK_SIZE * dt

            # Statistics
            rms = float(np.sqrt(np.mean(samples**2)))
            peak = float(np.max(np.abs(samples)))
            crest = peak/rms if rms > 1e-4 else 0.0
            var = float(np.var(samples))
            kurt = float(np.mean((samples - np.mean(samples))**4) / (var**2)) if var > 1e-6 else 3.0

            # FFT
            windowed = samples * self._hanning
            fft_mag = (np.abs(np.fft.rfft(windowed, n=BLOCK_SIZE)) * 2.0 / BLOCK_SIZE).astype(np.float32)[:128]

            # Pack & send
            pkt = struct.pack(PACKET_FORMAT, time.time(),
                              rms, peak, crest, kurt, SAMPLE_RATE, BLOCK_SIZE, fault,
                              *samples, *fft_mag)
            self._sock.sendto(pkt, (self.host, self.port))
            time.sleep(0.05)

    def stop(self):
        self._running = False

# ============================================================================
#  SECTION 5: Dark Industrial Theme (QSS Stylesheet)
# ============================================================================

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #0f1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}
QGroupBox {
    background-color: #161923;
    border: 1px solid #2a3044;
    border-radius: 8px;
    margin-top: 18px;
    font-size: 14px;
    font-weight: bold;
    color: #00adb5;
    padding-top: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}
QPushButton {
    background-color: #1e2433;
    border: 1px solid #3b4461;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
    color: #e6edf3;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #2b344a;
    border-color: #00adb5;
    color: #00adb5;
}
QPushButton:pressed {
    background-color: #00adb5;
    color: #ffffff;
}
QTableWidget {
    background-color: #131620;
    border: 1px solid #242a3b;
    border-radius: 6px;
    gridline-color: #1f2433;
    color: #cbd5e1;
    font-size: 12px;
}
QTableWidget::item:selected {
    background-color: #242e47;
}
QHeaderView::section {
    background-color: #1a1e2b;
    border: none;
    border-bottom: 2px solid #2b334a;
    color: #94a3b8;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #11141c;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #2a3144;
    min-height: 20px;
    border-radius: 4px;
}
"""

# ============================================================================
#  SECTION 6: KPI Card Widget
# ============================================================================

class KPICard(QtWidgets.QFrame):
    """Reusable industrial KPI (Key Performance Indicator) card widget."""

    def __init__(self, title: str, unit: str = "", badge: str = ""):
        super().__init__()
        self.setStyleSheet("""
            QFrame { background-color: #1a1d27; border: 1px solid #2d3348;
                     border-radius: 10px; padding: 10px; }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        self.lbl_title = QtWidgets.QLabel(title)
        self.lbl_title.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")

        val_row = QtWidgets.QHBoxLayout()
        self.lbl_value = QtWidgets.QLabel("0.00")
        self.lbl_value.setStyleSheet("font-size: 28px; font-weight: 800; color: #ffffff;")
        self.lbl_unit = QtWidgets.QLabel(f" {unit}")
        self.lbl_unit.setStyleSheet("font-size: 13px; color: #64748b; margin-top: 10px;")
        val_row.addWidget(self.lbl_value)
        val_row.addWidget(self.lbl_unit)
        val_row.addStretch()

        self.lbl_badge = QtWidgets.QLabel(badge)
        self.lbl_badge.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #2ecc71; "
            "background: #1f2d24; padding: 3px 8px; border-radius: 4px;")

        layout.addWidget(self.lbl_title)
        layout.addLayout(val_row)
        layout.addWidget(self.lbl_badge)

    def set_value(self, val: str):
        self.lbl_value.setText(val)

    def set_badge(self, text: str, color: str):
        self.lbl_badge.setText(text)
        bg = color.replace("#", "")
        # Darken the color for background
        r, g, b = int(bg[:2],16)//4, int(bg[2:4],16)//4, int(bg[4:],16)//4
        self.lbl_badge.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {color}; "
            f"background: #{r:02x}{g:02x}{b:02x}; padding: 3px 8px; border-radius: 4px;")

# ============================================================================
#  SECTION 7: Main Dashboard Window
# ============================================================================

FAULT_INFO = {
    0: ("الحالة: طبيعية وسليمة (Normal Operation)",
        "#2ecc71",
        "الآلة تعمل بسلاسة. مواصلة المراقبة الروتينية."),
    1: ("تشخيص: اختلال توازن كتلوي (Unbalance 1X)",
        "#f39c12",
        "تركز الطاقة في التردد الأساسي 25Hz. يوصى بإعادة الموازنة الديناميكية (Dynamic Balancing)."),
    2: ("تشخيص: عدم محاذاة المحاور (Misalignment 2X)",
        "#e67e22",
        "بروز التوافقين 50Hz و 75Hz. يلزم فحص وضبط الوصلة المرنة (Coupling Alignment)."),
    3: ("إنذار حرج: عيب محمل كريات (Bearing BPFO)",
        "#e74c3c",
        "نبضات صدمية بتردد 120Hz مع ارتفاع عامل القمة. يُوصى بفحص التشحيم واستبدال المحمل فوراً!")
}


class MainWindow(QtWidgets.QMainWindow):
    """Industrial vibration monitoring dashboard for maintenance engineers."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(*WINDOW_SIZE)
        self.event_records: list[dict] = []
        self._build_ui()
        self._start_receiver()

    # --- UI Construction ---
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header
        hdr = QtWidgets.QHBoxLayout()
        title_col = QtWidgets.QVBoxLayout()
        lbl_name = QtWidgets.QLabel("MECHPULSE | نظام الرصد الاهتزازي والتنبؤ بالأعطال")
        lbl_name.setStyleSheet("font-size: 20px; font-weight: 800; color: #00adb5;")
        lbl_sub = QtWidgets.QLabel("Unit: High-Pressure Feed Pump #03 — 1500 RPM (25 Hz) | ISO 10816-3 Group 2")
        lbl_sub.setStyleSheet("font-size: 12px; color: #8b949e;")
        title_col.addWidget(lbl_name)
        title_col.addWidget(lbl_sub)
        hdr.addLayout(title_col)
        hdr.addStretch()

        self.lbl_conn = QtWidgets.QLabel("● Waiting for data stream...")
        self.lbl_conn.setStyleSheet("font-size: 13px; font-weight: bold; color: #e74c3c; "
                                     "background: #331818; padding: 6px 14px; border-radius: 6px;")
        hdr.addWidget(self.lbl_conn)
        root.addLayout(hdr)

        # KPI Cards Row
        kpi_row = QtWidgets.QHBoxLayout()
        kpi_row.setSpacing(12)
        self.card_rms   = KPICard("شدة الاهتزاز الفعالة (Velocity RMS)", "mm/s", "ZONE A")
        self.card_peak  = KPICard("أقصى تسارع (Peak Acceleration)", "g", "Normal")
        self.card_crest = KPICard("عامل القمة (Crest Factor)", "", "Bearing OK")
        self.card_kurt  = KPICard("معامل التفرطح (Kurtosis)", "", "No Impulses")
        for c in [self.card_rms, self.card_peak, self.card_crest, self.card_kurt]:
            kpi_row.addWidget(c)
        root.addLayout(kpi_row)

        # Plots Row
        plots = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Time-domain waveform
        time_box = QtWidgets.QGroupBox("مخطط الإشارة الزمنية (Time-Domain Waveform)")
        tl = QtWidgets.QVBoxLayout(time_box)
        self.plot_time = pg.PlotWidget()
        self.plot_time.showGrid(x=True, y=True, alpha=0.3)
        self.plot_time.setLabel("left", "Acceleration", units="g")
        self.plot_time.setLabel("bottom", "Time", units="ms")
        self.plot_time.setYRange(-10, 10)
        self.curve_time = self.plot_time.plot(pen=pg.mkPen("#00adb5", width=1.5))
        tl.addWidget(self.plot_time)
        plots.addWidget(time_box)

        # FFT Spectrum
        freq_box = QtWidgets.QGroupBox("طيف الترددات (FFT Frequency Spectrum)")
        fl = QtWidgets.QVBoxLayout(freq_box)
        self.plot_freq = pg.PlotWidget()
        self.plot_freq.showGrid(x=True, y=True, alpha=0.3)
        self.plot_freq.setLabel("left", "Amplitude", units="mm/s")
        self.plot_freq.setLabel("bottom", "Frequency", units="Hz")
        self.plot_freq.setXRange(0, 300)
        self.plot_freq.setYRange(0, 6)
        self.curve_freq = self.plot_freq.plot(
            pen=pg.mkPen("#f39c12", width=2),
            brush=pg.mkBrush(243, 156, 18, 50), fillLevel=0)
        # Fault frequency markers
        for pos, col, lbl in [(25,"#e74c3c","1X 25Hz"),(50,"#3498db","2X 50Hz"),(120,"#9b59b6","BPFO 120Hz")]:
            line = pg.InfiniteLine(pos=pos, angle=90,
                                   pen=pg.mkPen(col, style=QtCore.Qt.PenStyle.DashLine), label=lbl)
            self.plot_freq.addItem(line)
        fl.addWidget(self.plot_freq)
        plots.addWidget(freq_box)

        root.addWidget(plots, stretch=2)

        # Bottom Row: Diagnostics + Event Log
        bottom = QtWidgets.QHBoxLayout()

        # Diagnostics panel
        diag_box = QtWidgets.QGroupBox("التشخيص الآلي والتوصية الفنية (AI Diagnostics)")
        dl = QtWidgets.QVBoxLayout(diag_box)
        self.lbl_diag = QtWidgets.QLabel("الحالة: طبيعية وسليمة (Normal Operation)")
        self.lbl_diag.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71;")
        self.lbl_rec = QtWidgets.QLabel("التوصية: مواصلة التشغيل الروتيني.")
        self.lbl_rec.setStyleSheet("font-size: 13px; color: #cbd5e1;")
        self.lbl_rec.setWordWrap(True)
        dl.addWidget(self.lbl_diag)
        dl.addWidget(self.lbl_rec)
        dl.addStretch()
        btn_csv = QtWidgets.QPushButton("📊 Export CSV Report | تصدير تقرير الصيانة")
        btn_csv.clicked.connect(self._export_csv)
        dl.addWidget(btn_csv)
        bottom.addWidget(diag_box, stretch=1)

        # Event log table
        log_box = QtWidgets.QGroupBox("سجل الأحداث والتنبيهات (Event Log)")
        ll = QtWidgets.QVBoxLayout(log_box)
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "ISO Zone", "RMS (mm/s)", "Diagnosis"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        ll.addWidget(self.table)
        bottom.addWidget(log_box, stretch=2)

        root.addLayout(bottom, stretch=1)

    # --- Receiver ---
    def _start_receiver(self):
        self.receiver = UDPReceiver()
        self.receiver.packet_received.connect(self._on_packet)
        self.receiver.connection_changed.connect(self._on_connection)
        self.receiver.start()

    def _on_connection(self, connected: bool):
        if connected:
            self.lbl_conn.setText("● Connected (20 FPS)")
            self.lbl_conn.setStyleSheet("font-size: 13px; font-weight: bold; color: #2ecc71; "
                                         "background: #183325; padding: 6px 14px; border-radius: 6px;")
        else:
            self.lbl_conn.setText("● Waiting for data stream...")
            self.lbl_conn.setStyleSheet("font-size: 13px; font-weight: bold; color: #e74c3c; "
                                         "background: #331818; padding: 6px 14px; border-radius: 6px;")

    # --- Packet Processing ---
    def _on_packet(self, pkt: dict):
        rms   = pkt["rms_velocity"]
        peak  = pkt["peak_accel"]
        crest = pkt["crest_factor"]
        kurt  = pkt["kurtosis"]
        fault = pkt["fault_mode"]
        samples  = pkt["samples"]
        spectrum = pkt["fft_spectrum"]
        sr       = pkt["sample_rate"]

        # 1. Update KPI cards
        self.card_rms.set_value(f"{rms:.2f}")
        self.card_peak.set_value(f"{peak:.2f}")
        self.card_crest.set_value(f"{crest:.2f}")
        self.card_kurt.set_value(f"{kurt:.2f}")

        # 2. ISO 10816-3 evaluation
        iso = ISO10816Evaluator.evaluate(rms)
        self.card_rms.set_badge(iso.label, iso.color)

        # 3. Fault diagnosis
        diag_text, diag_color, rec_text = FAULT_INFO.get(fault, FAULT_INFO[0])
        self.lbl_diag.setText(diag_text)
        self.lbl_diag.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {diag_color};")
        self.lbl_rec.setText(f"التوصية الفنية: {rec_text}")

        # 4. Update plots
        time_axis = np.arange(len(samples)) * (1000.0 / sr)
        self.curve_time.setData(time_axis, samples)

        freq_axis = np.linspace(0, sr / 2.0, len(spectrum))
        self.curve_freq.setData(freq_axis, spectrum)

        # 5. Log critical events
        if iso.zone in ("C", "D") or fault == 3:
            now = time.time()
            if not self.event_records or (now - self.event_records[-1]["ts"]) > 2.0:
                rec = {"ts": now, "time": datetime.now().strftime("%H:%M:%S"),
                       "zone": f"Zone {iso.zone}", "rms": f"{rms:.2f}",
                       "diag": diag_text.split("(")[0].strip()}
                self.event_records.append(rec)
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, val in enumerate([rec["time"], rec["zone"], rec["rms"], rec["diag"]]):
                    item = QtWidgets.QTableWidgetItem(val)
                    if col == 1:
                        item.setForeground(QtGui.QColor(iso.color))
                    self.table.setItem(row, col, item)
                self.table.scrollToBottom()

    # --- CSV Export ---
    def _export_csv(self):
        if not self.event_records:
            QtWidgets.QMessageBox.information(self, "Export", "No events recorded yet.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Report", "mechpulse_report.csv", "CSV (*.csv)")
        if path:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Timestamp", "ISO Zone", "RMS Velocity (mm/s)", "Fault Diagnosis"])
                for r in self.event_records:
                    w.writerow([r["time"], r["zone"], r["rms"], r["diag"]])
            QtWidgets.QMessageBox.information(self, "Success", f"Report saved to:\n{path}")

    def closeEvent(self, event):
        self.receiver.stop()
        event.accept()

# ============================================================================
#  SECTION 8: Application Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="MechPulse — Vibration Monitoring Dashboard")
    parser.add_argument("--simulate", action="store_true",
                        help="Run built-in Digital Twin simulator (no C++ engine needed)")
    parser.add_argument("--host", default=UDP_HOST, help=f"UDP host (default: {UDP_HOST})")
    parser.add_argument("--port", type=int, default=UDP_PORT, help=f"UDP port (default: {UDP_PORT})")
    args = parser.parse_args()

    simulator = None
    if args.simulate:
        logger.info("Starting built-in Digital Twin simulator...")
        simulator = DigitalTwinSimulator(args.host, args.port)
        threading.Thread(target=simulator.run, daemon=True).start()

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    ret = app.exec()
    if simulator:
        simulator.stop()
    sys.exit(ret)


if __name__ == "__main__":
    main()
