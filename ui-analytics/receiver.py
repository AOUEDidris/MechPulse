"""
مستقبل الحزم اللحظية عبر UDP Socket في خيط تشغيل مستقل (QThread).
يقوم بفك الحزمة الثنائية وبث الإشارات إلى الواجهة الرسومية دون أي تأخير.
"""

import socket
import struct
import numpy as np
from PySide6.QtCore import QThread, Signal

class UDPReceiverThread(QThread):
    packet_received = Signal(dict)
    connection_status = Signal(bool)

    # هيكل الحزمة المتطابق تماماً مع محرك C++
    PACKET_FORMAT = "<d 4f 2I i 256f 128f"
    PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        super().__init__()
        self.host = host
        self.port = port
        self.is_running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
            sock.settimeout(1.0)
            self.connection_status.emit(True)
        except Exception as e:
            print(f"[-] Failed to bind socket to {self.host}:{self.port} -> {e}")
            self.connection_status.emit(False)
            return

        last_packet_time = 0.0

        while self.is_running:
            try:
                data, addr = sock.recvfrom(self.PACKET_SIZE + 256)
                if len(data) >= self.PACKET_SIZE:
                    unpacked = struct.unpack(self.PACKET_FORMAT, data[:self.PACKET_SIZE])
                    
                    packet_dict = {
                        "timestamp": unpacked[0],
                        "rms_velocity": unpacked[1],
                        "peak_accel": unpacked[2],
                        "crest_factor": unpacked[3],
                        "kurtosis": unpacked[4],
                        "sample_rate": unpacked[5],
                        "sample_count": unpacked[6],
                        "fault_mode": unpacked[7],
                        "samples": np.array(unpacked[8:8 + 256], dtype=np.float32),
                        "fft_spectrum": np.array(unpacked[8 + 256: 8 + 256 + 128], dtype=np.float32)
                    }

                    self.packet_received.emit(packet_dict)
                    self.connection_status.emit(True)
            except socket.timeout:
                # لم تصل حزم خلال المهلة
                self.connection_status.emit(False)
            except Exception as e:
                if self.is_running:
                    print(f"[-] UDP Receive error: {e}")

        sock.close()

    def stop(self):
        self.is_running = False
        self.wait()
