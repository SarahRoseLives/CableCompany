import socket
import struct
import time
from PyQt5.QtCore import QThread, pyqtSignal
from core.sdt_parser import parse_service_name


class ScannerWorker(QThread):
    progress = pyqtSignal(int)
    channel_found = pyqtSignal(str, str)
    finished = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, mode="smart", custom_range=None, port=1234):
        super().__init__()
        self.mode = mode
        self.custom_range = custom_range
        self.port = port
        self.is_running = True

    def generate_smart_beacons(self):
        beacons = []
        # Block 1: 239.255.x.1
        for i in range(0, 256):
            beacons.append(f"239.255.{i}.1")
        # Block 2: 239.192.x.1
        for i in range(0, 50):
            beacons.append(f"239.192.{i}.1")
        return beacons

    def generate_range_ips(self, pattern):
        parts = pattern.split('.')
        if len(parts) != 4: return []

        def get_range(part):
            if part == '*': return range(0, 256)
            return [int(part)]

        ips = []
        try:
            for a in get_range(parts[0]):
                for b in get_range(parts[1]):
                    for c in get_range(parts[2]):
                        for d in get_range(parts[3]):
                            ips.append(f"{a}.{b}.{c}.{d}")
        except ValueError:
            pass
        return ips

    def run(self):
        scan_queue = []
        if self.mode == "smart":
            self.status.emit("Initializing Smart Scan...")
            scan_queue = self.generate_smart_beacons()
        else:
            scan_queue = self.generate_range_ips(self.custom_range)

        visited = set(scan_queue)
        found_count = 0
        total_estimated = len(scan_queue)
        processed = 0

        while scan_queue:
            # 1. IMMEDIATE STOP CHECK
            if not self.is_running:
                break

            ip = scan_queue.pop(0)
            processed += 1

            self.status.emit(f"Scanning {ip}...")

            # Check IP (This method now checks self.is_running internally)
            is_active = self.check_ip(ip)

            if is_active:
                found_count += 1

                # Adaptive Logic: Add neighbors if we hit a .1 address
                if self.mode == "smart" and ip.endswith(".1"):
                    subnet_base = ip.rsplit('.', 1)[0]
                    self.status.emit(f"🔥 Found subnet {subnet_base}.x! Expanding...")

                    new_ips = []
                    for i in range(2, 256):
                        new_ip = f"{subnet_base}.{i}"
                        if new_ip not in visited:
                            new_ips.append(new_ip)
                            visited.add(new_ip)

                    scan_queue = new_ips + scan_queue
                    total_estimated += len(new_ips)

            # Update Progress
            if total_estimated > 0:
                percent = min(100, int((processed / total_estimated) * 100))
                self.progress.emit(percent)

        self.finished.emit(found_count)

    def check_ip(self, ip):
        sock = None
        found = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind logic
            try:
                sock.bind((ip, self.port))
            except OSError:
                sock.bind(('', self.port))

            group = socket.inet_aton(ip)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # --- PHASE 1: FAST CHECK ---
            # Use a very short timeout (0.1s)
            sock.settimeout(0.1)
            try:
                # Try to peek at data
                sock.recv(1316)

                # Use a second check to ensure we stop immediately if button pressed
                if not self.is_running:
                    sock.close()
                    return False

                # --- PHASE 2: DEEP SCAN ---
                channel_name = f"Unknown {ip}"

                # Keep timeout short (0.1s) but loop many times (20 * 0.1 = 2.0s)
                # This makes the loop check 'is_running' 10 times per second
                start_hunt = time.time()

                while time.time() - start_hunt < 2.0:
                    # CRITICAL: Check stop flag inside the hunt loop
                    if not self.is_running:
                        sock.close()
                        return False

                    try:
                        chunk = sock.recv(4096)
                        name = parse_service_name(chunk)
                        if name:
                            channel_name = name
                            break
                    except socket.timeout:
                        pass  # Just loop again and check is_running

                self.channel_found.emit(channel_name, ip)
                found = True

            except socket.timeout:
                pass  # No signal

            # Cleanup
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except:
                pass
            sock.close()

        except Exception:
            if sock: sock.close()

        return found

    def stop(self):
        """Sets the flag to stop the thread safely."""
        self.is_running = False