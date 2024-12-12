# Wake-on-LAN Manager

<div align="center">

![Wake-on-LAN Manager](https://img.shields.io/badge/Wake--on--LAN-Manager-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

## 🌟 About

Wake-on-LAN Manager is a comprehensive tool for managing and monitoring Wake-on-LAN functionality on your network. It provides both a command-line interface and a web interface for sending WoL packets, monitoring network traffic, and configuring WoL settings.

Developed in collaboration with [Demo Homex](https://demohomex.com), this tool aims to make Wake-on-LAN management accessible and efficient.

## ✨ Features

- 📱 Web interface for remote access
- 🖥️ Terminal-based menu interface
- 📡 Real-time WoL packet monitoring
- 🔧 Network adapter configuration
- 📊 Comprehensive network information display
- 🚀 Easy BIOS/UEFI setup guide

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/naijagamerx/wol-manager.git
cd wol-manager
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

Run the main script:
```bash
python wol_manager.py
```

### Menu Options

1. **Show Network Information**
   - Display detailed information about network interfaces
   - View MAC addresses, IP addresses, and WoL support status

2. **Enable Wake-on-LAN**
   - Configure network adapters for WoL support
   - Automatic Windows registry configuration

3. **Send Wake-on-LAN Packet**
   - Send magic packets to wake remote machines
   - Support for custom broadcast addresses

4. **Start Packet Monitor**
   - Monitor incoming WoL packets
   - Filter by MAC address
   - Real-time packet analysis

5. **Start Web Interface**
   - Access WoL controls from any device
   - Mobile-friendly interface
   - Real-time status updates

6. **BIOS/UEFI Setup Guide**
   - Step-by-step configuration guide
   - Vendor-specific instructions
   - Troubleshooting tips

## 🛠️ Configuration

### Wake-on-LAN Settings

1. **BIOS/UEFI Configuration**
   - Enable "Wake-on-LAN" or "Power On by PCI-E"
   - Enable "Network Stack"
   - Save changes and restart

2. **Windows Configuration**
   - Run as administrator
   - Use the built-in configuration tool (Option 2)
   - Verify settings in Device Manager

### Network Requirements

- Ethernet connection (WoL may not work over Wi-Fi)
- Router must allow broadcast packets
- Target PC must be properly shut down (not hibernated)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- Developed in collaboration with [Demo Homex](https://demohomex.com)
- Special thanks to the open-source community

## 📞 Support

For support:
- Visit [Demo Homex](https://demohomex.com)
- Email: info@demohomex.com
- Open an issue on [GitHub](https://github.com/naijagamerx/wol-manager/issues)
- Author: [naijagamerx](https://github.com/naijagamerx)
