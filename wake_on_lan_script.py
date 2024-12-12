import json
import platform
import socket
import subprocess
import uuid
import winreg

import netifaces
import psutil

def get_comprehensive_network_info():
    """
    Retrieve detailed network and system information for Wake-on-LAN configuration.
    """
    network_info = {
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "computer_name": platform.node()
        },
        "network_interfaces": []
    }

    # Detect network interfaces
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        try:
            # MAC Address
            mac_info = netifaces.ifaddresses(interface).get(netifaces.AF_LINK, [{}])[0]
            mac_address = mac_info.get('addr', 'N/A')
            
            # IPv4 Details
            ipv4_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            ipv4 = ipv4_info[0]['addr'] if ipv4_info else 'N/A'
            
            # Better interface status detection
            is_up = False
            try:
                # Check if interface has an IP address
                is_up = bool(ipv4_info and ipv4 != 'N/A')
                if not is_up:
                    # Double check with psutil
                    stats = psutil.net_if_stats()
                    is_up = interface in stats and stats[interface].isup
            except Exception:
                is_up = False

            # Detailed interface information
            interface_details = {
                "name": interface,
                "mac_address": mac_address,
                "ipv4_address": ipv4,
                "is_up": is_up
            }

            # Additional WoL-specific checks for Windows
            if platform.system() == 'Windows':
                interface_details.update(check_windows_wol_support(interface))

            network_info["network_interfaces"].append(interface_details)
        
        except Exception as e:
            print(f"Error processing interface {interface}: {e}")

    return network_info

def check_windows_wol_support(interface):
    """
    Check Wake-on-LAN support for Windows network interfaces.
    """
    wol_support = {
        "wol_support": False,
        "wol_config_notes": []
    }

    try:
        # Check registry for network adapter WoL settings
        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                net_cfg_instance_id = winreg.QueryValueEx(subkey, "NetCfgInstanceId")[0]
                                if net_cfg_instance_id == interface:
                                    # Check WoL-related registry entries
                                    wol_support["wol_config_notes"].append("Network adapter found in registry")
                                    break
                            except FileNotFoundError:
                                continue
                    except Exception:
                        continue
        except Exception as reg_error:
            wol_support["wol_config_notes"].append(f"Registry check failed: {reg_error}")

        # Run netsh command to get detailed adapter information
        try:
            netsh_output = subprocess.check_output(
                f'netsh interface ipv4 show config name="{interface}"', 
                shell=True, 
                stderr=subprocess.STDOUT, 
                universal_newlines=True
            )
            wol_support["wol_config_notes"].append("Netsh configuration retrieved")
        except subprocess.CalledProcessError as netsh_error:
            wol_support["wol_config_notes"].append(f"Netsh error: {netsh_error}")

    except Exception as e:
        wol_support["wol_config_notes"].append(f"Unexpected error: {e}")

    # Determine basic WoL support
    wol_support["wol_support"] = len(wol_support["wol_config_notes"]) > 0

    return wol_support

def generate_wol_configuration_file(network_info):
    """
    Generate a comprehensive configuration file for Wake-on-LAN.
    """
    config_file = 'wol_config.json'
    
    try:
        with open(config_file, 'w') as f:
            json.dump(network_info, f, indent=4)
        
        print(f"Wake-on-LAN configuration saved to {config_file}")
        return config_file
    except Exception as e:
        print(f"Failed to generate configuration file: {e}")
        return None

def send_wol_packet(mac_address, broadcast="255.255.255.255", port=9):
    """
    Send a Wake-on-LAN packet to the specified MAC address.
    
    Args:
        mac_address (str): The MAC address of the target machine
        broadcast (str): The broadcast address to use (default: 255.255.255.255)
        port (int): The port to send the magic packet to (default: 9)
    """
    print(f"\n=== Wake-on-LAN Packet Details ===")
    print(f"Target MAC: {mac_address}")
    print(f"Broadcast Address: {broadcast}")
    print(f"Port: {port}")
    
    try:
        # Remove any separators from MAC address and convert to bytes
        mac_bytes = bytes.fromhex(mac_address.replace(':', '').replace('-', ''))
        
        # Create magic packet: 6 bytes of 0xFF followed by MAC address repeated 16 times
        magic_packet = b'\xFF' * 6 + mac_bytes * 16
        
        print(f"Magic Packet Size: {len(magic_packet)} bytes")
        print("Magic Packet Structure:")
        print(f"- Synchronization Stream: {' '.join([f'{b:02x}' for b in magic_packet[:6]])}")
        print(f"- Target MAC (First Copy): {' '.join([f'{b:02x}' for b in magic_packet[6:12]])}")
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        print("\nSending packet...")
        # Send magic packet
        sock.sendto(magic_packet, (broadcast, port))
        print(f"✓ Packet sent successfully to {broadcast}:{port}")
        
        # Try to set up a receiving socket to check for any response
        try:
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_socket.settimeout(2)  # 2 second timeout
            recv_socket.bind(('', port))
            print("\nListening for response...")
            
            try:
                data, addr = recv_socket.recvfrom(1024)
                print(f"← Received response from {addr}")
                print(f"Response data: {data.hex()}")
            except socket.timeout:
                print("× No response received (timeout)")
            
            recv_socket.close()
        except Exception as e:
            print(f"Note: Could not set up response monitoring: {e}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"\n× Error sending WoL packet: {e}")
        return False

def main():
    # Retrieve network information
    network_info = get_comprehensive_network_info()
    
    # Print detailed network information
    print(json.dumps(network_info, indent=2))
    
    # Generate configuration file
    config_file = generate_wol_configuration_file(network_info)

    # Provide summary and guidance
    print("\n🌐 Wake-on-LAN Configuration Guide:")
    print("1. Ensure your PC is completely shut down (not in sleep mode)")
    print("2. Verify network cable is connected")
    print("3. Check BIOS/UEFI settings for Wake-on-LAN support")
    
    # Highlight potential WoL-capable interfaces
    print("\n🖧 Potential WoL Interfaces:")
    for iface in network_info.get("network_interfaces", []):
        status = "✅ Potentially WoL-Ready" if iface.get("is_up", False) else "❌ Not Ready"
        print(f"Interface: {iface.get('name', 'Unknown')}")
        print(f"  MAC Address: {iface.get('mac_address', 'N/A')}")
        print(f"  IP Address: {iface.get('ipv4_address', 'N/A')}")
        print(f"  Status: {status}\n")

if __name__ == "__main__":
    network_info = get_comprehensive_network_info()
    # Save network info to JSON for the web app
    with open("wol_config.json", "w") as f:
        json.dump(network_info, f, indent=4)

    # Example: Send WoL packet (replace with your target MAC and broadcast address)
    target_mac = "2c:4d:54:cf:f7:c1"  # Replace with the correct MAC address
    send_wol_packet(target_mac, "192.168.3.255") # Replace with your broadcast address if needed
