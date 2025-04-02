#!/usr/bin/env python3
"""
Test suite for Packet Filter module

Note: These tests require root privileges to run, as they modify firewall rules.
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.packet_filter import PacketFilter

class TestPacketFilter(unittest.TestCase):
    """Test cases for the PacketFilter class."""
    
    @patch('subprocess.run')
    def test_setup_base_table(self, mock_run):
        """Test creating a base table and chains."""
        # Configure the mock to return a successful CompletedProcess
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create an instance of PacketFilter
        pf = PacketFilter("test_table")
        
        # Call setup_base_table and check the result
        result = pf.setup_base_table()
        self.assertTrue(result)
        
        # Check if subprocess.run was called the correct number of times
        # Once for creating the table, three times for creating the chains
        self.assertEqual(mock_run.call_count, 4)
    
    @patch('subprocess.run')
    def test_add_rule(self, mock_run):
        """Test adding a rule to a chain."""
        # Configure the mock to return a successful CompletedProcess
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create an instance of PacketFilter
        pf = PacketFilter("test_table")
        
        # Call add_rule and check the result
        result = pf.add_rule("input", "tcp dport 22 accept")
        self.assertTrue(result)
        
        # Check if subprocess.run was called with the correct arguments
        mock_run.assert_called_with(
            ["nft", "add", "rule", "inet", "test_table", "input", "tcp dport 22 accept"],
            check=True
        )
    
    @patch('subprocess.run')
    def test_delete_rule(self, mock_run):
        """Test deleting a rule from a chain."""
        # Configure the mock to return a successful CompletedProcess
        mock_run.return_value = MagicMock(returncode=0)
        
        # Create an instance of PacketFilter
        pf = PacketFilter("test_table")
        
        # Call delete_rule and check the result
        result = pf.delete_rule("input", 42)
        self.assertTrue(result)
        
        # Check if subprocess.run was called with the correct arguments
        mock_run.assert_called_with(
            ["nft", "delete", "rule", "inet", "test_table", "input", "handle", "42"],
            check=True
        )

if __name__ == "__main__":
    unittest.main() 