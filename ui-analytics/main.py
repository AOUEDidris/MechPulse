"""
نقطة الدخول الرئيسية لنظام المراقبة والتحليل الاهتزازي VibrationGuard AI.
الاستخدام:
  python main.py             (تشغيل الواجهة والاستماع لمحرك C++ أو البث الخارجي)
  python main.py --simulate  (تشغيل الواجهة مع تشغيل محاكي الإشارات الرقمية التوأم داخلياً)
"""

import sys
import os
import argparse
import threading
from PySide6 import QtWidgets

# إضافة مسار المجلد الحالي إلى sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from simulator_streamer import VibrationSimulator

def start_background_simulator():
    sim = VibrationSimulator(host="127.0.0.1", port=9876, sample_rate=1000)
    sim_thread = threading.Thread(target=sim.run, kwargs={"auto_cycle": True}, daemon=True)
    sim_thread.start()
    return sim

def main():
    parser = argparse.ArgumentParser(description="VibrationGuard AI Dashboard")
    parser.add_argument("--simulate", action="store_true", help="تشغيل المحاكي التوأم الرقمي في الخلفية تلقائياً")
    args = parser.parse_args()

    simulator = None
    if args.simulate:
        print("[+] Starting built-in digital twin vibration simulator...")
        simulator = start_background_simulator()

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("VibrationGuard AI")
    
    window = MainWindow()
    window.show()

    ret = app.exec()
    if simulator:
        simulator.stop()
    sys.exit(ret)

if __name__ == "__main__":
    main()
