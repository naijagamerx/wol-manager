# Wake-on-LAN Manager

A comprehensive Wake-on-LAN (WoL) management tool that allows you to remotely wake computers, monitor network traffic, and configure WoL settings. Developed in collaboration with [Demo Homex](https://demohomex.com).

## Features

- 🖥️ **Complete WoL Management**
  - Send Wake-on-LAN magic packets
  - Monitor incoming WoL packets
  - Configure network adapter WoL settings
  - Check and verify BIOS/UEFI settings

- 🌐 **Network Tools**
  - Display detailed network information
  - Monitor network interfaces
  - Web interface for remote access
  - Real-time packet monitoring

- ⚙️ **System Configuration**
  - Automatic WoL settings configuration
  - BIOS/UEFI settings checker
  - Power management optimization
  - Fast Startup control

## Requirements

- Windows OS
- Python 3.8 or higher
- Administrator privileges (for configuration)
- Network adapter with Wake-on-LAN support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wakeonlan.git
cd wakeonlan
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Program

Run with administrator privileges for full functionality:
```bash
python wol_manager.py
```

### Main Menu Options

1. **Show Network Information**
   - Display detailed information about network interfaces

2. **Enable Wake-on-LAN**
   - Configure network adapter for WoL support

3. **Send Wake-on-LAN Packet**
   - Send magic packets to wake remote computers

4. **Start Packet Monitor**
   - Monitor incoming WoL packets

5. **Start Web Interface**
   - Access the tool through a web browser

6. **Configure BIOS/UEFI Settings Guide**
   - Step-by-step guide for BIOS configuration

7. **Check WoL Configuration**
   - Verify current WoL settings

8. **Check BIOS Settings**
   - Display current BIOS and power settings

9. **Configure All WoL Settings**
   - Automatically configure all necessary settings
   - Requires administrator privileges

### Configuring Wake-on-LAN

For WoL to work properly, ensure:

1. **Network Adapter Settings**
   - Wake on Magic Packet enabled
   - Power Management settings configured
   - ARP and NS Offload enabled

2. **BIOS/UEFI Settings**
   - Power On By PCI-E/PCI enabled
   - Deep Sleep Control disabled
   - EuP/ErP Ready disabled

3. **Windows Settings**
   - Fast Startup disabled
   - Network adapter power management configured
   - Wake timers enabled

## Troubleshooting

### Common Issues

1. **Computer won't wake up**
   - Verify BIOS settings
   - Check network adapter configuration
   - Ensure Fast Startup is disabled

2. **Permission errors**
   - Run the program as administrator
   - Check Windows security settings

3. **Network adapter not found**
   - Verify adapter supports WoL
   - Update network drivers
   - Check physical connection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Developed by [Demo Homex](https://demohomex.com)
- Wake-on-LAN implementation based on standard protocols
- Special thanks to the open-source community

## Contact

For support or inquiries:
- Website: [https://demohomex.com](https://demohomex.com)
- GitHub Issues: [Report a bug](https://github.com/yourusername/wakeonlan/issues)
