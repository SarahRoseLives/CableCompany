# core/sdt_parser.py
import struct


def parse_service_name(data):
    """
    Scans raw MPEG-TS data for the SDT (PID 0x11) and extracts the Service Name.
    """
    packet_size = 188

    # We might receive a buffer that doesn't start exactly at 0x47 if packets dropped.
    # We iterate byte by byte to find the sync marker.
    for i in range(len(data) - packet_size):
        # 1. Find Sync Byte
        if data[i] != 0x47:
            continue

        # 2. Extract PID
        # Header is 4 bytes. PID is 13 bits inside bytes 1 and 2.
        # Header: [Sync] [TEI/PUSI/Pri/PID_H] [PID_L] [Scram/Adapt/Cont]
        header = struct.unpack(">I", data[i:i + 4])[0]
        pid = (header >> 8) & 0x1FFF

        # 3. Check for SDT (PID 0x11)
        if pid == 0x11:
            try:
                payload = data[i + 4: i + 188]

                # Check for Payload Unit Start Indicator (PUSI)
                # If PUSI is 1 (bit 14 of 16-bit word at offset 1), header contains pointer field
                pusi = (header >> 22) & 0x1

                pointer_field = 0
                if pusi:
                    pointer_field = payload[0]
                    payload = payload[1 + pointer_field:]

                # Now we are at the start of the Table Section
                table_id = payload[0]

                # Table ID 0x42 is "Service Description Table - Actual Transport Stream"
                if table_id != 0x42:
                    continue

                # The SDT section structure is complex.
                # Instead of strict parsing, we scan this specific packet for the
                # Service Descriptor Tag (0x48) which contains the text.
                # Format: [Tag 0x48] [Length] [Type] [Provider_Len] [Provider_Name] [Name_Len] [Name]

                for j in range(3, len(payload) - 5):
                    if payload[j] == 0x48:  # Service Descriptor Tag
                        # descriptor_length = payload[j+1]
                        # service_type = payload[j+2]
                        provider_name_len = payload[j + 3]

                        if j + 4 + provider_name_len + 1 >= len(payload):
                            continue

                        service_name_len_offset = j + 4 + provider_name_len
                        service_name_len = payload[service_name_len_offset]

                        start = service_name_len_offset + 1
                        end = start + service_name_len

                        if end > len(payload):
                            continue

                        name_bytes = payload[start:end]

                        # Decode and clean garbage characters
                        # ISO-8859-1 is standard for DVB, but UTF-8 is common in IPTV
                        try:
                            return name_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            return name_bytes.decode('iso-8859-1')

            except Exception:
                continue

    return None