"""
السمة البصرية الصناعية الداكنة (Modern Dark Industrial Theme)
مصممة لشاشات المراقبة وغرف التحكم (Control Rooms).
"""

INDUSTRIAL_DARK_THEME = """
QMainWindow {
    background-color: #0f1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}

QWidget {
    color: #e6edf3;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}

/* بطاقات المؤشرات (KPI Cards) */
QFrame.kpi-card {
    background-color: #1a1d27;
    border: 1px solid #2d3348;
    border-radius: 10px;
    padding: 12px;
}

QLabel.kpi-title {
    font-size: 13px;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel.kpi-value {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    margin-top: 4px;
}

QLabel.kpi-unit {
    font-size: 13px;
    font-weight: normal;
    color: #64748b;
}

/* شريط الحالة واللوحات */
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

/* الأزرار الصناعية */
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

QPushButton.primary-btn {
    background-color: #00adb5;
    color: #0f1117;
    border: none;
    font-weight: bold;
}

QPushButton.primary-btn:hover {
    background-color: #00c7d1;
    color: #0f1117;
}

/* جدول الأحداث والتنبيهات */
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
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1a1e2b;
    border: none;
    border-bottom: 2px solid #2b334a;
    color: #94a3b8;
    padding: 6px;
    font-weight: bold;
}

/* أشرطة التمرير */
QScrollBar:vertical {
    background: #11141c;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a3144;
    min-height: 20px;
    border-radius: 4px;
}
"""
