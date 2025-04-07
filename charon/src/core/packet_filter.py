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
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.packet_filter')

class RuleAction(Enum):
    """Enum for firewall rule actions."""
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    RETURN = "return"

class NATType(Enum):
    """Enum for NAT types."""
    SNAT = "snat"
    DNAT = "dnat"
    MASQUERADE = "masquerade"

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
            
            # Create NAT table and chains
            nat_cmd = [
                "nft", "add", "table", "ip", f"{self.table_name}_nat"
            ]
            subprocess.run(nat_cmd, check=True)
            
            # Create NAT chains
            nat_chains = ["prerouting", "postrouting"]
            for chain in nat_chains:
                cmd = [
                    "nft", "add", "chain", "ip", f"{self.table_name}_nat",
                    chain, "{ type nat hook " + chain + " priority 0; }"
                ]
                subprocess.run(cmd, check=True)
            
            logger.info(f"Base tables and chains created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create base tables: {e}")
            return False

    def add_stateful_rule(self, chain: str, rule_spec: Dict[str, Any]) -> bool:
        """Add a stateful rule to a specific chain.
        
        Args:
            chain (str): The chain to add the rule to.
            rule_spec (Dict[str, Any]): Rule specification including:
                - action: RuleAction enum value
                - protocol: tcp/udp/icmp
                - source: source IP/network
                - destination: destination IP/network
                - state: new/established/related/untracked
                - comment: optional rule description
                
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Build the rule string
            rule_parts = []
            
            # Add protocol if specified
            if 'protocol' in rule_spec:
                rule_parts.append(f"protocol {rule_spec['protocol']}")
            
            # Add source if specified
            if 'source' in rule_spec:
                rule_parts.append(f"ip saddr {rule_spec['source']}")
            
            # Add destination if specified
            if 'destination' in rule_spec:
                rule_parts.append(f"ip daddr {rule_spec['destination']}")
            
            # Add state tracking
            if 'state' in rule_spec:
                rule_parts.append(f"ct state {rule_spec['state']}")
            
            # Add comment if specified
            if 'comment' in rule_spec:
                rule_parts.append(f"comment \"{rule_spec['comment']}\"")
            
            # Add action
            rule_parts.append(rule_spec['action'].value)
            
            # Combine all parts
            rule = " ".join(rule_parts)
            
            cmd = [
                "nft", "add", "rule", "inet", self.table_name, chain, rule
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"Stateful rule added to {chain} chain: {rule}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add stateful rule to {chain}: {e}")
            return False

    def add_nat_rule(self, nat_type: NATType, rule_spec: Dict[str, Any]) -> bool:
        """Add a NAT rule.
        
        Args:
            nat_type (NATType): Type of NAT (SNAT/DNAT/MASQUERADE)
            rule_spec (Dict[str, Any]): Rule specification including:
                - chain: prerouting/postrouting
                - source: source IP/network
                - destination: destination IP/network
                - to: target IP/port for NAT
                - comment: optional rule description
                
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Build the rule string
            rule_parts = []
            
            # Add protocol if specified
            if 'protocol' in rule_spec:
                rule_parts.append(f"protocol {rule_spec['protocol']}")
            
            # Add source if specified
            if 'source' in rule_spec:
                rule_parts.append(f"ip saddr {rule_spec['source']}")
            
            # Add destination if specified
            if 'destination' in rule_spec:
                rule_parts.append(f"ip daddr {rule_spec['destination']}")
            
            # Add NAT target
            if nat_type == NATType.MASQUERADE:
                rule_parts.append("masquerade")
            else:
                rule_parts.append(f"{nat_type.value} to {rule_spec['to']}")
            
            # Add comment if specified
            if 'comment' in rule_spec:
                rule_parts.append(f"comment \"{rule_spec['comment']}\"")
            
            # Combine all parts
            rule = " ".join(rule_parts)
            
            cmd = [
                "nft", "add", "rule", "ip", f"{self.table_name}_nat",
                rule_spec['chain'], rule
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"NAT rule added to {rule_spec['chain']} chain: {rule}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add NAT rule: {e}")
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