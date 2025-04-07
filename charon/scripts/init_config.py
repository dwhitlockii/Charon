#!/usr/bin/env python3
"""
Script to initialize the database with default configuration settings.

This script adds default configuration values to the database for the Charon firewall.
"""

import os
import sys
import logging
import subprocess
import platform
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.scripts.init_config')

# Add the parent directory to the path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from charon.src.db.database import Database
except ImportError as e:
    logger.error(f"Error importing database module: {e}")
    sys.exit(1)

def get_system_info():
    """Collect real system information."""
    info = {
        'hostname': platform.node(),
        'os': platform.system(),
        'os_version': platform.version(),
        'cpu_count': os.cpu_count(),
        'memory_total': 0,
        'interfaces': []
    }
    
    # Get memory information
    try:
        if platform.system() == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        info['memory_total'] = int(line.split(':')[1].strip().split()[0]) // 1024  # Convert to MB
        elif platform.system() == 'Windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            memory_status = ctypes.c_ulonglong()
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
            info['memory_total'] = memory_status.value // (1024 * 1024)  # Convert to MB
    except Exception as e:
        logger.warning(f"Could not get memory information: {e}")
    
    # Get network interfaces
    try:
        if platform.system() == 'Linux':
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split('\n'):
                    if ':' in line and '@' not in line and 'lo:' not in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            current_interface = parts[1].strip()
                            info['interfaces'].append(current_interface)
        elif platform.system() == 'Windows':
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split('\n'):
                    if 'adapter' in line.lower() and ':' in line:
                        current_interface = line.split(':')[0].strip()
                        info['interfaces'].append(current_interface)
    except Exception as e:
        logger.warning(f"Could not get network interfaces: {e}")
    
    return info

def get_firewall_rules():
    """Collect real firewall rules from the system."""
    rules = []
    
    try:
        if platform.system() == 'Linux':
            # Get iptables rules
            result = subprocess.run(['iptables', '-L', '-n', '-v'], capture_output=True, text=True)
            if result.returncode == 0:
                current_chain = None
                for line in result.stdout.split('\n'):
                    if 'Chain' in line:
                        current_chain = line.split()[1]
                    elif line.strip() and 'target' not in line and 'Chain' not in line:
                        parts = line.split()
                        if len(parts) >= 8:
                            action = parts[0]
                            protocol = parts[3]
                            dst_port = parts[6] if len(parts) > 6 else 'any'
                            
                            rules.append({
                                'chain': current_chain,
                                'action': action,
                                'protocol': protocol,
                                'dst_port': dst_port,
                                'description': f'Rule from {current_chain} chain',
                                'enabled': True
                            })
    except Exception as e:
        logger.warning(f"Could not get firewall rules: {e}")
    
    return rules

def init_config():
    """Initialize the database with real system data."""
    # Connect to the database
    db = Database()
    if not db.connect():
        logger.error("Failed to connect to database")
        return False
    
    logger.info("Connected to database")
    
    # Create tables if they don't exist
    if not db.create_tables():
        logger.error("Failed to create tables")
        return False
    
    logger.info("Tables created successfully")
    
    # Set default configuration values
    try:
        # Get real system information
        system_info = get_system_info()
        
        # General settings
        db.set_config('general', 'version', '1.0.0', 'Charon Firewall version')
        db.set_config('general', 'hostname', system_info['hostname'], 'Hostname')
        db.set_config('general', 'log_level', 'info', 'Logging level')
        db.set_config('general', 'os', system_info['os'], 'Operating System')
        db.set_config('general', 'os_version', system_info['os_version'], 'OS Version')
        db.set_config('general', 'cpu_count', str(system_info['cpu_count']), 'CPU Count')
        db.set_config('general', 'memory_total', str(system_info['memory_total']), 'Total Memory (MB)')
        
        # Firewall settings
        db.set_config('firewall', 'enabled', 'true', 'Firewall enabled')
        db.set_config('firewall', 'default_policy', 'drop', 'Default firewall policy')
        db.set_config('firewall', 'log_dropped', 'true', 'Log dropped packets')
        db.set_config('firewall', 'log_accepted', 'false', 'Log accepted packets')
        
        # Content filter settings
        db.set_config('content_filter', 'enabled', 'true', 'Content filter enabled')
        db.set_config('content_filter', 'domains_count', '0', 'Number of blocked domains')
        db.set_config('content_filter', 'categories_enabled', '0', 'Number of enabled categories')
        
        # QoS settings
        db.set_config('qos', 'enabled', 'false', 'QoS enabled')
        db.set_config('qos', 'traffic_classes', '0', 'Number of traffic classes')
        db.set_config('qos', 'active_filters', '0', 'Number of active filters')
        
        # Add network interfaces
        for interface in system_info['interfaces']:
            db.set_config('interface', interface, 'true', f'Network interface: {interface}')
        
        # Add real firewall rules
        rules = get_firewall_rules()
        if not rules:
            # If no rules were found, add minimal default rules
            default_rules = [
                {
                    'chain': 'INPUT',
                    'action': 'ACCEPT',
                    'protocol': 'TCP',
                    'dst_port': '22',
                    'description': 'Allow SSH',
                    'enabled': True
                },
                {
                    'chain': 'INPUT',
                    'action': 'ACCEPT',
                    'protocol': 'TCP',
                    'dst_port': '80',
                    'description': 'Allow HTTP',
                    'enabled': True
                },
                {
                    'chain': 'INPUT',
                    'action': 'ACCEPT',
                    'protocol': 'TCP',
                    'dst_port': '443',
                    'description': 'Allow HTTPS',
                    'enabled': True
                }
            ]
            for rule in default_rules:
                db.add_rule(rule)
                logger.info(f"Added default rule: {rule['action']} {rule['protocol']} to port {rule['dst_port']}")
        else:
            for rule in rules:
                db.add_rule(rule)
                logger.info(f"Added system rule: {rule['action']} {rule['protocol']} to port {rule['dst_port']}")
        
        logger.info("Database initialized with real system data")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        # Close the database connection
        db.close()

if __name__ == '__main__':
    success = init_config()
    sys.exit(0 if success else 1) 