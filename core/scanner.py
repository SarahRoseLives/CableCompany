# core/scanner.py
import socket
import struct
import time
import sys
from PyQt5.QtCore import QThread, pyqtSignal
from core.sdt_parser import parse_service_name


class ScannerWorker(QThread):
    progress = pyqtSignal(int)
    channel_found = pyqtSignal(str, str)
    finished = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, start_ip="239.255.0.1", port=1234, limit=20):
        super().__init__()
        self.start_ip = start_ip
        self.port = port
        self.limit = limit
        self.is_running = True

    def run(self):
        base_ip = self.start_ip.rsplit('.', 1)[0]
        start_octet = int(self.start_ip.rsplit('.', 1)[1])
        found_count = 0

        # Create a single socket? No, we need fresh bindings for strict filtering.

        for i in range(self.limit):
            if not self.is_running: break

            current_octet = start_octet + i
            ip = f"{base_ip}.{current_octet}"
            self.status.emit(f"Checking {ip}...")

            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

                # Allow multiple apps to use this port (VLC + Scanner)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # --- CRITICAL FIX FOR LINUX ---
                # Bind DIRECTLY to the multicast IP.
                # This ensures we only receive packets destined for THIS specific group.
                # If we bind to '', we get everything on port 1234.
                try:
                    sock.bind((ip, self.port))
                except OSError:
                    # Fallback for systems that don't allow binding to multicast IP (rare on Linux)
                    sock.bind(('', self.port))

                # Join Multicast Group
                group = socket.inet_aton(ip)
                mreq = struct.pack('4sL', group, socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

                # 1. Quick Check (0.2s)
                # Shorter timeout to speed up scanning of empty space
                sock.settimeout(0.2)

                try:
                    # Peek at data
                    sock.recv(1316)

                    # 2. Deep Scan (Hunt for SDT)
                    # We found a signal, now identify it.
                    channel_name = f"Unknown Channel {current_octet}"

                    # We know data is flowing, so we increase timeout to wait for metadata
                    sock.settimeout(0.5)
                    start_hunt = time.time()

                    # Hunt for up to 2 seconds
                    while time.time() - start_hunt < 2.0:
                        if not self.is_running: break
                        try:
                            chunk = sock.recv(4096)
                            name = parse_service_name(chunk)
                            if name:
                                channel_name = name
                                break
                        except socket.timeout:
                            break

                    self.channel_found.emit(channel_name, ip)
                    found_count += 1

                except socket.timeout:
                    pass  # Silence is golden (no channel here)

                # Cleanup
                try:
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
                except:
                    pass
                sock.close()

            except Exception as e:
                # print(f"Error scanning {ip}: {e}") # Debug only
                if sock: sock.close()

            self.progress.emit(int((i + 1) / self.limit * 100))

        self.finished.emit(found_count)

    def stop(self):
        self.is_running = False