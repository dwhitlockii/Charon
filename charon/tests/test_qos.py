#!/usr/bin/env python3
"""Tests for the QoS module with cross-platform support."""

import unittest
from unittest import mock
import platform
import subprocess
import sys
import os
import pytest
import tempfile
import json
from pathlib import Path
import functools

# Add the parent directory to the path to make imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import QoS directly from the core module
from src.core.qos import QoS

# Determine if we're on Windows for skipping tests
IS_WINDOWS = platform.system() == 'Windows'

def mock_linux_permissions(func):
    """Decorator to handle permissions mocking based on platform.
    
    This decorator will:
    - On Linux: mock os.geteuid to return 0 (root)
    - On Windows: skip trying to mock os.geteuid
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if IS_WINDOWS:
            # On Windows, we don't need to mock os.geteuid
            return func(self, *args, **kwargs)
        else:
            # On Linux, we mock os.geteuid
            with mock.patch('os.geteuid', return_value=0):
                return func(self, *args, **kwargs)
    return wrapper

class TestQoS(unittest.TestCase):
    """Tests for the QoS class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock platform detection for consistent testing
        self.platform_patcher = mock.patch('platform.system')
        self.mock_platform = self.platform_patcher.start()
        
        # Mock subprocess to prevent actual system calls
        self.subprocess_patcher = mock.patch('subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        
        # Configure subprocess.run mock to return successful CompletedProcess
        self.mock_subprocess.return_value = mock.Mock(
            stdout="mock output",
            stderr="",
            returncode=0
        )
        
    def tearDown(self):
        """Tear down test environment."""
        self.platform_patcher.stop()
        self.subprocess_patcher.stop()
    
    @mock_linux_permissions
    def test_init_with_interface(self):
        """Test QoS initialization with provided interface."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0", total_bandwidth=100)
        
        self.assertEqual(qos.interface, "eth0")
        self.assertEqual(qos.total_bandwidth, 100)
        self.assertEqual(qos.platform, 'Linux')
    
    @mock_linux_permissions
    def test_init_autodetect_interface_linux(self):
        """Test interface auto-detection on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        # Mock response for interface detection
        self.mock_subprocess.return_value = mock.Mock(
            stdout="1.2.3.4 via 192.168.1.1 dev wlan0 src 192.168.1.2",
            stderr="",
            returncode=0
        )
        
        qos = QoS(interface=None)
        
        self.assertEqual(qos.interface, "wlan0")
        self.assertEqual(qos.platform, 'Linux')
    
    def test_init_autodetect_interface_windows(self):
        """Test interface auto-detection on Windows."""
        self.mock_platform.return_value = 'Windows'
        
        # Mock response for interface detection
        self.mock_subprocess.return_value = mock.Mock(
            stdout="Wi-Fi",
            stderr="",
            returncode=0
        )
        
        # Mock ctypes for Windows admin check
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface=None)
            
            self.assertEqual(qos.interface, "Wi-Fi")
            self.assertEqual(qos.platform, 'Windows')
    
    @mock_linux_permissions
    def test_detect_default_interface_exception(self):
        """Test fallback when interface detection fails."""
        self.mock_platform.return_value = 'Linux'
        
        # Make subprocess.run raise an exception
        self.mock_subprocess.side_effect = subprocess.SubprocessError("Command failed")
        
        qos = QoS(interface=None)
        
        # Should fallback to default interface
        self.assertEqual(qos.interface, "eth0")
    
    @unittest.skipIf(IS_WINDOWS, "Linux-specific test")
    @mock.patch('os.geteuid', return_value=0)
    def test_check_permissions_linux_root(self, mock_geteuid):
        """Test permission check on Linux as root."""
        self.mock_platform.return_value = 'Linux'
        
        # No exception should be raised
        QoS(interface="eth0")
        
        # Check geteuid was called
        mock_geteuid.assert_called_once()
    
    @unittest.skipIf(IS_WINDOWS, "Linux-specific test")
    @mock.patch('os.geteuid', return_value=1000)
    def test_check_permissions_linux_non_root(self, mock_geteuid):
        """Test permission check on Linux as non-root."""
        self.mock_platform.return_value = 'Linux'
        
        # Should log a warning but not raise an exception
        with self.assertLogs('charon.qos', level='WARNING') as cm:
            QoS(interface="eth0")
            
        self.assertTrue(any("Not running as root" in msg for msg in cm.output))
    
    def test_check_permissions_windows_admin(self):
        """Test permission check on Windows as admin."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            # No exception should be raised
            QoS(interface="Ethernet")
    
    def test_check_permissions_windows_non_admin(self):
        """Test permission check on Windows as non-admin."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
            # Should log a warning but not raise an exception
            with self.assertLogs('charon.qos', level='WARNING') as cm:
                QoS(interface="Ethernet")
                
            self.assertTrue(any("Not running as Administrator" in msg for msg in cm.output))
    
    @mock_linux_permissions
    def test_apply_qos_linux(self):
        """Test apply_qos on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        # Mock setup_default_profile to isolate the test
        with mock.patch.object(QoS, 'setup_default_profile', return_value=True) as mock_setup:
            qos = QoS(interface="eth0")
            result = qos.apply_qos()
            
            self.assertTrue(result)
            mock_setup.assert_called_once()
    
    def test_apply_qos_windows(self):
        """Test apply_qos on Windows."""
        self.mock_platform.return_value = 'Windows'
        
        # Mock _apply_windows_qos to isolate the test
        with mock.patch.object(QoS, '_apply_windows_qos', return_value=True) as mock_apply, \
             mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            result = qos.apply_qos()
            
            self.assertTrue(result)
            mock_apply.assert_called_once()
    
    @mock_linux_permissions
    def test_apply_qos_exception(self):
        """Test apply_qos handling exceptions."""
        self.mock_platform.return_value = 'Linux'
        
        # Mock setup_default_profile to raise an exception
        with mock.patch.object(QoS, 'setup_default_profile', side_effect=Exception("Test error")):
            qos = QoS(interface="eth0")
            
            # Should log an error and return False
            with self.assertLogs('charon.qos', level='ERROR') as cm:
                result = qos.apply_qos()
                
            self.assertFalse(result)
            self.assertTrue(any("Failed to apply QoS" in msg for msg in cm.output))
    
    def test_apply_windows_qos(self):
        """Test Windows-specific QoS application."""
        self.mock_platform.return_value = 'Windows'
        
        # Mock tempfile.NamedTemporaryFile with a proper context manager replacement
        mock_tempfile = mock.MagicMock()
        mock_tempfile.name = "C:\\temp\\test_script.ps1"
        mock_tempfile.__enter__.return_value = mock_tempfile
        mock_tempfile.__exit__.return_value = None
        
        with mock.patch('tempfile.NamedTemporaryFile', return_value=mock_tempfile), \
             mock.patch('os.unlink') as mock_unlink, \
             mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            
            qos = QoS(interface="Ethernet")
            result = qos._apply_windows_qos()
            
            self.assertTrue(result)
            # Check that PowerShell was called with the script
            self.mock_subprocess.assert_called_with(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", mock_tempfile.name],
                check=True, capture_output=True, text=True
            )
            # Check that the temporary file was deleted
            mock_unlink.assert_called_with(mock_tempfile.name)
    
    @mock_linux_permissions
    def test_setup_tc_qdisc_linux(self):
        """Test TC qdisc setup on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0")
        result = qos.setup_tc_qdisc()
        
        self.assertTrue(result)
        # Check that tc commands were called
        self.assertEqual(self.mock_subprocess.call_count, 3)
    
    def test_setup_tc_qdisc_windows(self):
        """Test TC qdisc setup on Windows (should not be supported)."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            
            # Should log a warning and return False
            with self.assertLogs('charon.qos', level='WARNING') as cm:
                result = qos.setup_tc_qdisc()
                
            self.assertFalse(result)
            self.assertTrue(any("not supported on Windows" in msg for msg in cm.output))
    
    @mock_linux_permissions
    def test_add_traffic_class_linux(self):
        """Test adding a traffic class on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0")
        result = qos.add_traffic_class(10, 1000, 2000, priority=1)
        
        self.assertTrue(result)
        # Check that tc commands were called
        self.assertEqual(self.mock_subprocess.call_count, 2)
    
    def test_add_traffic_class_windows(self):
        """Test adding a traffic class on Windows (should not be supported)."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            
            # Should log a warning and return False
            with self.assertLogs('charon.qos', level='WARNING') as cm:
                result = qos.add_traffic_class(10, 1000)
                
            self.assertFalse(result)
            self.assertTrue(any("not supported on Windows" in msg for msg in cm.output))
    
    @mock_linux_permissions
    def test_add_filter_linux(self):
        """Test adding a filter on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0")
        result = qos.add_filter(10, protocol="tcp", dst_port=80)
        
        self.assertTrue(result)
        # Check that tc filter command was called
        self.mock_subprocess.assert_called()
    
    def test_add_filter_windows(self):
        """Test adding a filter on Windows (should not be supported)."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            
            # Should log a warning and return False
            with self.assertLogs('charon.qos', level='WARNING') as cm:
                result = qos.add_filter(10, protocol="tcp", dst_port=80)
                
            self.assertFalse(result)
            self.assertTrue(any("not supported on Windows" in msg for msg in cm.output))
    
    def test_add_windows_policy(self):
        """Test adding a Windows QoS policy."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            result = qos.add_windows_policy("Web", protocol="TCP", dst_ports=[80, 443], dscp_value=46)
            
            self.assertTrue(result)
            # Check that PowerShell command was called
            self.mock_subprocess.assert_called_with(
                ["powershell", "-Command", mock.ANY], 
                check=True, capture_output=True, text=True
            )
            
            # Verify command contains the expected parameters
            cmd = self.mock_subprocess.call_args[0][0][2]
            self.assertIn("Charon-Web", cmd)
            self.assertIn("TCP", cmd)
            self.assertIn("-IPDstPort 80,443", cmd)
            self.assertIn("-DSCPAction 46", cmd)
    
    @mock_linux_permissions
    def test_add_windows_policy_on_linux(self):
        """Test adding a Windows QoS policy on Linux (should not be supported)."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0")
        
        # Should log a warning and return False
        with self.assertLogs('charon.qos', level='WARNING') as cm:
            result = qos.add_windows_policy("Web", protocol="TCP", dst_ports=[80, 443])
            
        self.assertFalse(result)
        self.assertTrue(any("only supported on Windows" in msg for msg in cm.output))
    
    @mock_linux_permissions
    def test_remove_all_policies_linux(self):
        """Test removing all QoS policies on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        qos = QoS(interface="eth0")
        result = qos.remove_all_policies()
        
        self.assertTrue(result)
        # Check that tc command was called
        self.mock_subprocess.assert_called_with(
            ["tc", "qdisc", "del", "dev", "eth0", "root"],
            check=True, capture_output=True
        )
    
    def test_remove_all_policies_windows(self):
        """Test removing all QoS policies on Windows."""
        self.mock_platform.return_value = 'Windows'
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            result = qos.remove_all_policies()
            
            self.assertTrue(result)
            # Check that PowerShell command was called
            self.mock_subprocess.assert_called_with(
                ["powershell", "-Command", mock.ANY],
                check=True, capture_output=True, text=True
            )
            
            # Verify command contains the expected parameters
            cmd = self.mock_subprocess.call_args[0][0][2]
            self.assertIn("Get-NetQosPolicy", cmd)
            self.assertIn("Where-Object", cmd)
            self.assertIn("Remove-NetQosPolicy", cmd)
    
    @mock_linux_permissions
    def test_get_status_linux(self):
        """Test getting QoS status on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        # Mock responses for status commands
        qdisc_response = mock.Mock(stdout="qdisc htb 1: root", stderr="", returncode=0)
        class_response = mock.Mock(stdout="class htb 1:1 root\nclass htb 1:10 parent 1:1", stderr="", returncode=0)
        
        self.mock_subprocess.side_effect = [qdisc_response, class_response]
        
        qos = QoS(interface="eth0")
        status = qos.get_status()
        
        self.assertEqual(status["platform"], "Linux")
        self.assertEqual(status["interface"], "eth0")
        self.assertTrue(status["enabled"])
        self.assertEqual(status["policies"], ["class htb 1:1 root", "class htb 1:10 parent 1:1"])
    
    def test_get_status_windows(self):
        """Test getting QoS status on Windows."""
        self.mock_platform.return_value = 'Windows'
        
        # Mock response for PowerShell command
        ps_response = mock.Mock(
            stdout='[{"Name":"Charon-High-SSH","IPProtocol":"TCP","IPDstPort":"22","DSCPAction":"46"}]',
            stderr="",
            returncode=0
        )
        
        self.mock_subprocess.return_value = ps_response
        
        with mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            qos = QoS(interface="Ethernet")
            status = qos.get_status()
            
            self.assertEqual(status["platform"], "Windows")
            self.assertEqual(status["interface"], "Ethernet")
            self.assertTrue(status["enabled"])
            self.assertEqual(len(status["policies"]), 1)
            self.assertEqual(status["policies"][0]["Name"], "Charon-High-SSH")
            self.assertEqual(status["policies"][0]["IPProtocol"], "TCP")
            self.assertEqual(status["policies"][0]["IPDstPort"], "22")
            self.assertEqual(status["policies"][0]["DSCPAction"], "46")
    
    @mock_linux_permissions
    def test_get_status_error(self):
        """Test error handling in get_status."""
        self.mock_platform.return_value = 'Linux'
        
        # Make subprocess.run raise an exception
        self.mock_subprocess.side_effect = Exception("Test error")
        
        qos = QoS(interface="eth0")
        
        # Should log an error and return status with error
        with self.assertLogs('charon.qos', level='ERROR') as cm:
            status = qos.get_status()
            
        self.assertEqual(status["platform"], "Linux")
        self.assertEqual(status["interface"], "eth0")
        self.assertFalse(status["enabled"])
        self.assertEqual(status["error"], "Test error")
        self.assertTrue(any("Failed to get QoS status" in msg for msg in cm.output))
    
    @mock_linux_permissions
    def test_setup_default_profile_linux(self):
        """Test setting up default profile on Linux."""
        self.mock_platform.return_value = 'Linux'
        
        # Mock setup_tc_qdisc and other methods to isolate the test
        with mock.patch.object(QoS, 'setup_tc_qdisc', return_value=True) as mock_qdisc, \
             mock.patch.object(QoS, 'add_traffic_class', return_value=True) as mock_class, \
             mock.patch.object(QoS, 'add_filter', return_value=True) as mock_filter:
            
            qos = QoS(interface="eth0")
            result = qos.setup_default_profile()
            
            self.assertTrue(result)
            mock_qdisc.assert_called_once()
            self.assertEqual(mock_class.call_count, 4)  # 4 traffic classes
            self.assertEqual(mock_filter.call_count, 6)  # 6 filters
    
    def test_setup_default_profile_windows(self):
        """Test setting up default profile on Windows."""
        self.mock_platform.return_value = 'Windows'
        
        # Mock _apply_windows_qos to isolate the test
        with mock.patch.object(QoS, '_apply_windows_qos', return_value=True) as mock_apply, \
             mock.patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            
            qos = QoS(interface="Ethernet")
            result = qos.setup_default_profile()
            
            self.assertTrue(result)
            mock_apply.assert_called_once()

if __name__ == '__main__':
    unittest.main() 