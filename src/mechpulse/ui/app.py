"""Application entry point for MechPulse."""

import sys
import argparse
import logging
import threading
from PySide6.QtWidgets import QApplication
import pyqtgraph as pg

from mechpulse.ui.main_window import MainWindow
from mechpulse.ui.theme import DARK_STYLESHEET
from mechpulse.core.simulator import VibrationSimulator

logger = logging.getLogger(__name__)

def main() -> None:
    """Parses arguments, configures environment, and starts the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(description="MechPulse Vibration Monitoring Dashboard")
    parser.add_argument("--simulate", action="store_true", help="Start the internal digital twin simulator")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="UDP host to bind/send to")
    parser.add_argument("--port", type=int, default=5005, help="UDP port")
    args = parser.parse_args()

    # PyQtGraph global configuration
    pg.setConfigOption('background', '#131620')
    pg.setConfigOption('foreground', '#94a3b8')
    pg.setConfigOption('antialias', True)

    simulator = None
    if args.simulate:
        logger.info("Starting internal simulator...")
        simulator = VibrationSimulator(host=args.host, port=args.port)
        sim_thread = threading.Thread(target=simulator.run, daemon=True)
        sim_thread.start()

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    
    window = MainWindow()
    # Override receiver host/port if provided
    window.receiver.host = args.host
    window.receiver.port = args.port
    
    window.show()
    
    exit_code = app.exec()
    
    if simulator:
        simulator.stop()
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
