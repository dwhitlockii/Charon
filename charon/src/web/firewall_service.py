#!/usr/bin/env python3
"""
Firewall Service Module for Charon Web UI

This module provides services to connect the web UI with the firewall functionality.
"""

import logging
import os
import subprocess
from typing import Dict, List, Optional, Any, Tuple

from ..db.database import Database
from ..core.packet_filter import PacketFilter
from ..core.content_filter import ContentFilter
from ..core.qos import QoS
from ..scheduler.firewall_scheduler import FirewallScheduler
from ..plugins.plugin_manager import PluginManager

logger = logging.getLogger('charon.web.service')

class FirewallService:
    """Service for integrating the web UI with firewall functionality."""
    
    def __init__(self):
        """Initialize the firewall service."""
        self.db = None
        self.packet_filter = None
        self.content_filter = None
        self.qos = None
        self.scheduler = None
        self.plugin_manager = None
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all firewall components."""
        try:
            # Initialize database
            self.db = Database()
            success = self.db.connect()
            if not success:
                logger.error("Failed to connect to database")
            
            # Initialize packet filter
            self.packet_filter = PacketFilter()
            
            # Initialize content filter
            content_filter_enabled = os.environ.get('CHARON_CONTENT_FILTER_ENABLED', 'true').lower() == 'true'
            self.content_filter = ContentFilter(enabled=content_filter_enabled)
            
            # Initialize QoS
            qos_enabled = os.environ.get('CHARON_QOS_ENABLED', 'false').lower() == 'true'
            qos_default_bandwidth = os.environ.get('CHARON_QOS_DEFAULT_BANDWIDTH', '10Mbit')
            self.qos = QoS(enabled=qos_enabled, default_bandwidth=qos_default_bandwidth)
            
            # Initialize scheduler
            self.scheduler = FirewallScheduler(db=self.db)
            
            # Initialize plugin manager
            plugins_dir = os.environ.get('CHARON_PLUGINS_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins'))
            self.plugin_manager = PluginManager(plugins_dir=plugins_dir)
            
            logger.info("Firewall service components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize firewall service: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the firewall.
        
        Returns:
            Dict with status information
        """
        try:
            # Platform-specific commands for getting system information
            platform = os.environ.get('CHARON_PLATFORM', 'linux').lower()
            
            if platform == 'windows':
                # Windows-specific commands
                uptime = self._get_windows_uptime()
                connections = self._get_windows_connections()
                firewall_active = self._is_windows_firewall_active()
            else:
                # Linux/Unix commands
                uptime = self._get_linux_uptime()
                connections = self._get_linux_connections()
                firewall_active = self._is_linux_firewall_active()
            
            # Get active rules count
            rules_active = 0
            if self.db:
                rules = self.db.get_rules({"enabled": True})
                rules_active = len(rules)
            
            return {
                'status': 'active' if firewall_active else 'inactive',
                'uptime': uptime,
                'rules_active': rules_active,
                'connections': connections,
                'plugins_loaded': len(self.plugin_manager.plugins) if self.plugin_manager else 0
            }
        except Exception as e:
            logger.error(f"Failed to get firewall status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_linux_uptime(self) -> str:
        """Get system uptime on Linux."""
        try:
            uptime_cmd = ["uptime", "-p"]
            uptime_result = subprocess.run(uptime_cmd, capture_output=True, text=True, check=True)
            return uptime_result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get Linux uptime: {e}")
            return "Unknown"
    
    def _get_windows_uptime(self) -> str:
        """Get system uptime on Windows."""
        try:
            uptime_cmd = ["powershell", "-Command", "(Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime"]
            uptime_result = subprocess.run(uptime_cmd, capture_output=True, text=True, check=True)
            boot_time = uptime_result.stdout.strip()
            # Calculate uptime from boot time
            import datetime
            boot_time_dt = datetime.datetime.strptime(boot_time, "%Y%m%d%H%M%S.%f%z")
            uptime_seconds = (datetime.datetime.now(datetime.timezone.utc) - boot_time_dt).total_seconds()
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"up {int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
            elif hours > 0:
                return f"up {int(hours)} hours, {int(minutes)} minutes"
            else:
                return f"up {int(minutes)} minutes"
        except Exception as e:
            logger.error(f"Failed to get Windows uptime: {e}")
            return "Unknown"
    
    def _get_linux_connections(self) -> int:
        """Get active connections count on Linux."""
        try:
            conn_cmd = ["ss", "-tn", "state", "established"]
            conn_result = subprocess.run(conn_cmd, capture_output=True, text=True, check=True)
            return len(conn_result.stdout.strip().split('\n')) - 1  # Subtract header line
        except Exception as e:
            logger.error(f"Failed to get Linux connections: {e}")
            return 0
    
    def _get_windows_connections(self) -> int:
        """Get active connections count on Windows."""
        try:
            conn_cmd = ["powershell", "-Command", "Get-NetTCPConnection -State Established | Measure-Object | Select-Object -ExpandProperty Count"]
            conn_result = subprocess.run(conn_cmd, capture_output=True, text=True, check=True)
            return int(conn_result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get Windows connections: {e}")
            return 0
    
    def _is_linux_firewall_active(self) -> bool:
        """Check if the firewall is active on Linux."""
        try:
            firewall_tables = os.environ.get('CHARON_FIREWALL_TABLES', 'charon').split(',')
            active_cmd = ["nft", "list", "tables"]
            active_result = subprocess.run(active_cmd, capture_output=True, text=True, check=True)
            
            for table in firewall_tables:
                if table.strip() in active_result.stdout:
                    return True
            return False
        except subprocess.SubprocessError:
            logger.error("Failed to check Linux firewall status")
            return False
    
    def _is_windows_firewall_active(self) -> bool:
        """Check if the firewall is active on Windows."""
        try:
            check_cmd = ["powershell", "-Command", "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
            
            # If any profile is enabled, consider firewall active
            for line in check_result.stdout.strip().split('\n'):
                if line.strip().lower() == 'true':
                    return True
            return False
        except subprocess.SubprocessError:
            logger.error("Failed to check Windows firewall status")
            return False
    
    def get_rules(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get firewall rules.
        
        Args:
            filter_criteria: Optional criteria to filter rules by
            
        Returns:
            List of rule dictionaries
        """
        if self.db:
            return self.db.get_rules(filter_criteria)
        else:
            # Fall back to direct retrieval if no database is available
            try:
                cmd = ["nft", "list", "table", "inet", "charon"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Parse the output to extract rules
                # This is a simplified example - in practice you'd need a more robust parser
                rules = []
                for line in result.stdout.strip().split('\n'):
                    if 'add rule' in line:
                        rule = {
                            'id': len(rules) + 1,
                            'chain': line.split('chain')[1].split()[0] if 'chain' in line else '',
                            'action': 'accept' if 'accept' in line else 'drop' if 'drop' in line else 'unknown',
                            'enabled': True
                        }
                        rules.append(rule)
                
                return rules
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to get firewall rules: {e}")
                return []
    
    def get_logs(self, limit: int = 100, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get firewall logs.
        
        Args:
            limit: Maximum number of logs to return
            filter_criteria: Optional criteria to filter logs by
            
        Returns:
            List of log dictionaries
        """
        if self.db:
            return self.db.get_logs(limit, filter_criteria)
        else:
            # Fall back to reading system logs if no database is available
            try:
                cmd = ["journalctl", "-u", "nftables", "-n", str(limit)]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Parse the output to extract logs
                # This is a simplified example - in practice you'd need a more robust parser
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if 'IN=' in line:  # Firewall log entries typically contain this
                        parts = line.split()
                        timestamp = ' '.join(parts[0:3])
                        src_ip = next((p.split('=')[1] for p in parts if p.startswith('SRC=')), '')
                        dst_ip = next((p.split('=')[1] for p in parts if p.startswith('DST=')), '')
                        
                        log = {
                            'timestamp': timestamp,
                            'src_ip': src_ip,
                            'dst_ip': dst_ip,
                            'action': 'drop'  # Assuming logged packets are dropped
                        }
                        logs.append(log)
                
                return logs
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to get firewall logs: {e}")
                return []
    
    def add_rule(self, rule_data: Dict[str, Any]) -> Optional[int]:
        """Add a firewall rule.
        
        Args:
            rule_data: Dictionary with rule details
            
        Returns:
            ID of the created rule or None if failed
        """
        try:
            # Add the rule to the database
            rule_id = None
            if self.db:
                # Pass rule_data as a dictionary without unpacking
                rule_id = self.db.add_rule(rule_data)
            
            # Apply the rule to the firewall
            chain = rule_data.get('chain', 'input')
            action = rule_data.get('action', 'drop')
            protocol = rule_data.get('protocol')
            src_ip = rule_data.get('src_ip')
            dst_ip = rule_data.get('dst_ip')
            src_port = rule_data.get('src_port')
            dst_port = rule_data.get('dst_port')
            
            if self.packet_filter:
                self.packet_filter.add_rule(
                    chain=chain,
                    action=action,
                    protocol=protocol,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=src_port,
                    dst_port=dst_port
                )
            
            return rule_id
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return None
    
    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """Update a firewall rule.
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary with updated rule details
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update the rule in the database
            success = False
            if self.db:
                success = self.db.update_rule(rule_id, rule_data)
            
            # Apply the change to the firewall
            # In practice, you'd need to delete the old rule and add the new one
            
            return success
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {e}")
            return False
    
    def delete_rule(self, rule_id: int) -> bool:
        """Delete a firewall rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the rule before deleting it
            rule = None
            if self.db:
                rules = self.db.get_rules({"id": rule_id})
                if rules:
                    rule = rules[0]
            
            # Delete the rule from the database
            success = False
            if self.db:
                success = self.db.delete_rule(rule_id)
            
            # Remove the rule from the firewall
            if rule and self.packet_filter:
                # In practice, you'd need to identify the rule in nftables and delete it
                pass
            
            return success
        except Exception as e:
            logger.error(f"Failed to delete rule {rule_id}: {e}")
            return False
    
    def get_content_filter_categories(self) -> List[Dict[str, Any]]:
        """Get a list of content filter categories.
        
        Returns:
            List of category dictionaries
        """
        if self.content_filter:
            return self.content_filter.get_categories()
        return []
    
    def get_scheduled_rules(self) -> List[Dict[str, Any]]:
        """Get a list of scheduled rules.
        
        Returns:
            List of scheduled rule dictionaries
        """
        if self.scheduler:
            return self.scheduler.list_scheduled_rules()
        return []
    
    def get_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get a list of available plugins.
        
        Returns:
            Dictionary mapping plugin names to their information
        """
        if self.plugin_manager:
            return self.plugin_manager.get_all_plugins()
        return {} 