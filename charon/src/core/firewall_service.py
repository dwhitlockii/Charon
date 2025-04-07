#!/usr/bin/env python3
"""
Charon Firewall Service

This module provides the main entry point for the firewall service.
It uses the PacketFilter class to set up and manage firewall rules.
"""

import logging
import time
from packet_filter import PacketFilter, RuleAction, NATType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.firewall_service')

def main():
    """Main entry point for the firewall service."""
    logger.info("Starting Charon firewall service...")

    # Create packet filter instance
    pf = PacketFilter()

    # Set up base tables and chains
    if not pf.setup_base_table():
        logger.error("Failed to set up base tables and chains")
        return

    # Allow established and related connections
    pf.add_rule("input", "ct state established,related counter accept comment \"Allow established and related connections\"")
    pf.add_rule("output", "ct state established,related counter accept comment \"Allow established and related connections\"")
    pf.add_rule("forward", "ct state established,related counter accept comment \"Allow established and related connections\"")

    # Allow ICMP
    pf.add_rule("input", "meta l4proto icmp counter accept comment \"Allow incoming ICMP\"")
    pf.add_rule("output", "meta l4proto icmp counter accept comment \"Allow outgoing ICMP\"")
    pf.add_rule("forward", "meta l4proto icmp counter accept comment \"Allow forwarded ICMP\"")

    # Allow SSH access to the firewall
    pf.add_rule("input", "tcp dport 22 ct state new counter accept comment \"Allow SSH access\"")

    # Allow HTTP/HTTPS access to the firewall's web interface
    pf.add_rule("input", "tcp dport { 80, 443 } ct state new counter accept comment \"Allow HTTP/HTTPS access\"")

    # Set up NAT for LAN clients
    pf.add_nat_rule(NATType.MASQUERADE, {
        "chain": "postrouting",
        "source": "10.0.0.0/24",  # LAN network
        "comment": "NAT for LAN clients"
    })

    # Allow forwarding from LAN to DMZ
    pf.add_rule("forward", "ip saddr 10.0.0.0/24 ip daddr 172.16.0.0/24 ct state new counter accept comment \"Allow LAN to DMZ\"")

    # Allow forwarding from LAN to WAN
    pf.add_rule("forward", "ip saddr 10.0.0.0/24 ct state new counter accept comment \"Allow LAN to WAN\"")

    # Allow forwarding from DMZ to WAN
    pf.add_rule("forward", "ip saddr 172.16.0.0/24 ct state new counter accept comment \"Allow DMZ to WAN\"")

    logger.info("Firewall rules configured successfully")

    # Keep the service running
    while True:
        time.sleep(60)
        logger.info("Firewall service is running...")

if __name__ == "__main__":
    main() 