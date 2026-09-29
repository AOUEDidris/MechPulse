"""Digital Twin Vibration Simulator module."""

import time
import struct
import socket
import logging
import threading
from typing import ClassVar
import numpy as np

logger = logging.getLogger(__name__)


class VibrationSimulator:
    """Simulates a C++ vibration engine outputting UDP packets.

    Generates synthetic time-domain waveforms for various machine faults,
    computes FFT and KPIs, and sends them via UDP matching the C++ struct.
    """

    PACKET_FMT: ClassVar[str] = "<d 4f 2I i 256f 128f"
    PACKET_SIZE: ClassVar[int] = struct.calcsize(PACKET_FMT)

    def __init__(self, host: str = "127.0.0.1", port: int = 5005, sample_rate: int = 1000):
        """Initializes the VibrationSimulator.

        Args:
            host: Target host IP for UDP packets.
            port: Target UDP port.
            sample_rate: The simulated sampling rate in Hz.
        """
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.sample_count = 256
        self._is_running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet_counter = 0

    def generate_signal(self, fault_mode: int) -> np.ndarray:
        """Generates a synthetic vibration signal based on fault mode.

        Args:
            fault_mode: 0=Normal, 1=Unbalance, 2=Misalignment, 3=BearingFault.

        Returns:
            A numpy array of 256 time-domain acceleration samples.
        """
        t = np.arange(self.sample_count) / self.sample_rate
        f0 = 25.0  # Running speed 1X (25 Hz = 1500 RPM)
        
        # Base normal noise
        signal = np.random.normal(0, 0.1, self.sample_count)
        
        if fault_mode == 0:
            # Normal: Just small 1X component
            signal += 0.5 * np.sin(2 * np.pi * f0 * t)
        elif fault_mode == 1:
            # Unbalance: High 1X component
            signal += 3.0 * np.sin(2 * np.pi * f0 * t)
        elif fault_mode == 2:
            # Misalignment: High 1X and 2X components
            signal += 1.5 * np.sin(2 * np.pi * f0 * t)
            signal += 2.5 * np.sin(2 * np.pi * 2 * f0 * t)
        elif fault_mode == 3:
            # Bearing Fault: High frequency impacts (BPFO ~ 120Hz)
            signal += 0.5 * np.sin(2 * np.pi * f0 * t)
            bpfo = 120.0
            signal += 1.2 * np.sin(2 * np.pi * bpfo * t)
            # Add impulsive impacts
            impacts = np.zeros(self.sample_count)
            impacts[::int(self.sample_rate/bpfo)] = 5.0
            signal += impacts
            
        return signal

    def run(self) -> None:
        """Main simulator loop generating and sending packets."""
        self._is_running = True
        logger.info(f"Simulator started, sending to {self.host}:{self.port}")
        
        while self._is_running:
            # Auto cycle faults every 120 packets
            fault_mode = (self.packet_counter // 120) % 4
            
            timestamp = time.time()
            samples = self.generate_signal(fault_mode)
            
            # Compute KPIs
            rms_velocity = float(np.sqrt(np.mean(np.square(samples))) * 1.5) # scaling for realistic velocity
            peak_accel = float(np.max(np.abs(samples)))
            rms_accel = float(np.sqrt(np.mean(np.square(samples))))
            crest_factor = peak_accel / rms_accel if rms_accel > 0 else 1.0
            
            # Kurtosis
            mean = np.mean(samples)
            std = np.std(samples)
            if std > 0:
                kurtosis = float(np.mean(((samples - mean) / std) ** 4))
            else:
                kurtosis = 3.0
                
            # Compute FFT with Hanning window
            window = np.hanning(self.sample_count)
            windowed_samples = samples * window
            fft_complex = np.fft.rfft(windowed_samples)
            # Take magnitude and scale, we only need 128 bins for 256 samples
            fft_mag = np.abs(fft_complex)[:128] * (2.0 / self.sample_count)
            
            # Pack data
            samples_list = samples.tolist()
            fft_list = fft_mag.tolist()
            
            # Ensure exact length
            if len(samples_list) != 256:
                samples_list = (samples_list + [0.0]*256)[:256]
            if len(fft_list) != 128:
                fft_list = (fft_list + [0.0]*128)[:128]
                
            pack_args = [
                self.PACKET_FMT,
                timestamp, rms_velocity, peak_accel, crest_factor, kurtosis,
                self.sample_rate, self.sample_count, fault_mode
            ]
            pack_args.extend(samples_list)
            pack_args.extend(fft_list)
            
            try:
                data = struct.pack(*pack_args)
                self.sock.sendto(data, (self.host, self.port))
            except Exception as e:
                logger.error(f"Simulator send error: {e}")
                
            self.packet_counter += 1
            time.sleep(0.1) # Simulate ~10Hz update rate

    def stop(self) -> None:
        """Stops the simulator."""
        self._is_running = False
        logger.info("Simulator stopped.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sim = VibrationSimulator()
    t = threading.Thread(target=sim.run, daemon=True)
    t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()
