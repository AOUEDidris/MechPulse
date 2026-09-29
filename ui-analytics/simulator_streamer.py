"""
محاكي بيانات الاهتزاز الموازي بلغة Python (Digital Twin Simulator).
يولد نفس بنية الحزمة الثنائية التي يولدها محرك C++ لتسهيل العرض والتجربة الفورية.
"""

import socket
import struct
import time
import math
import numpy as np

PACKET_FORMAT = "<d 4f 2I i 256f 128f"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

class VibrationSimulator:
    def __init__(self, host="127.0.0.1", port=9876, sample_rate=1000):
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.block_size = 256
        self.running_speed_hz = 25.0  # 1500 RPM
        self.fault_mode = 0           # 0=Normal, 1=Unbalance, 2=Misalignment, 3=Bearing
        self.is_running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def set_fault_mode(self, mode: int):
        self.fault_mode = mode

    def run(self, auto_cycle=True):
        print(f"[Python Twin Simulator] Streaming vibration packets to {self.host}:{self.port}...")
        t_global = 0.0
        dt = 1.0 / self.sample_rate
        counter = 0

        # نافذة Hanning
        hanning = np.hanning(self.block_size)

        while self.is_running:
            counter += 1
            if auto_cycle and (counter % 120 == 0):
                self.fault_mode = (self.fault_mode + 1) % 4
                names = ["NORMAL (Zone A)", "UNBALANCE (1X)", "MISALIGNMENT (1X+2X)", "BEARING DEFECT (BPFO)"]
                print(f"[Simulator Twin] -> Switched mode to: {names[self.fault_mode]}")

            # توليد كتلة العينات الزمنية
            t_block = t_global + np.arange(self.block_size) * dt
            f1 = self.running_speed_hz
            f2 = 2.0 * f1
            f_bpfo = 4.8 * f1 # 120 Hz

            noise = np.random.normal(0.0, 0.25, self.block_size).astype(np.float32)

            if self.fault_mode == 0:  # NORMAL
                samples = 0.8 * np.sin(2.0 * np.pi * f1 * t_block) + noise
            elif self.fault_mode == 1:  # UNBALANCE
                samples = 4.8 * np.sin(2.0 * np.pi * f1 * t_block) + 0.4 * np.sin(2.0 * np.pi * f2 * t_block) + noise
            elif self.fault_mode == 2:  # MISALIGNMENT
                samples = (2.5 * np.sin(2.0 * np.pi * f1 * t_block) +
                           4.2 * np.sin(2.0 * np.pi * f2 * t_block) +
                           1.2 * np.sin(2.0 * np.pi * 3.0 * f1 * t_block) + noise)
            else:  # BEARING FAULT
                pulse_mod = np.sin(2.0 * np.pi * f_bpfo * t_block)
                pulses = np.where(pulse_mod > 0.85, 7.5 * (pulse_mod - 0.85), 0.0)
                samples = 1.2 * np.sin(2.0 * np.pi * f1 * t_block) + pulses + np.random.normal(0.0, 0.5, self.block_size)

            samples = samples.astype(np.float32)
            t_global += self.block_size * dt

            # حساب المؤشرات الإحصائية
            rms = float(np.sqrt(np.mean(samples ** 2)))
            peak = float(np.max(np.abs(samples)))
            crest = float(peak / rms) if rms > 1e-4 else 0.0
            variance = np.var(samples)
            kurtosis = float(np.mean((samples - np.mean(samples))**4) / (variance**2)) if variance > 1e-6 else 3.0

            # حساب طيف الترددات (FFT)
            windowed = samples * hanning
            fft_complex = np.fft.rfft(windowed, n=self.block_size)
            fft_mag = (np.abs(fft_complex) * 2.0 / self.block_size).astype(np.float32)
            # نأخذ أول 128 قيمة
            spectrum = fft_mag[:128]

            # تجميع الحزمة الثنائية
            packet_bytes = struct.pack(
                PACKET_FORMAT,
                time.time(),
                rms,
                peak,
                crest,
                kurtosis,
                self.sample_rate,
                self.block_size,
                self.fault_mode,
                *samples,
                *spectrum
            )

            self.sock.sendto(packet_bytes, (self.host, self.port))
            time.sleep(0.05)  # 20 FPS

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    sim = VibrationSimulator()
    try:
        sim.run(auto_cycle=True)
    except KeyboardInterrupt:
        print("[Simulator Twin] Stopped.")
