"""
الواجهة الرسومية الرئيسية لمهندس الصيانة (PySide6 + PyQtGraph)
تعرض إشارات الاهتزاز والتحليل الطيفي ومؤشرات المعايير الصناعية ISO 10816 في الوقت الحقيقي.
"""

import sys
import csv
import time
from datetime import datetime
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

from iso_evaluator import ISO10816Evaluator
from receiver import UDPReceiverThread
from gui.styles import INDUSTRIAL_DARK_THEME

# إعداد pyqtgraph للسمة الداكنة
pg.setConfigOption('background', '#131620')
pg.setConfigOption('foreground', '#94a3b8')
pg.setConfigOption('antialias', True)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VibrationGuard AI - Real-Time Predictive Maintenance (Algeria Industry 4.0)")
        self.resize(1300, 850)
        self.setStyleSheet(INDUSTRIAL_DARK_THEME)

        self.event_records = []
        self.init_ui()
        self.init_receiver()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. شريط العنوان العلوي (Header)
        header_layout = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QVBoxLayout()
        
        lbl_app = QtWidgets.QLabel("VIBRATIONGUARD AI | نظام الرصد الاهتزازي والتنبؤ بالأعطال")
        lbl_app.setStyleSheet("font-size: 20px; font-weight: 800; color: #00adb5;")
        
        lbl_sub = QtWidgets.QLabel("Algerian Industrial Plants | Unit: High-Pressure Feed Pump #03 (1500 RPM / 25Hz)")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8b949e;")
        title_box.addWidget(lbl_app)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # مؤشر الاتصال
        self.lbl_conn = QtWidgets.QLabel("● جاري انتظار البث (Port 9876)...")
        self.lbl_conn.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c; background: #1f2433; padding: 6px 14px; border-radius: 6px;")
        header_layout.addWidget(self.lbl_conn)

        main_layout.addLayout(header_layout)

        # 2. صف بطاقات المؤشرات اللحظية (KPI Cards Row)
        kpi_row = QtWidgets.QHBoxLayout()
        kpi_row.setSpacing(12)

        self.card_rms, self.lbl_val_rms, self.lbl_badge_iso = self.create_kpi_card("شدة الاهتزاز الفعالة (Velocity RMS)", "0.00", "mm/s", "ZONE A - NORMAL")
        self.card_peak, self.lbl_val_peak, _ = self.create_kpi_card("أقصى تسارع اهتزازي (Peak Accel)", "0.00", "g", "Normal Range")
        self.card_crest, self.lbl_val_crest, self.lbl_sub_crest = self.create_kpi_card("عامل القمة (Crest Factor)", "0.00", "", "Bearing Health Index")
        self.card_kurt, self.lbl_val_kurt, self.lbl_sub_kurt = self.create_kpi_card("معامل التفرطح (Kurtosis)", "3.00", "", "Shock Pulse Metric")

        kpi_row.addWidget(self.card_rms)
        kpi_row.addWidget(self.card_peak)
        kpi_row.addWidget(self.card_crest)
        kpi_row.addWidget(self.card_kurt)
        main_layout.addLayout(kpi_row)

        # 3. المنطقة الوسطى: الرسوم البيانية (Oscilloscope & FFT Spectrum)
        plots_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # مخطط المجال الزمني (Time Domain)
        time_box = QtWidgets.QGroupBox("مخطط الإشارة في المجال الزمني (Time-Domain Waveform)")
        time_layout = QtWidgets.QVBoxLayout(time_box)
        self.plot_time = pg.PlotWidget()
        self.plot_time.showGrid(x=True, y=True, alpha=0.3)
        self.plot_time.setLabel('left', 'Acceleration', units='g')
        self.plot_time.setLabel('bottom', 'Time', units='ms')
        self.plot_time.setYRange(-10, 10)
        self.curve_time = self.plot_time.plot(pen=pg.mkPen(color='#00adb5', width=1.5))
        time_layout.addWidget(self.plot_time)
        plots_splitter.addWidget(time_box)

        # مخطط طيف الترددات (FFT Spectrum)
        freq_box = QtWidgets.QGroupBox("طيف الترددات والقمم التوافقية (FFT Frequency Spectrum)")
        freq_layout = QtWidgets.QVBoxLayout(freq_box)
        self.plot_freq = pg.PlotWidget()
        self.plot_freq.showGrid(x=True, y=True, alpha=0.3)
        self.plot_freq.setLabel('left', 'Amplitude', units='mm/s')
        self.plot_freq.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_freq.setXRange(0, 300)
        self.plot_freq.setYRange(0, 6)
        self.curve_freq = self.plot_freq.plot(
            pen=pg.mkPen(color='#f39c12', width=2.0),
            brush=pg.mkBrush(color=(243, 156, 18, 50)),
            fillLevel=0
        )
        # خطوط دلالية للترددات الهامة
        self.line_1x = pg.InfiniteLine(pos=25.0, angle=90, pen=pg.mkPen('#e74c3c', style=QtCore.Qt.PenStyle.DashLine), label="1X (25Hz)")
        self.line_2x = pg.InfiniteLine(pos=50.0, angle=90, pen=pg.mkPen('#3498db', style=QtCore.Qt.PenStyle.DashLine), label="2X (50Hz)")
        self.line_bpfo = pg.InfiniteLine(pos=120.0, angle=90, pen=pg.mkPen('#9b59b6', style=QtCore.Qt.PenStyle.DashLine), label="BPFO (120Hz)")
        self.plot_freq.addItem(self.line_1x)
        self.plot_freq.addItem(self.line_2x)
        self.plot_freq.addItem(self.line_bpfo)

        freq_layout.addWidget(self.plot_freq)
        plots_splitter.addWidget(freq_box)

        main_layout.addWidget(plots_splitter, stretch=2)

        # 4. المنطقة السفلية: التشخيص الآلي وجدول الأحداث (Bottom Control & Log Panel)
        bottom_layout = QtWidgets.QHBoxLayout()

        # صندوق التشخيص الذكي والتوصيات
        diag_box = QtWidgets.QGroupBox("التشخيص الآلي والتوصية الفنية (Automated AI Diagnostics)")
        diag_layout = QtWidgets.QVBoxLayout(diag_box)

        self.lbl_diagnosis = QtWidgets.QLabel("الحالة: طبيعية وسليمة (Normal Operation)")
        self.lbl_diagnosis.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71;")
        self.lbl_recommendation = QtWidgets.QLabel("التوصية: مواصلة التشغيل الروتيني دون قيود.")
        self.lbl_recommendation.setStyleSheet("font-size: 13px; color: #cbd5e1;")
        self.lbl_recommendation.setWordWrap(True)

        diag_layout.addWidget(self.lbl_diagnosis)
        diag_layout.addWidget(self.lbl_recommendation)
        diag_layout.addStretch()

        # زر تصدير التقرير
        btn_export = QtWidgets.QPushButton("تصدير سجل التنبيهات (CSV Report)")
        btn_export.clicked.connect(self.export_csv_report)
        diag_layout.addWidget(btn_export)

        bottom_layout.addWidget(diag_box, stretch=1)

        # جدول الأحداث وسجل التنبيهات اللحظي
        log_box = QtWidgets.QGroupBox("سجل الأحداث وتنبيهات ISO 10816 (Event Log)")
        log_layout = QtWidgets.QVBoxLayout(log_box)
        self.table_log = QtWidgets.QTableWidget(0, 4)
        self.table_log.setHorizontalHeaderLabels(["الوقت", "المنطقة (ISO)", "السرعة (RMS)", "التشخيص"])
        self.table_log.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.table_log)

        bottom_layout.addWidget(log_box, stretch=2)
        main_layout.addLayout(bottom_layout, stretch=1)

    def create_kpi_card(self, title, default_val, unit, subtext):
        card = QtWidgets.QFrame()
        card.setProperty("class", "kpi-card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setProperty("class", "kpi-title")
        lbl_title.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: bold;")

        val_layout = QtWidgets.QHBoxLayout()
        lbl_val = QtWidgets.QLabel(default_val)
        lbl_val.setStyleSheet("font-size: 26px; font-weight: 800; color: #ffffff;")
        lbl_unit = QtWidgets.QLabel(f" {unit}")
        lbl_unit.setStyleSheet("font-size: 13px; color: #64748b; margin-top: 8px;")
        val_layout.addWidget(lbl_val)
        val_layout.addWidget(lbl_unit)
        val_layout.addStretch()

        lbl_sub = QtWidgets.QLabel(subtext)
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: 600; color: #2ecc71; padding: 2px 6px; border-radius: 4px; background: #1f2d24;")

        layout.addWidget(lbl_title)
        layout.addLayout(val_layout)
        layout.addWidget(lbl_sub)
        return card, lbl_val, lbl_sub

    def init_receiver(self):
        self.receiver_thread = UDPReceiverThread(host="127.0.0.1", port=9876)
        self.receiver_thread.packet_received.connect(self.on_packet_received)
        self.receiver_thread.connection_status.connect(self.on_connection_status)
        self.receiver_thread.start()

    def on_connection_status(self, is_connected: bool):
        if is_connected:
            self.lbl_conn.setText("● متصل بمحرك الإشارات (20 FPS)")
            self.lbl_conn.setStyleSheet("font-size: 13px; font-weight: bold; color: #2ecc71; background: #183325; padding: 6px 14px; border-radius: 6px;")
        else:
            self.lbl_conn.setText("● جاري انتظار البث (Port 9876)...")
            self.lbl_conn.setStyleSheet("font-size: 13px; font-weight: bold; color: #e74c3c; background: #331818; padding: 6px 14px; border-radius: 6px;")

    def on_packet_received(self, pkt: dict):
        rms = pkt["rms_velocity"]
        peak = pkt["peak_accel"]
        crest = pkt["crest_factor"]
        kurt = pkt["kurtosis"]
        fault_mode = pkt["fault_mode"]
        samples = pkt["samples"]
        spectrum = pkt["fft_spectrum"]

        # 1. تحديث بطاقات الأرقام
        self.lbl_val_rms.setText(f"{rms:.2f}")
        self.lbl_val_peak.setText(f"{peak:.2f}")
        self.lbl_val_crest.setText(f"{crest:.2f}")
        self.lbl_val_kurt.setText(f"{kurt:.2f}")

        # 2. تقييم معايير ISO 10816-3
        iso_res = ISO10816Evaluator.evaluate(rms)
        self.lbl_badge_iso.setText(iso_res.status_label)
        self.lbl_badge_iso.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {iso_res.color_hex}; background: #1a2233; padding: 3px 6px; border-radius: 4px;")

        # 3. تشخيص نوع العطل الميكانيكي
        fault_names = {
            0: ("الحالة: طبيعية وسليمة (Normal Operation)", "#2ecc71", "الآلة تعمل بسلاسة، استمر في المراقبة الروتينية."),
            1: ("تشخيص: اختلال توازن كتلوي في الدوار (Unbalance 1X)", "#f39c12", "يلاحظ تركيز الطاقة في التردد الأساسي 25Hz. يوصى بإعادة الموازنة الديناميكية (Dynamic Balancing)."),
            2: ("تشخيص: عدم محاذاة المحاور (Misalignment 2X)", "#e67e22", "بروز التوافق الثاني 50Hz والثالث. يلزم فحص الوصلة المرنة (Coupling Alignment)."),
            3: ("إنذار حرج: عيب في محمل الكريات (Bearing Defect BPFO)", "#e74c3c", "ارتفاع ملحوظ في عامل القمة (Crest Factor) ونبضات صدمية بتردد 120Hz. يُوصى بفحص التشحيم واستبدال المحمل فوراً.")
        }

        diag_title, diag_col, diag_rec = fault_names.get(fault_mode, ("حالة غير معروفة", "#95a5a6", ""))
        self.lbl_diagnosis.setText(diag_title)
        self.lbl_diagnosis.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {diag_col};")
        self.lbl_recommendation.setText(f"التوصية الفنية: {diag_rec}")

        # 4. تحديث الرسوم البيانية
        # المجال الزمني (Time Domain)
        time_axis = np.arange(len(samples)) * (1000.0 / pkt["sample_rate"])
        self.curve_time.setData(time_axis, samples)

        # طيف الترددات (FFT Spectrum)
        freq_axis = np.linspace(0, pkt["sample_rate"] / 2.0, len(spectrum))
        self.curve_freq.setData(freq_axis, spectrum)

        # 5. تسجيل الأحداث إذا تم تجاوز الحد المقبول (Zone C أو D)
        if iso_res.zone in ['C', 'D'] or fault_mode == 3:
            now_str = datetime.now().strftime("%H:%M:%S")
            # نسجل مرة كل ثانية كحد أقصى لتفادي التكرار المفرط
            if not self.event_records or (time.time() - self.event_records[-1]["ts"]) > 2.0:
                rec = {
                    "ts": time.time(),
                    "time": now_str,
                    "zone": f"Zone {iso_res.zone}",
                    "rms": f"{rms:.2f} mm/s",
                    "diag": diag_title.split(":")[0]
                }
                self.event_records.append(rec)
                self.add_log_row(rec["time"], rec["zone"], rec["rms"], rec["diag"], iso_res.color_hex)

    def add_log_row(self, time_str, zone, rms, diag, col_hex):
        row = self.table_log.rowCount()
        self.table_log.insertRow(row)

        item_time = QtWidgets.QTableWidgetItem(time_str)
        item_zone = QtWidgets.QTableWidgetItem(zone)
        item_zone.setForeground(QtGui.QColor(col_hex))
        item_rms = QtWidgets.QTableWidgetItem(rms)
        item_diag = QtWidgets.QTableWidgetItem(diag)

        self.table_log.setItem(row, 0, item_time)
        self.table_log.setItem(row, 1, item_zone)
        self.table_log.setItem(row, 2, item_rms)
        self.table_log.setItem(row, 3, item_diag)
        self.table_log.scrollToBottom()

    def export_csv_report(self):
        if not self.event_records:
            QtWidgets.QMessageBox.information(self, "تصدير التقرير", "لا توجد سجلات أحداث مسجلة حالياً.")
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "حفظ تقرير الفحص والاهتزاز", "vibration_report.csv", "CSV Files (*.csv)"
        )
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "ISO Zone", "RMS Velocity (mm/s)", "Fault Diagnosis"])
                    for r in self.event_records:
                        writer.writerow([r["time"], r["zone"], r["rms"], r["diag"]])
                QtWidgets.QMessageBox.information(self, "نجاح", f"تم تصدير التقرير بنجاح إلى:\n{filename}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "خطأ", f"تعذر حفظ الملف: {e}")

    def closeEvent(self, event):
        self.receiver_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
