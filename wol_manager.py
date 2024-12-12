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
            print("7 │ Check WoL Configuration")
            print("8 │ Check BIOS Settings")
            print("9 │ Configure All WoL Settings")
            print("10 │ Exit")
            print("\n" + "─" * 50)
            
            choice = input("\nEnter your choice (1-10): ")
            
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
                self.check_wol_configuration()
            elif choice == '8':
                self.check_bios_settings()
            elif choice == '9':
                self.configure_wol_settings()
            elif choice == '10':
                print("\nExiting...")
                self.is_monitoring = False
                if self.monitor_thread and self.monitor_thread.is_alive():
                    self.monitor_thread.join()
                sys.exit(0)

    def check_bios_settings(self):
        """Check BIOS settings related to Wake-on-LAN using PowerShell."""
        print("\n" + "="*50)
        print("CHECKING BIOS/UEFI SETTINGS")
        print("="*50 + "\n")

        try:
            # Get BIOS information using PowerShell
            print("\n[1] BIOS Information:")
            print("-" * 20)
            bios_info = subprocess.check_output(
                ["powershell", "Get-WmiObject -Class Win32_BIOS | Format-List Manufacturer,Name,Version,SerialNumber"],
                text=True
            )
            print(bios_info)
            input("Press Enter to continue to power settings...")

            # Get power settings related to Wake-on-LAN
            print("\n[2] Power Settings Related to Wake:")
            print("-" * 20)
            
            # Get current power scheme
            current_scheme = subprocess.check_output(
                ["powershell", "powercfg /getactivescheme"],
                text=True
            ).strip()
            print("Current Power Scheme:", current_scheme)
            
            # Get network adapter settings using registry and advanced queries
            print("\nNetwork Adapter Settings:")
            power_settings = subprocess.check_output(
                ["powershell", """
                $adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}
                foreach ($adapter in $adapters) {
                    Write-Output "`nAdapter: $($adapter.Name)"
                    Write-Output "Status: $($adapter.Status)"
                    Write-Output "Media Type: $($adapter.MediaType)"
                    Write-Output "Interface Description: $($adapter.InterfaceDescription)"
                    
                    # Check registry for Wake-on-LAN settings
                    $adapterRegPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}"
                    Get-ChildItem $adapterRegPath | ForEach-Object {
                        $regPath = $_.PSPath
                        $description = (Get-ItemProperty -Path $regPath).DriverDesc
                        if ($description -eq $adapter.InterfaceDescription) {
                            $wolMagicPacket = (Get-ItemProperty -Path $regPath).WolMagicPacket
                            $pmARPOffload = (Get-ItemProperty -Path $regPath).PMARPOffload
                            $pmNSOffload = (Get-ItemProperty -Path $regPath).PMNSOffload
                            $pmWakeOnPattern = (Get-ItemProperty -Path $regPath).WakeOnPattern
                            
                            Write-Output "`nWake-on-LAN Settings:"
                            Write-Output "  Wake on Magic Packet: $wolMagicPacket"
                            Write-Output "  PM ARP Offload: $pmARPOffload"
                            Write-Output "  PM NS Offload: $pmNSOffload"
                            Write-Output "  Wake on Pattern: $pmWakeOnPattern"
                        }
                    }
                    Write-Output "-----------------"
                }"""],
                text=True
            )
            print(power_settings)
            
            # Get device wake capabilities
            print("\n[3] System Wake Capabilities:")
            print("-" * 20)
            wake_status = subprocess.check_output(
                ["powershell", """
                Write-Output "Devices that can wake the system:"
                $wakeDevices = powercfg /devicequery wake_armed
                $wakeDevices | ForEach-Object {
                    Write-Output "  * $_"
                }
                
                Write-Output "`nPower Settings Status:"
                # Check if Fast Startup is enabled
                $fastStartup = Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" -Name HiberbootEnabled -ErrorAction SilentlyContinue
                Write-Output "  Fast Startup: $(if ($fastStartup.HiberbootEnabled -eq 1) { 'Enabled' } else { 'Disabled' })"
                
                # Check network adapter wake settings
                Write-Output "`nNetwork Adapter Wake Status:"
                Get-WmiObject MSPower_DeviceWakeEnable -Namespace root/wmi | ForEach-Object {
                    $status = if ($_.Enable) { "Enabled" } else { "Disabled" }
                    Write-Output "  * Wake capability: $status"
                }"""],
                text=True
            )
            print(wake_status)
            
            print("\nBIOS Settings Check Complete!")
            print("=" * 50)
            
            # Print recommendations
            print("\nRecommendations:")
            print("-" * 20)
            print("1. Ensure 'Wake on Magic Packet' is enabled in network adapter settings")
            print("2. If Wake-on-LAN isn't working, check if Fast Startup is disabled")
            print("3. Verify that your network adapter is listed in 'Devices that can wake the system'")
            print("4. In BIOS/UEFI settings, ensure:")
            print("   - Power On By PCI-E/PCI is enabled")
            print("   - Deep Sleep Control is disabled")
            print("   - EuP/ErP Ready is disabled")
            
            input("\nPress Enter to return to main menu...")

        except subprocess.CalledProcessError as e:
            print(f"\nError checking settings: {e}")
            input("\nPress Enter to continue...")
            return False
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            input("\nPress Enter to continue...")
            return False

        return True

    def check_wol_configuration(self):
        """Perform a comprehensive check of Wake-on-LAN configuration."""
        print("\n=== Wake-on-LAN Configuration Check ===\n")
        
        issues_found = []
        recommendations = []
        
        # Check Network Adapter Settings
        try:
            # Use PowerShell to get detailed network adapter settings
            ps_command = """
            Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {
                $adapter = $_
                $pm = Get-NetAdapterPowerManagement -Name $adapter.Name
                Write-Output "Adapter: $($adapter.Name)"
                Write-Output "WakeOnMagicPacket: $($pm.WakeOnMagicPacket)"
                Write-Output "WakeOnPattern: $($pm.WakeOnPattern)"
                Write-Output "DeviceSleepOnDisconnect: $($pm.DeviceSleepOnDisconnect)"
            }
            """
            result = subprocess.run(["powershell", "-Command", ps_command], 
                                 capture_output=True, text=True, check=True)
            
            print("Network Adapter Settings:")
            print(result.stdout)
            
            if "Disabled" in result.stdout:
                issues_found.append("Wake-on-LAN is disabled in network adapter settings")
                recommendations.append(
                    "Enable WoL in Device Manager:\n"
                    "1. Open Device Manager\n"
                    "2. Find your network adapter\n"
                    "3. Right-click → Properties\n"
                    "4. Go to 'Power Management' tab\n"
                    "5. Check 'Allow this device to wake the computer'\n"
                    "6. Check 'Only allow a magic packet to wake the computer'"
                )
        except Exception as e:
            print(f"Could not check network adapter settings: {e}")
        
        # Check if running on battery (for laptops)
        if hasattr(psutil, "sensors_battery"):
            try:
                battery = psutil.sensors_battery()
                if battery and not battery.power_plugged:
                    issues_found.append("Running on battery power")
                    recommendations.append(
                        "Connect your laptop to AC power. WoL might not work on battery power."
                    )
            except:
                pass
        
        # Check network connection type
        try:
            ps_command = """
            Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, MediaType
            """
            result = subprocess.run(["powershell", "-Command", ps_command], 
                                 capture_output=True, text=True, check=True)
            
            print("\nNetwork Connection Type:")
            print(result.stdout)
            
            if "Wi-Fi" in result.stdout or "Wireless" in result.stdout:
                issues_found.append("Using Wi-Fi connection")
                recommendations.append(
                    "Use a wired Ethernet connection. WoL is more reliable over Ethernet."
                )
        except Exception as e:
            print(f"Could not check network connection type: {e}")
        
        # Check Windows Fast Startup
        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Power"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                fast_startup = winreg.QueryValueEx(key, "HiberbootEnabled")[0]
                print("\nFast Startup:", "Enabled" if fast_startup else "Disabled")
                
                if fast_startup:
                    issues_found.append("Windows Fast Startup is enabled")
                    recommendations.append(
                        "Disable Fast Startup:\n"
                        "1. Open Control Panel\n"
                        "2. System and Security → Power Options\n"
                        "3. Choose what the power buttons do\n"
                        "4. Change settings that are currently unavailable\n"
                        "5. Uncheck 'Turn on fast startup'"
                    )
        except Exception as e:
            print(f"Could not check Fast Startup status: {e}")
        
        # Print issues and recommendations
        if issues_found:
            print("\n⚠️ Issues Found:")
            for i, issue in enumerate(issues_found, 1):
                print(f"{i}. {issue}")
            
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}\n")
        else:
            print("\n✅ No issues found! Your system appears to be properly configured for WoL.")
        
        print("\n📋 Additional Steps:")
        print("1. Check BIOS/UEFI Settings:")
        print("   - Enable 'Wake on LAN' or similar option")
        print("   - Enable 'Power On by PCI-E' or similar")
        print("   - Disable Deep Sleep mode")
        print("\n2. Router Configuration:")
        print("   - Enable UDP port forwarding for ports 7 and 9")
        print("   - Allow broadcast packets")
        print("   - If using port forwarding, forward to your PC's MAC address")
        
        input("\nPress Enter to continue...")

    def configure_wol_settings(self):
        """Configure all necessary Wake-on-LAN settings."""
        print("\nConfiguring Wake-on-LAN Settings...")
        print("=" * 50)
        
        try:
            # Enable WoL settings using PowerShell (requires admin privileges)
            wol_script = """
            # Get the network adapter
            $adapter = Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -and $_.MediaType -eq '802.3'}
            
            if ($adapter) {
                Write-Output "Configuring adapter: $($adapter.Name)"
                
                # Enable WoL in power management
                $devicePath = $adapter.PnPDeviceID
                $device = Get-PnpDevice | Where-Object { $_.InstanceId -eq $devicePath }
                
                # Registry path for the network adapter
                $adapterId = ($adapter.InterfaceDescription -replace '[^a-zA-Z0-9]', '_')
                $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}"
                
                Get-ChildItem $regPath | ForEach-Object {
                    $instancePath = $_.PSPath
                    if ((Get-ItemProperty -Path $instancePath).DriverDesc -eq $adapter.InterfaceDescription) {
                        # Enable WoL settings
                        Set-ItemProperty -Path $instancePath -Name "WolMagicPacket" -Value 1
                        Set-ItemProperty -Path $instancePath -Name "WakeOnMagicPacket" -Value 1
                        Set-ItemProperty -Path $instancePath -Name "PMARPOffload" -Value 1
                        Set-ItemProperty -Path $instancePath -Name "PMNSOffload" -Value 1
                        Set-ItemProperty -Path $instancePath -Name "WakeOnPattern" -Value 1
                        Write-Output "Enabled Wake-on-LAN registry settings"
                    }
                }
                
                # Enable device to wake computer
                $powerMgmt = Get-WmiObject MSPower_DeviceWakeEnable -Namespace root\\wmi | 
                    Where-Object { $_.InstanceName -match $adapterId }
                if ($powerMgmt) {
                    $powerMgmt.Enable = $true
                    $powerMgmt.Put()
                }
                
                # Disable Fast Startup
                $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power"
                Set-ItemProperty -Path $regPath -Name "HiberbootEnabled" -Value 0
                Write-Output "Disabled Fast Startup"
                
                # Configure Power Settings
                # Prevent sleep when plugged in
                powercfg /change standby-timeout-ac 0
                
                # Enable wake timers
                powercfg /setacvalueindex scheme_current sub_buttons pbuttonaction 0
                powercfg /setacvalueindex scheme_current sub_none wakefromlan 1
                powercfg /setactive scheme_current
                
                Write-Output "Power settings configured successfully"
            } else {
                Write-Output "No suitable network adapter found"
            }
            """
            
            print("\nAttempting to configure Wake-on-LAN settings (requires admin privileges)...")
            result = subprocess.run(
                ["powershell", "-Command", wol_script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("\nSuccessfully configured Wake-on-LAN settings!")
                print("\nSettings applied:")
                print("✓ Enabled Wake on Magic Packet")
                print("✓ Enabled Power Management ARP Offload")
                print("✓ Enabled Power Management NS Offload")
                print("✓ Enabled Wake on Pattern")
                print("✓ Disabled Fast Startup")
                print("✓ Configured Power Settings")
                
                print("\nAdditional steps required:")
                print("1. Restart your computer for changes to take effect")
                print("2. Enter BIOS/UEFI settings during restart and ensure:")
                print("   - Power On By PCI-E/PCI is enabled")
                print("   - Deep Sleep Control is disabled")
                print("   - EuP/ErP Ready is disabled")
            else:
                print("\nError configuring settings. Make sure to run as administrator.")
                print("Error details:")
                print(result.stderr)
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Make sure to run the program as administrator.")
            input("\nPress Enter to continue...")

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
