"""UDP Receiver module for MechPulse."""

import socket
import struct
import logging
import select
from typing import Dict, Any
import numpy as np
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class UDPReceiverThread(QThread):
    """QThread that receives binary UDP packets and parses them.

    Signals:
        packet_received: Emitted when a valid packet is parsed, contains a dict of data.
        connection_status: Emitted when connection status changes (True=connected, False=disconnected).
    """

    packet_received = Signal(dict)
    connection_status = Signal(bool)

    # Packet format:
    # double timestamp (8 bytes)
    # float rms_velocity, peak_accel, crest_factor, kurtosis (16 bytes)
    # uint32_t sample_rate, sample_count (8 bytes)
    # int32_t fault_mode (4 bytes)
    # float samples[256] (1024 bytes)
    # float fft_spectrum[128] (512 bytes)
    # Total: 1572 bytes
    PACKET_FMT = "<d 4f 2I i 256f 128f"
    PACKET_SIZE = struct.calcsize(PACKET_FMT)

    def __init__(self, host: str = "0.0.0.0", port: int = 5005, parent=None):
        """Initializes the UDPReceiverThread.

        Args:
            host: The host IP to bind to.
            port: The UDP port to listen on.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.host = host
        self.port = port
        self._is_running = False
        self.socket: socket.socket | None = None

    def run(self) -> None:
        """Main thread loop for receiving UDP packets."""
        self._is_running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            logger.info(f"UDP receiver bound to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to bind socket: {e}")
            self.connection_status.emit(False)
            return

        while self._is_running:
            try:
                ready = select.select([self.socket], [], [], 1.0)
                if ready[0]:
                    data, addr = self.socket.recvfrom(2048)
                    if len(data) == self.PACKET_SIZE:
                        self.connection_status.emit(True)
                        parsed_data = self._parse_packet(data)
                        if parsed_data:
                            self.packet_received.emit(parsed_data)
                    else:
                        logger.warning(f"Received packet of incorrect size: {len(data)}")
                else:
                    self.connection_status.emit(False)
            except Exception as e:
                logger.error(f"Error receiving packet: {e}")
                self.connection_status.emit(False)

        if self.socket:
            self.socket.close()

    def _parse_packet(self, data: bytes) -> Dict[str, Any] | None:
        """Parses raw byte data into a dictionary.

        Args:
            data: The raw binary data received from the UDP socket.

        Returns:
            A dictionary containing parsed packet data, or None if parsing fails.
        """
        try:
            unpacked = struct.unpack(self.PACKET_FMT, data)
            timestamp = unpacked[0]
            rms_velocity = unpacked[1]
            peak_accel = unpacked[2]
            crest_factor = unpacked[3]
            kurtosis = unpacked[4]
            sample_rate = unpacked[5]
            sample_count = unpacked[6]
            fault_mode = unpacked[7]

            samples_end = 8 + 256
            samples = np.array(unpacked[8:samples_end], dtype=np.float32)
            fft_spectrum = np.array(unpacked[samples_end:], dtype=np.float32)

            return {
                "timestamp": timestamp,
                "rms_velocity": rms_velocity,
                "peak_accel": peak_accel,
                "crest_factor": crest_factor,
                "kurtosis": kurtosis,
                "sample_rate": sample_rate,
                "sample_count": sample_count,
                "fault_mode": fault_mode,
                "samples": samples,
                "fft_spectrum": fft_spectrum,
            }
        except Exception as e:
            logger.error(f"Failed to parse packet: {e}")
            return None

    def stop(self) -> None:
        """Stops the receiver loop."""
        self._is_running = False
        self.wait()
        logger.info("UDPReceiverThread stopped.")
