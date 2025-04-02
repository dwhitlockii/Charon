#!/usr/bin/env python3
"""
Script to initialize the database with default configuration settings.

This script adds default configuration values to the database for the Charon firewall.
"""

import os
import sys
import logging

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

def init_config():
    """Initialize the database with default configuration."""
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
        # General settings
        db.set_config('general', 'version', '1.0.0', 'Charon Firewall version')
        db.set_config('general', 'hostname', 'charon', 'Hostname')
        db.set_config('general', 'log_level', 'info', 'Logging level')
        
        # Firewall settings
        db.set_config('firewall', 'enabled', 'true', 'Firewall enabled')
        db.set_config('firewall', 'default_policy', 'drop', 'Default firewall policy')
        db.set_config('firewall', 'log_dropped', 'true', 'Log dropped packets')
        db.set_config('firewall', 'log_accepted', 'false', 'Log accepted packets')
        
        # Content filter settings
        db.set_config('content_filter', 'enabled', 'true', 'Content filter enabled')
        db.set_config('content_filter', 'domains_count', '1250', 'Number of blocked domains')
        db.set_config('content_filter', 'categories_enabled', '5', 'Number of enabled categories')
        
        # QoS settings
        db.set_config('qos', 'enabled', 'false', 'QoS enabled')
        db.set_config('qos', 'traffic_classes', '4', 'Number of traffic classes')
        db.set_config('qos', 'active_filters', '0', 'Number of active filters')
        
        # Add some sample categories for content filter
        categories = [
            ('adult', 'Adult content', 'true'),
            ('gambling', 'Gambling websites', 'true'),
            ('social', 'Social media', 'false'),
            ('ads', 'Advertisement sites', 'true'),
            ('malware', 'Malware and phishing sites', 'true')
        ]
        
        for cat_id, cat_name, cat_enabled in categories:
            db.set_config('category', cat_id, cat_name, f'Content filter category: {cat_name}')
            db.set_config('category_enabled', cat_id, cat_enabled, f'Category enabled status: {cat_name}')
        
        # Add some sample firewall rules
        rules = [
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
            },
            {
                'chain': 'INPUT',
                'action': 'DROP',
                'protocol': 'TCP',
                'dst_port': '23',
                'description': 'Block Telnet',
                'enabled': True
            }
        ]
        
        for rule in rules:
            db.add_rule(rule)
            logger.info(f"Added rule: {rule['action']} {rule['protocol']} to port {rule['dst_port']}")
        
        # Add some sample logs
        logs = [
            {
                'chain': 'INPUT',
                'action': 'DROP',
                'protocol': 'TCP',
                'src_ip': '192.168.1.105',
                'src_port': '45321',
                'dst_ip': '203.0.113.42',
                'dst_port': '80'
            },
            {
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'UDP',
                'src_ip': '192.168.1.100',
                'src_port': '53421',
                'dst_ip': '8.8.8.8',
                'dst_port': '53'
            },
            {
                'chain': 'INPUT',
                'action': 'DROP',
                'protocol': 'TCP',
                'src_ip': '192.168.1.101',
                'src_port': '55213',
                'dst_ip': '198.51.100.23',
                'dst_port': '443'
            }
        ]
        
        for log in logs:
            db.add_log(log)
            logger.info(f"Added log: {log['action']} {log['protocol']} from {log['src_ip']} to {log['dst_ip']}")
        
        logger.info("Database initialized with default configuration")
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