import socket
import struct
import time
from datetime import datetime

def is_wol_packet(data, target_mac=None):
    """Check if the received data is a Wake-on-LAN magic packet."""
    if len(data) != 102:  # WoL magic packet is always 102 bytes
        return False
    
    # Check for 6 bytes of 0xFF
    if data[:6] != b'\xFF' * 6:
        return False
    
    # Extract the MAC address from the packet
    mac_bytes = data[6:12]
    mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
    
    # If a target MAC is specified, check if this packet is for that MAC
    if target_mac:
        target_mac_clean = target_mac.replace(':', '').replace('-', '').lower()
        packet_mac_clean = mac_str.replace(':', '').lower()
        if target_mac_clean != packet_mac_clean:
            return False
    
    return True, mac_str

def monitor_wol_packets(target_mac=None, ports=[7, 9]):
    """
    Monitor for Wake-on-LAN packets.
    
    Args:
        target_mac (str): Optional MAC address to filter for specific packets
        ports (list): List of ports to monitor (default: 7 and 9, common WoL ports)
    """
    sockets = []
    
    try:
        # Create a socket for each port
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', port))
            sock.settimeout(0.1)  # Small timeout for non-blocking operation
            sockets.append((sock, port))
        
        print(f"\n=== Wake-on-LAN Packet Monitor ===")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Monitoring ports: {', '.join(map(str, ports))}")
        if target_mac:
            print(f"Filtering for MAC: {target_mac}")
        print("\nWaiting for packets...\n")
        
        try:
            while True:
                for sock, port in sockets:
                    try:
                        data, addr = sock.recvfrom(1024)
                        is_wol, mac = is_wol_packet(data, target_mac)
                        
                        if is_wol:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] WoL Packet Received!")
                            print(f"└─ From: {addr[0]}:{addr[1]}")
                            print(f"└─ To Port: {port}")
                            print(f"└─ Target MAC: {mac}")
                            print(f"└─ Packet Size: {len(data)} bytes")
                            print("└─ Status: Valid Wake-on-LAN magic packet ✓\n")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error receiving packet: {e}")
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            
    except Exception as e:
        print(f"Error setting up monitor: {e}")
    
    finally:
        for sock, _ in sockets:
            try:
                sock.close()
            except:
                pass

if __name__ == "__main__":
    # You can specify your MAC address here to filter packets
    YOUR_MAC = "2c:4d:54:cf:f7:c1"  # Replace with your MAC address
    monitor_wol_packets(target_mac=YOUR_MAC)
