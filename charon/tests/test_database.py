"""
Tests for the database module.
"""

import pytest
import datetime
from charon.src.db.database import Database, FirewallRule, FirewallLog, ConfigSetting


def test_database_connection(test_db):
    """Test database connection."""
    assert test_db is not None
    assert test_db.session is not None


def test_create_tables(test_db):
    """Test table creation."""
    # Tables should already be created by the fixture
    # Add a simple query to verify
    result = test_db.session.query(FirewallRule).all()
    assert isinstance(result, list)


def test_add_rule(test_db):
    """Test adding a firewall rule."""
    # Create a test rule
    rule_data = {
        'chain': 'INPUT',
        'action': 'ACCEPT',
        'protocol': 'TCP',
        'dst_port': '22',
        'description': 'Allow SSH',
        'enabled': True
    }
    
    # Add the rule
    rule_id = test_db.add_rule(rule_data)
    
    # Verify the rule was added
    assert rule_id is not None
    assert isinstance(rule_id, int)
    
    # Query the rule
    rule = test_db.session.query(FirewallRule).filter_by(id=rule_id).first()
    assert rule is not None
    assert rule.chain == 'INPUT'
    assert rule.action == 'ACCEPT'
    assert rule.protocol == 'TCP'
    assert rule.dst_port == '22'
    assert rule.description == 'Allow SSH'
    assert rule.enabled is True


def test_update_rule(test_db):
    """Test updating a firewall rule."""
    # Create a test rule
    rule_data = {
        'chain': 'INPUT',
        'action': 'ACCEPT',
        'protocol': 'TCP',
        'dst_port': '22',
        'description': 'Allow SSH',
        'enabled': True
    }
    
    # Add the rule
    rule_id = test_db.add_rule(rule_data)
    
    # Update the rule
    update_data = {
        'action': 'DROP',
        'description': 'Block SSH'
    }
    
    success = test_db.update_rule(rule_id, update_data)
    assert success is True
    
    # Query the rule
    rule = test_db.session.query(FirewallRule).filter_by(id=rule_id).first()
    assert rule is not None
    assert rule.action == 'DROP'
    assert rule.description == 'Block SSH'
    
    # Original fields should be unchanged
    assert rule.chain == 'INPUT'
    assert rule.protocol == 'TCP'
    assert rule.dst_port == '22'


def test_delete_rule(test_db):
    """Test deleting a firewall rule."""
    # Create a test rule
    rule_data = {
        'chain': 'INPUT',
        'action': 'ACCEPT',
        'protocol': 'TCP',
        'dst_port': '22',
        'description': 'Allow SSH',
        'enabled': True
    }
    
    # Add the rule
    rule_id = test_db.add_rule(rule_data)
    
    # Delete the rule
    success = test_db.delete_rule(rule_id)
    assert success is True
    
    # Query the rule - should not exist
    rule = test_db.session.query(FirewallRule).filter_by(id=rule_id).first()
    assert rule is None


def test_get_rules(test_db):
    """Test getting firewall rules with filters."""
    # Create test rules
    rules_data = [
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
            'action': 'DROP',
            'protocol': 'TCP',
            'dst_port': '23',
            'description': 'Block Telnet',
            'enabled': True
        },
        {
            'chain': 'OUTPUT',
            'action': 'ACCEPT',
            'protocol': 'TCP',
            'dst_port': '80',
            'description': 'Allow HTTP',
            'enabled': False
        }
    ]
    
    for rule_data in rules_data:
        test_db.add_rule(rule_data)
    
    # Get all rules
    all_rules = test_db.get_rules()
    assert len(all_rules) == 3
    
    # Filter by chain
    input_rules = test_db.get_rules(filters={'chain': 'INPUT'})
    assert len(input_rules) == 2
    
    # Filter by enabled
    enabled_rules = test_db.get_rules(filters={'enabled': True})
    assert len(enabled_rules) == 2
    
    # Filter by chain and action
    accept_input_rules = test_db.get_rules(filters={'chain': 'INPUT', 'action': 'ACCEPT'})
    assert len(accept_input_rules) == 1
    assert accept_input_rules[0].description == 'Allow SSH'


def test_add_log(test_db):
    """Test adding a log entry."""
    # Create a test log
    log_data = {
        'chain': 'INPUT',
        'action': 'DROP',
        'protocol': 'TCP',
        'src_ip': '192.168.1.100',
        'dst_ip': '203.0.113.42',
        'src_port': '45123',
        'dst_port': '80'
    }
    
    # Add the log
    log_id = test_db.add_log(log_data)
    
    # Verify the log was added
    assert log_id is not None
    assert isinstance(log_id, int)
    
    # Query the log
    log = test_db.session.query(FirewallLog).filter_by(id=log_id).first()
    assert log is not None
    assert log.chain == 'INPUT'
    assert log.action == 'DROP'
    assert log.protocol == 'TCP'
    assert log.src_ip == '192.168.1.100'
    assert log.dst_ip == '203.0.113.42'
    assert log.src_port == '45123'
    assert log.dst_port == '80'


def test_get_logs(test_db):
    """Test getting log entries with filters."""
    # Create test logs
    logs_data = [
        {
            'chain': 'INPUT',
            'action': 'DROP',
            'protocol': 'TCP',
            'src_ip': '192.168.1.100',
            'dst_ip': '203.0.113.42',
            'src_port': '45123',
            'dst_port': '80'
        },
        {
            'chain': 'INPUT',
            'action': 'ACCEPT',
            'protocol': 'UDP',
            'src_ip': '192.168.1.101',
            'dst_ip': '8.8.8.8',
            'src_port': '53421',
            'dst_port': '53'
        },
        {
            'chain': 'OUTPUT',
            'action': 'ACCEPT',
            'protocol': 'TCP',
            'src_ip': '192.168.1.102',
            'dst_ip': '203.0.113.43',
            'src_port': '45124',
            'dst_port': '443'
        }
    ]
    
    for log_data in logs_data:
        test_db.add_log(log_data)
    
    # Get all logs
    all_logs = test_db.get_logs()
    assert len(all_logs) == 3
    
    # Filter by chain
    input_logs = test_db.get_logs(filters={'chain': 'INPUT'})
    assert len(input_logs) == 2
    
    # Filter by action
    accept_logs = test_db.get_logs(filters={'action': 'ACCEPT'})
    assert len(accept_logs) == 2
    
    # Test limit
    limited_logs = test_db.get_logs(limit=2)
    assert len(limited_logs) == 2


def test_config_settings(test_db):
    """Test configuration settings."""
    # Set config
    test_db.set_config('general', 'version', '1.0.0', 'Charon version')
    
    # Get config
    value = test_db.get_config('general', 'version')
    assert value == '1.0.0'
    
    # Update config
    test_db.set_config('general', 'version', '1.1.0')
    value = test_db.get_config('general', 'version')
    assert value == '1.1.0'
    
    # Default value
    value = test_db.get_config('general', 'nonexistent', 'default')
    assert value == 'default'
    
    # Get section
    test_db.set_config('firewall', 'enabled', 'true')
    test_db.set_config('firewall', 'policy', 'drop')
    
    section = test_db.get_config_section('firewall')
    assert len(section) == 2
    assert section['enabled'] == 'true'
    assert section['policy'] == 'drop' 