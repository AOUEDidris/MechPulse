"""Industrial dark theme configuration and stylesheets."""

from typing import Dict

COLORS: Dict[str, str] = {
    "bg_primary": "#0f1117",
    "bg_secondary": "#161923",
    "bg_card": "#1a1d27",
    "accent": "#00adb5",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "border": "#2d3348",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "info": "#3498db"
}

DARK_STYLESHEET: str = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", Arial, sans-serif;
}}

QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin-top: 1.5ex;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: {COLORS['accent']};
}}

QPushButton {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    color: {COLORS['text_primary']};
    padding: 6px 12px;
}}

QPushButton:hover {{
    background-color: {COLORS['accent']};
    color: {COLORS['bg_primary']};
}}

QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    padding: 4px;
    border: 1px solid {COLORS['border']};
}}

QScrollBar:vertical {{
    border: none;
    background: {COLORS['bg_primary']};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

def get_zone_style(zone: str) -> str:
    """Gets the inline CSS style for a specific ISO zone.

    Args:
        zone: The ISO zone letter ('A', 'B', 'C', or 'D').

    Returns:
        A string containing inline CSS for the zone color.
    """
    color = COLORS.get('success')
    if zone == 'B':
        color = COLORS.get('success') # 00b894
    elif zone == 'C':
        color = COLORS.get('warning')
    elif zone == 'D':
        color = COLORS.get('danger')
        
    return f"color: {color}; font-weight: bold;"
