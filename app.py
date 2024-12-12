from flask import Flask, render_template, jsonify, request
import json
import io
import sys
from contextlib import redirect_stdout
from wake_on_lan_script import send_wol_packet, get_comprehensive_network_info

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Get network information
        network_info = get_comprehensive_network_info()
        return render_template('index.html', network_info=network_info)
    except Exception as e:
        return str(e), 500

@app.route('/wake', methods=['POST'])
def wake():
    try:
        data = request.json
        mac_address = data.get('mac_address')
        broadcast = data.get('broadcast', '255.255.255.255')
        
        if not mac_address:
            return jsonify({'error': 'MAC address is required'}), 400
            
        # Capture the terminal output
        output = io.StringIO()
        with redirect_stdout(output):
            success = send_wol_packet(mac_address, broadcast)
        
        terminal_output = output.getvalue()
        
        if success:
            return jsonify({
                'message': 'Wake-on-LAN packet sent successfully',
                'terminal_output': terminal_output
            })
        else:
            return jsonify({
                'error': 'Failed to send Wake-on-LAN packet',
                'terminal_output': terminal_output
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
