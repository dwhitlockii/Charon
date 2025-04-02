#!/usr/bin/env python3
"""
Quality of Service (QoS) Module for Charon Firewall

This module provides traffic shaping functionality to manage bandwidth and prioritize traffic.
It supports both Linux (using tc) and Windows (using PowerShell Network QoS Policies).
"""

import subprocess
import logging
import os
import platform
import tempfile
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger('charon.qos')

class QoS:
    """Quality of Service (QoS) manager for bandwidth control and traffic prioritization."""
    
    def __init__(self, interface: Optional[str] = None, total_bandwidth: int = 1000):
        """Initialize the QoS manager.
        
        Args:
            interface: The network interface to apply QoS to (auto-detected if None)
            total_bandwidth: The total bandwidth in Mbps for the interface
        """
        self.total_bandwidth = total_bandwidth  # in Mbps
        self.platform = platform.system()
        
        # Auto-detect interface if not provided
        if interface is None:
            self.interface = self._detect_default_interface()
        else:
            self.interface = interface
            
        self._check_permissions()
    
    def _detect_default_interface(self) -> str:
        """Detect the default network interface.
        
        Returns:
            str: Default interface name
        """
        try:
            if self.platform == 'Windows':
                # Get the default interface on Windows using PowerShell
                cmd = ["powershell", "-Command", 
                       "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 -ExpandProperty Name"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                interface = result.stdout.strip()
                if not interface:
                    interface = "Ethernet"  # Default fallback
            else:
                # Get the default interface on Linux
                cmd = ["ip", "route", "get", "8.8.8.8"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                interface = result.stdout.split("dev")[1].split()[0].strip()
                if not interface:
                    interface = "eth0"  # Default fallback
                    
            logger.info(f"Detected default network interface: {interface}")
            return interface
        except Exception as e:
            logger.warning(f"Failed to detect default interface: {e}")
            # Return a platform-specific default
            return "Ethernet" if self.platform == 'Windows' else "eth0"
    
    def _check_permissions(self) -> None:
        """Check if the current user has permissions to modify QoS settings."""
        try:
            if self.platform == 'Windows':
                # Check if running as Administrator on Windows
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                if not is_admin:
                    logger.warning("Not running as Administrator. QoS operations on Windows may fail.")
            else:
                # Check if running as root on Linux/Unix
                if os.geteuid() != 0:
                    logger.warning("Not running as root. QoS operations may fail.")
        except Exception as e:
            logger.warning(f"Could not check permissions: {e}")
    
    def apply_qos(self) -> bool:
        """Apply QoS settings based on the current platform.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.platform == 'Windows':
                return self._apply_windows_qos()
            else:
                return self.setup_default_profile()
        except Exception as e:
            logger.error(f"Failed to apply QoS: {e}")
            return False
    
    def _apply_windows_qos(self) -> bool:
        """Apply QoS settings on Windows using PowerShell.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Setting up Windows QoS policies...")
        
        try:
            # Calculate bandwidth values
            total_kbps = self.total_bandwidth * 1000
            high_rate = int(total_kbps * 0.2)     # 20% for high priority
            medium_rate = int(total_kbps * 0.3)   # 30% for medium priority
            low_rate = int(total_kbps * 0.1)      # 10% for low priority
            default_rate = int(total_kbps * 0.4)  # 40% for default traffic
            
            # Create a temporary script to set up Windows QoS policies
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as script_file:
                script_path = script_file.name
                
                # Write PowerShell script content
                script_file.write(f"""
# Remove existing Charon QoS policies
Get-NetQosPolicy | Where-Object {{ $_.Name -like "Charon*" }} | Remove-NetQosPolicy -Confirm:$false

# Create QoS policies for different traffic classes
New-NetQosPolicy -Name "Charon-High-SSH" -IPProtocol TCP -IPDstPort 22 -DSCPAction 46 -NetworkProfile All
New-NetQosPolicy -Name "Charon-High-VoIP" -IPProtocol UDP -IPDstPort 5060,5061 -DSCPAction 46 -NetworkProfile All
New-NetQosPolicy -Name "Charon-Medium-Web" -IPProtocol TCP -IPDstPort 80,443 -DSCPAction 34 -NetworkProfile All
New-NetQosPolicy -Name "Charon-Low-P2P" -IPProtocol TCP -IPDstPort 6881 -DSCPAction 8 -NetworkProfile All

# Set up bandwidth throttling if supported by the adapter
$interfaceName = "{self.interface}"

# Set DSCP priority mappings for QoS
# Priority class 1 (Highest)
New-NetQosDcbxSetting -Willing $true -Interface $interfaceName

Write-Output "Windows QoS policies have been configured."
""")
            
            # Execute the PowerShell script
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except Exception:
                pass  # Ignore cleanup errors
                
            logger.info("Windows QoS policies set up successfully")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to set up Windows QoS policies: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting up Windows QoS: {e}")
            return False
    
    def setup_tc_qdisc(self) -> bool:
        """Set up the traffic control queuing discipline (Linux only).
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.platform == 'Windows':
            logger.warning("setup_tc_qdisc is not supported on Windows")
            return False
            
        try:
            # Remove any existing qdisc
            cmd = ["tc", "qdisc", "del", "dev", self.interface, "root"]
            try:
                subprocess.run(cmd, check=False, capture_output=True)
            except subprocess.SubprocessError:
                pass  # Ignore errors from trying to delete a non-existent qdisc
            
            # Set up HTB qdisc
            cmd = [
                "tc", "qdisc", "add", "dev", self.interface, 
                "root", "handle", "1:", "htb", "default", "30"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Set up root class with total bandwidth
            rate_kbps = self.total_bandwidth * 1000  # Convert to Kbps
            cmd = [
                "tc", "class", "add", "dev", self.interface, 
                "parent", "1:", "classid", "1:1", "htb", 
                "rate", f"{rate_kbps}kbit", "ceil", f"{rate_kbps}kbit"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"TC qdisc set up successfully on {self.interface}")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to set up TC qdisc: {e}")
            return False
    
    def add_traffic_class(self, class_id: int, rate: int, ceiling: Optional[int] = None, 
                          parent_id: int = 1, priority: int = 0) -> bool:
        """Add a traffic class for bandwidth allocation (Linux only).
        
        Args:
            class_id: The class identifier (1-99)
            rate: Guaranteed bandwidth in Kbps
            ceiling: Maximum bandwidth in Kbps (defaults to rate if None)
            parent_id: Parent class ID
            priority: Priority level (0-7, lower is higher priority)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.platform == 'Windows':
            logger.warning("add_traffic_class is not supported on Windows")
            return False
            
        if ceiling is None:
            ceiling = rate
            
        try:
            cmd = [
                "tc", "class", "add", "dev", self.interface,
                "parent", f"1:{parent_id}", "classid", f"1:{class_id}", "htb",
                "rate", f"{rate}kbit", "ceil", f"{ceiling}kbit", "prio", str(priority)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Add SFQ qdisc to ensure fair queuing within the class
            cmd = [
                "tc", "qdisc", "add", "dev", self.interface,
                "parent", f"1:{class_id}", "handle", f"{class_id}:", "sfq", "perturb", "10"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Added traffic class 1:{class_id} with rate {rate}kbit, ceiling {ceiling}kbit")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to add traffic class: {e}")
            return False
    
    def add_filter(self, class_id: int, protocol: str = "ip", 
                   src_ip: Optional[str] = None, dst_ip: Optional[str] = None,
                   src_port: Optional[int] = None, dst_port: Optional[int] = None,
                   priority: int = 1) -> bool:
        """Add a filter to classify traffic into classes (Linux only).
        
        Args:
            class_id: The target class identifier
            protocol: IP protocol (tcp, udp, etc.)
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            priority: Filter priority (lower number = higher priority)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.platform == 'Windows':
            logger.warning("add_filter is not supported on Windows")
            return False
            
        try:
            # Start building the filter command
            cmd = [
                "tc", "filter", "add", "dev", self.interface,
                "protocol", "ip", "parent", "1:0", "prio", str(priority),
                "u32"
            ]
            
            # Build the match string based on provided parameters
            match = []
            
            if protocol in ["tcp", "udp"]:
                match.append(f"ip protocol {protocol}")
                
            if src_ip:
                match.append(f"match ip src {src_ip}")
                
            if dst_ip:
                match.append(f"match ip dst {dst_ip}")
                
            if src_port and protocol in ["tcp", "udp"]:
                match.append(f"match {protocol} sport {src_port} 0xffff")
                
            if dst_port and protocol in ["tcp", "udp"]:
                match.append(f"match {protocol} dport {dst_port} 0xffff")
            
            # Add match conditions and flowid
            cmd.extend(match)
            cmd.extend(["flowid", f"1:{class_id}"])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Added filter for class 1:{class_id} with {match}")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to add filter: {e}")
            return False

    def add_windows_policy(self, name: str, protocol: str = "TCP", 
                          dst_ports: Optional[List[int]] = None,
                          dscp_value: int = 0) -> bool:
        """Add a Windows QoS policy.
        
        Args:
            name: Policy name suffix (will be prefixed with Charon-)
            protocol: IP protocol (TCP, UDP)
            dst_ports: List of destination ports
            dscp_value: DSCP value (0-63) for traffic marking
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.platform != 'Windows':
            logger.warning("add_windows_policy is only supported on Windows")
            return False
            
        try:
            # Format ports as comma-separated string if provided
            ports_str = ""
            if dst_ports and len(dst_ports) > 0:
                ports_str = ",".join(map(str, dst_ports))
                ports_param = f"-IPDstPort {ports_str}"
            else:
                ports_param = ""
            
            # Create PowerShell command
            ps_cmd = (
                f"New-NetQosPolicy -Name 'Charon-{name}' "
                f"-IPProtocol {protocol} {ports_param} "
                f"-DSCPAction {dscp_value} -NetworkProfile All"
            )
            
            # Execute PowerShell command
            cmd = ["powershell", "-Command", ps_cmd]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info(f"Added Windows QoS policy 'Charon-{name}' for {protocol} ports {ports_str}")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to add Windows QoS policy: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding Windows QoS policy: {e}")
            return False
    
    def remove_all_policies(self) -> bool:
        """Remove all Charon QoS policies.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.platform == 'Windows':
                # Remove Windows QoS policies
                ps_cmd = "Get-NetQosPolicy | Where-Object { $_.Name -like 'Charon*' } | Remove-NetQosPolicy -Confirm:$false"
                cmd = ["powershell", "-Command", ps_cmd]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info("Removed all Windows QoS policies")
            else:
                # Remove Linux tc configuration
                cmd = ["tc", "qdisc", "del", "dev", self.interface, "root"]
                subprocess.run(cmd, check=True, capture_output=True)
                logger.info("Removed all Linux QoS settings")
                
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to remove QoS policies: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error removing QoS policies: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of QoS settings.
        
        Returns:
            Dict containing status information
        """
        status = {
            "platform": self.platform,
            "interface": self.interface,
            "total_bandwidth": self.total_bandwidth,
            "enabled": False,
            "policies": [],
            "error": None
        }
        
        try:
            if self.platform == 'Windows':
                # Get Windows QoS policies
                ps_cmd = "Get-NetQosPolicy | Where-Object { $_.Name -like 'Charon*' } | Select-Object Name, IPProtocol, IPDstPort, DSCPAction | ConvertTo-Json"
                cmd = ["powershell", "-Command", ps_cmd]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                # Check if we have any policies
                if result.stdout.strip() and "Charon" in result.stdout:
                    status["enabled"] = True
                    
                    # Try to parse JSON output
                    try:
                        import json
                        policies = json.loads(result.stdout)
                        # Handle single policy (not in array)
                        if isinstance(policies, dict):
                            policies = [policies]
                        status["policies"] = policies
                    except json.JSONDecodeError:
                        # If JSON parsing fails, just include raw output
                        status["policies"] = result.stdout.strip()
            else:
                # Get Linux QoS status
                cmd = ["tc", "qdisc", "show", "dev", self.interface]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                if "htb" in result.stdout:
                    status["enabled"] = True
                    
                    # Get classes
                    cmd = ["tc", "class", "show", "dev", self.interface]
                    class_result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    status["policies"] = class_result.stdout.strip().split("\n")
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Failed to get QoS status: {e}")
            
        return status
    
    def setup_default_profile(self) -> bool:
        """Set up a default QoS profile with common traffic classes.
        
        This creates a basic profile with classes for:
        - High priority (VoIP, SSH)
        - Medium priority (HTTP/HTTPS)
        - Low priority (P2P, bulk downloads)
        - Default traffic
        
        Returns:
            bool: True if successful, False otherwise
        """
        # For Windows, use the _apply_windows_qos method
        if self.platform == 'Windows':
            return self._apply_windows_qos()
            
        # Linux implementation
        success = True
        
        # Set up the qdisc first
        if not self.setup_tc_qdisc():
            return False
            
        # Calculate bandwidth percentages for each class
        total_kbps = self.total_bandwidth * 1000
        high_rate = int(total_kbps * 0.2)     # 20% guaranteed for high priority
        medium_rate = int(total_kbps * 0.3)   # 30% guaranteed for medium priority
        low_rate = int(total_kbps * 0.1)      # 10% guaranteed for low priority
        default_rate = int(total_kbps * 0.4)  # 40% guaranteed for default traffic
        
        # Set up traffic classes
        success &= self.add_traffic_class(10, high_rate, total_kbps, priority=0)    # High priority
        success &= self.add_traffic_class(20, medium_rate, total_kbps, priority=1)  # Medium priority
        success &= self.add_traffic_class(30, default_rate, total_kbps, priority=2)  # Default
        success &= self.add_traffic_class(40, low_rate, total_kbps, priority=3)     # Low priority
        
        # Add filters for high priority traffic
        success &= self.add_filter(10, protocol="tcp", dst_port=22)  # SSH
        success &= self.add_filter(10, protocol="udp", dst_port=5060)  # SIP
        success &= self.add_filter(10, protocol="udp", dst_port=5061)  # SIP Secure
        
        # Add filters for medium priority traffic
        success &= self.add_filter(20, protocol="tcp", dst_port=80)   # HTTP
        success &= self.add_filter(20, protocol="tcp", dst_port=443)  # HTTPS
        
        # Add filters for low priority traffic (P2P common ports as example)
        success &= self.add_filter(40, protocol="tcp", dst_port=6881)  # BitTorrent
        
        logger.info("Default QoS profile setup complete")
        return success 