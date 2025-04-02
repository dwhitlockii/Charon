#!/usr/bin/env python3
"""
Charon Packet Filter Module

This module provides the core functionality for packet filtering using nftables.
It defines the basic structure for creating and managing firewall rules.
"""

import subprocess
import logging
import os
import json
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.packet_filter')

class PacketFilter:
    """Base class for packet filtering operations using nftables."""
    
    def __init__(self, table_name: str = "charon"):
        """Initialize the packet filter with a table name.
        
        Args:
            table_name (str): Name of the nftables table to use.
        """
        self.table_name = table_name
        self._check_permissions()
    
    def _check_permissions(self) -> None:
        """Check if the current user has permissions to modify firewall rules."""
        if os.geteuid() != 0:
            logger.warning("Not running as root. Some operations may fail.")
    
    def setup_base_table(self) -> bool:
        """Create the base table and chains for the firewall.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create the main table
            cmd = [
                "nft", "add", "table", "inet", self.table_name
            ]
            subprocess.run(cmd, check=True)
            
            # Create base chains
            chains = ["input", "output", "forward"]
            for chain in chains:
                cmd = [
                    "nft", "add", "chain", "inet", self.table_name,
                    chain, "{ type filter hook " + chain + " priority 0; policy drop; }"
                ]
                subprocess.run(cmd, check=True)
            
            logger.info(f"Base table '{self.table_name}' and chains created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create base table: {e}")
            return False
    
    def add_rule(self, chain: str, rule: str) -> bool:
        """Add a rule to a specific chain.
        
        Args:
            chain (str): The chain to add the rule to.
            rule (str): The rule specification in nftables syntax.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            cmd = [
                "nft", "add", "rule", "inet", self.table_name, chain, rule
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"Rule added to {chain} chain: {rule}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add rule to {chain}: {e}")
            return False
    
    def delete_rule(self, chain: str, handle: int) -> bool:
        """Delete a rule from a chain using its handle.
        
        Args:
            chain (str): The chain containing the rule.
            handle (int): The handle identifying the rule.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            cmd = [
                "nft", "delete", "rule", "inet", self.table_name, chain, "handle", str(handle)
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"Rule with handle {handle} deleted from {chain} chain")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete rule with handle {handle} from {chain}: {e}")
            return False
    
    def list_rules(self) -> Optional[str]:
        """List all rules in the table.
        
        Returns:
            Optional[str]: JSON formatted string of rules or None if failed.
        """
        try:
            cmd = ["nft", "--json", "list", "table", "inet", self.table_name]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list rules: {e}")
            return None 