from WAKEONLAN.wake_on_lan_script import get_comprehensive_network_info
from WAKEONLAN.wake_on_lan_script import main, get_comprehensive_network_info, generate_wol_configuration_file
from io import StringIO
from unittest.mock import patch, MagicMock
from unittest.mock import patch, mock_open
import json
import netifaces
import platform
import psutil
import pytest
import sys

class TestWakeOnLanScript:

    def test_get_comprehensive_network_info_windows(self):
        """
        Test get_comprehensive_network_info function for Windows platform
        """
        with patch('platform.system', return_value='Windows'), \
             patch('platform.version', return_value='10.0.19041'), \
             patch('platform.node', return_value='TestPC'), \
             patch('netifaces.interfaces', return_value=['eth0']), \
             patch('netifaces.ifaddresses') as mock_ifaddresses, \
             patch('psutil.net_if_stats') as mock_net_if_stats, \
             patch('WAKEONLAN.wake_on_lan_script.check_windows_wol_support', return_value={'wol_support': True, 'wol_config_notes': ['Test note']}):

            mock_ifaddresses.return_value = {
                netifaces.AF_LINK: [{'addr': '00:11:22:33:44:55'}],
                netifaces.AF_INET: [{'addr': '192.168.1.100'}]
            }
            mock_net_if_stats.return_value = {'eth0': MagicMock(isup=True)}

            result = get_comprehensive_network_info()

            assert result['system']['os'] == 'Windows'
            assert result['system']['os_version'] == '10.0.19041'
            assert result['system']['computer_name'] == 'TestPC'
            assert len(result['network_interfaces']) == 1
            assert result['network_interfaces'][0]['name'] == 'eth0'
            assert result['network_interfaces'][0]['mac_address'] == '00:11:22:33:44:55'
            assert result['network_interfaces'][0]['ipv4_address'] == '192.168.1.100'
            assert result['network_interfaces'][0]['is_up'] == True
            assert result['network_interfaces'][0]['wol_support'] == True
            assert result['network_interfaces'][0]['wol_config_notes'] == ['Test note']

    @patch('WAKEONLAN.wake_on_lan_script.get_comprehensive_network_info')
    @patch('WAKEONLAN.wake_on_lan_script.generate_wol_configuration_file')
    def test_main_config_file_generation_failure(self, mock_generate_config, mock_get_info):
        """
        Test main function when config file generation fails
        """
        mock_get_info.return_value = {"network_interfaces": []}
        mock_generate_config.return_value = None

        # Redirect stdout to capture print statements
        captured_output = StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        assert "Wake-on-LAN Configuration Guide:" in output
        assert "Potential WoL Interfaces:" in output

    @patch('WAKEONLAN.wake_on_lan_script.get_comprehensive_network_info')
    @patch('WAKEONLAN.wake_on_lan_script.generate_wol_configuration_file')
    def test_main_empty_network_info(self, mock_generate_config, mock_get_info):
        """
        Test main function when network info is empty
        """
        mock_get_info.return_value = {}
        mock_generate_config.return_value = 'wol_config.json'

        # Redirect stdout to capture print statements
        captured_output = StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        assert "Wake-on-LAN Configuration Guide:" in output
        assert "Potential WoL Interfaces:" in output
        assert "Interface: Unknown" not in output

    @patch('WAKEONLAN.wake_on_lan_script.get_comprehensive_network_info')
    @patch('WAKEONLAN.wake_on_lan_script.generate_wol_configuration_file')
    def test_main_invalid_interface_data(self, mock_generate_config, mock_get_info):
        """
        Test main function with invalid interface data
        """
        mock_get_info.return_value = {
            "network_interfaces": [
                {"name": "eth0"},  # Missing other required fields
                {"mac_address": "00:11:22:33:44:55"},  # Missing name and other fields
                {}  # Empty interface data
            ]
        }
        mock_generate_config.return_value = 'wol_config.json'

        # Redirect stdout to capture print statements
        captured_output = StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        assert "Wake-on-LAN Configuration Guide:" in output
        assert "Potential WoL Interfaces:" in output
        assert "Interface: eth0" in output
        assert "Interface: Unknown" in output
        assert "MAC Address: N/A" in output
        assert "IP Address: N/A" in output
        assert "Status: ❌ Not Ready" in output

    @patch('WAKEONLAN.wake_on_lan_script.get_comprehensive_network_info')
    @patch('WAKEONLAN.wake_on_lan_script.generate_wol_configuration_file')
    def test_main_invalid_network_info(self, mock_generate_config, mock_get_info):
        """
        Test main function when network info is invalid
        """
        mock_get_info.return_value = {"invalid_key": "invalid_value"}
        mock_generate_config.return_value = 'wol_config.json'

        # Redirect stdout to capture print statements
        captured_output = StringIO()
        sys.stdout = captured_output

        main()

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        assert "Wake-on-LAN Configuration Guide:" in output
        assert "Potential WoL Interfaces:" in output
        assert "Interface: Unknown" not in output

    @patch('WAKEONLAN.wake_on_lan_script.get_comprehensive_network_info')
    @patch('WAKEONLAN.wake_on_lan_script.generate_wol_configuration_file')
    def test_main_network_info_exception(self, mock_generate_config, mock_get_info):
        """
        Test main function when get_comprehensive_network_info raises an exception
        """
        mock_get_info.side_effect = Exception("Network info error")
        mock_generate_config.return_value = 'wol_config.json'

        with pytest.raises(Exception):
            main()