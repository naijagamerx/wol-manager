"""
Wake-on-LAN Manager
==================

A comprehensive tool for managing and monitoring Wake-on-LAN functionality.

Developed in collaboration with Demo Homex (https://demohomex.com)
Copyright (c) 2024 Demo Homex - MIT License

Features:
- Web interface for remote access
- Terminal-based menu interface
- Real-time WoL packet monitoring
- Network adapter configuration
- Comprehensive network information display
- BIOS/UEFI setup guide
"""

import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import winreg
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import netifaces
import psutil

# Flask application
app = Flask(__name__)

class WoLManager:
    def __init__(self):
        self.monitor_thread = None
        self.web_thread = None
        self.is_monitoring = False

    def get_network_info(self):
        """Get comprehensive network information."""
        network_info = {
            "system": {
                "os": platform.system(),
                "os_version": platform.version(),
                "computer_name": platform.node()
            },
            "network_interfaces": []
        }

        interfaces = netifaces.interfaces()
        for interface in interfaces:
            try:
                mac_info = netifaces.ifaddresses(interface).get(netifaces.AF_LINK, [{}])[0]
                mac_address = mac_info.get('addr', 'N/A')
                
                ipv4_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
                ipv4 = ipv4_info[0]['addr'] if ipv4_info else 'N/A'
                
                try:
                    stats = psutil.net_if_stats()
                    is_up = interface in stats and stats[interface].isup
                except Exception:
                    is_up = False

                interface_details = {
                    "name": interface,
                    "mac_address": mac_address,
                    "ipv4_address": ipv4,
                    "is_up": is_up
                }

                if platform.system() == 'Windows':
                    interface_details.update(self.check_wol_support(interface))

                network_info["network_interfaces"].append(interface_details)
            
            except Exception as e:
                print(f"Error processing interface {interface}: {e}")

        return network_info

    def check_wol_support(self, interface):
        """Check Wake-on-LAN support for a network interface."""
        wol_support = {
            "wol_support": False,
            "wol_settings": []
        }

        try:
            # Check registry for network adapter settings
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                # Check if this is the right network adapter
                                net_cfg_instance_id = winreg.QueryValueEx(subkey, "NetCfgInstanceId")[0]
                                if net_cfg_instance_id.lower() == interface.lower():
                                    # Check WoL-related registry values
                                    try:
                                        wol_magic = winreg.QueryValueEx(subkey, "*WakeOnMagicPacket")[0]
                                        wol_support["wol_settings"].append(
                                            f"Wake on Magic Packet: {'Enabled' if wol_magic == 1 else 'Disabled'}")
                                    except:
                                        pass

                                    try:
                                        pme_support = winreg.QueryValueEx(subkey, "PMESupported")[0]
                                        wol_support["wol_settings"].append(
                                            f"PME Support: {'Yes' if pme_support == 1 else 'No'}")
                                    except:
                                        pass

                                    wol_support["wol_support"] = True
                                    break
                            except:
                                continue
                    except:
                        continue
        except Exception as e:
            wol_support["wol_settings"].append(f"Error checking registry: {e}")

        return wol_support

    def enable_wol_adapter(self, interface_name):
        """Enable Wake-on-LAN for a network adapter."""
        try:
            # Use PowerShell to enable WoL
            ps_command = f"""
            $adapter = Get-NetAdapter | Where-Object {{$_.InterfaceDescription -like '*{interface_name}*'}}
            $adapter | Set-NetAdapterPowerManagement -WakeOnMagicPacket Enabled
            """
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            return True, "Wake-on-LAN enabled successfully"
        except Exception as e:
            return False, f"Failed to enable Wake-on-LAN: {e}"

    def send_wol_packet(self, mac_address, broadcast="255.255.255.255", port=9):
        """Send a Wake-on-LAN packet."""
        print(f"\n=== Wake-on-LAN Packet Details ===")
        print(f"Target MAC: {mac_address}")
        print(f"Broadcast Address: {broadcast}")
        print(f"Port: {port}")
        
        try:
            mac_bytes = bytes.fromhex(mac_address.replace(':', '').replace('-', ''))
            magic_packet = b'\xFF' * 6 + mac_bytes * 16
            
            print(f"Magic Packet Size: {len(magic_packet)} bytes")
            print("Magic Packet Structure:")
            print(f"- Synchronization Stream: {' '.join([f'{b:02x}' for b in magic_packet[:6]])}")
            print(f"- Target MAC (First Copy): {' '.join([f'{b:02x}' for b in magic_packet[6:12]])}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            print("\nSending packet...")
            sock.sendto(magic_packet, (broadcast, port))
            print(f"✓ Packet sent successfully to {broadcast}:{port}")
            sock.close()
            return True
            
        except Exception as e:
            print(f"\n× Error sending WoL packet: {e}")
            return False

    def monitor_wol_packets(self, target_mac=None):
        """Monitor for incoming Wake-on-LAN packets."""
        self.is_monitoring = True
        ports = [7, 9]  # Common WoL ports
        sockets = []

        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind(('', port))
                sock.settimeout(0.1)
                sockets.append((sock, port))

            print(f"\n=== Wake-on-LAN Packet Monitor ===")
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Monitoring ports: {', '.join(map(str, ports))}")
            if target_mac:
                print(f"Filtering for MAC: {target_mac}")
            print("\nWaiting for packets...\n")

            while self.is_monitoring:
                for sock, port in sockets:
                    try:
                        data, addr = sock.recvfrom(1024)
                        if len(data) == 102 and data[:6] == b'\xFF' * 6:
                            mac_bytes = data[6:12]
                            mac_str = ':'.join(f'{b:02x}' for b in mac_bytes)
                            
                            if not target_mac or mac_str.lower() == target_mac.lower():
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"[{timestamp}] WoL Packet Received!")
                                print(f"└─ From: {addr[0]}:{addr[1]}")
                                print(f"└─ To Port: {port}")
                                print(f"└─ Target MAC: {mac_str}")
                                print(f"└─ Packet Size: {len(data)} bytes")
                                print("└─ Status: Valid Wake-on-LAN magic packet ✓\n")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.is_monitoring:
                            print(f"Error receiving packet: {e}")

        except Exception as e:
            print(f"Error in monitor: {e}")
        finally:
            for sock, _ in sockets:
                try:
                    sock.close()
                except:
                    pass

    def start_web_server(self):
        """Start the Flask web server."""
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    def show_menu(self):
        """Display the main menu."""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n" + "═" * 50)
            print(" Wake-on-LAN Manager ".center(50, "═"))
            print("═" * 50)
            print("\n" + " Welcome to LAN Manager ".center(50, "─"))
            print(" Developed by Demo Homex ".center(50))
            print(" https://demohomex.com ".center(50))
            print("\n" + "─" * 50 + "\n")
            
            print("1 │ Show Network Information")
            print("2 │ Enable Wake-on-LAN for Network Adapter")
            print("3 │ Send Wake-on-LAN Packet")
            print("4 │ Start Packet Monitor")
            print("5 │ Start Web Interface")
            print("6 │ Configure BIOS/UEFI Settings Guide")
            print("7 │ Exit")
            print("\n" + "─" * 50)
            
            choice = input("\nEnter your choice (1-7): ")
            
            if choice == '1':
                network_info = self.get_network_info()
                print("\nNetwork Information:")
                print(json.dumps(network_info, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == '2':
                network_info = self.get_network_info()
                print("\nAvailable Network Adapters:")
                for i, interface in enumerate(network_info['network_interfaces'], 1):
                    print(f"{i}. {interface['name']} ({interface['mac_address']})")
                
                try:
                    idx = int(input("\nEnter adapter number to enable WoL: ")) - 1
                    if 0 <= idx < len(network_info['network_interfaces']):
                        success, msg = self.enable_wol_adapter(
                            network_info['network_interfaces'][idx]['name'])
                        print(msg)
                except ValueError:
                    print("Invalid input")
                input("\nPress Enter to continue...")
                
            elif choice == '3':
                mac = input("Enter target MAC address (xx:xx:xx:xx:xx:xx): ")
                broadcast = input("Enter broadcast address (default: 255.255.255.255): ")
                if not broadcast:
                    broadcast = "255.255.255.255"
                self.send_wol_packet(mac, broadcast)
                input("\nPress Enter to continue...")
                
            elif choice == '4':
                if not self.monitor_thread or not self.monitor_thread.is_alive():
                    mac = input("Enter MAC address to filter (optional): ")
                    self.monitor_thread = threading.Thread(
                        target=self.monitor_wol_packets, args=(mac if mac else None,))
                    self.monitor_thread.daemon = True
                    self.monitor_thread.start()
                    print("\nMonitor started! Press Enter to stop...")
                    input()
                    self.is_monitoring = False
                    self.monitor_thread.join()
                else:
                    print("Monitor is already running!")
                    input("\nPress Enter to continue...")
                
            elif choice == '5':
                if not self.web_thread or not self.web_thread.is_alive():
                    print("\nStarting web interface...")
                    self.web_thread = threading.Thread(target=self.start_web_server)
                    self.web_thread.daemon = True
                    self.web_thread.start()
                    print(f"\nWeb interface available at:")
                    print(f"Local: http://127.0.0.1:5000")
                    network_info = self.get_network_info()
                    for interface in network_info['network_interfaces']:
                        if interface['ipv4_address'] != 'N/A':
                            print(f"Network: http://{interface['ipv4_address']}:5000")
                else:
                    print("\nWeb interface is already running!")
                input("\nPress Enter to continue...")
                
            elif choice == '6':
                print("\n=== BIOS/UEFI Wake-on-LAN Setup Guide ===")
                print("1. Restart your computer and enter BIOS/UEFI settings")
                print("   (Usually by pressing F2, F12, or Delete during startup)")
                print("\n2. Look for these settings (names may vary):")
                print("   - Power Management or Power Options")
                print("   - Wake-on-LAN")
                print("   - Network Boot")
                print("   - PCI Device Power On")
                print("   - Resume By PCI-E Device")
                print("\n3. Enable the Wake-on-LAN or similar option")
                print("\n4. Save changes and exit BIOS/UEFI")
                print("\n5. In Windows, also check:")
                print("   - Device Manager > Network Adapter > Properties")
                print("   - Power Management tab")
                print("   - Check 'Allow this device to wake the computer'")
                print("   - Check 'Only allow a magic packet to wake the computer'")
                input("\nPress Enter to continue...")
                
            elif choice == '7':
                print("\nExiting...")
                self.is_monitoring = False
                if self.monitor_thread and self.monitor_thread.is_alive():
                    self.monitor_thread.join()
                sys.exit(0)

# Flask routes
@app.route('/')
def index():
    network_info = wol_manager.get_network_info()
    return render_template('index.html', network_info=network_info)

@app.route('/wake', methods=['POST'])
def wake():
    try:
        data = request.json
        mac_address = data.get('mac_address')
        broadcast = data.get('broadcast', '255.255.255.255')
        
        if not mac_address:
            return jsonify({'error': 'MAC address is required'}), 400
            
        success = wol_manager.send_wol_packet(mac_address, broadcast)
        
        if success:
            return jsonify({'message': 'Wake-on-LAN packet sent successfully'})
        else:
            return jsonify({'error': 'Failed to send Wake-on-LAN packet'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    wol_manager = WoLManager()
    wol_manager.show_menu()
