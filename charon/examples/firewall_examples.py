#!/usr/bin/env python3
"""
Examples of using the Charon Packet Filter

This script demonstrates how to use the enhanced packet filter features
including stateful rules and NAT configuration.
"""

from charon.src.core.packet_filter import PacketFilter, RuleAction, NATType

def setup_basic_firewall():
    """Set up a basic firewall with common rules."""
    pf = PacketFilter()
    
    # Create base tables and chains
    pf.setup_base_table()
    
    # Allow established connections
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "state": "established,related",
        "comment": "Allow established connections"
    })
    
    # Allow loopback traffic
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "protocol": "tcp",
        "source": "127.0.0.1",
        "comment": "Allow localhost TCP"
    })
    
    # Allow SSH from specific IP
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "protocol": "tcp",
        "source": "192.168.1.100",  # Replace with your admin IP
        "destination": "22",
        "comment": "Allow SSH from admin IP"
    })
    
    # Allow HTTP/HTTPS
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "protocol": "tcp",
        "destination": "80,443",
        "comment": "Allow HTTP/HTTPS"
    })

def setup_nat():
    """Set up NAT for internet access."""
    pf = PacketFilter()
    
    # Create base tables and chains if not exists
    pf.setup_base_table()
    
    # Set up masquerade NAT for internet access
    pf.add_nat_rule(NATType.MASQUERADE, {
        "chain": "postrouting",
        "source": "192.168.1.0/24",  # Replace with your local network
        "comment": "NAT for local network"
    })
    
    # Port forward web server
    pf.add_nat_rule(NATType.DNAT, {
        "chain": "prerouting",
        "protocol": "tcp",
        "destination": "80",
        "to": "192.168.1.10:80",  # Replace with your web server IP
        "comment": "Forward HTTP to web server"
    })
    
    # Port forward SSH
    pf.add_nat_rule(NATType.DNAT, {
        "chain": "prerouting",
        "protocol": "tcp",
        "destination": "2222",  # External SSH port
        "to": "192.168.1.10:22",  # Internal SSH port
        "comment": "Forward SSH to internal server"
    })

def setup_vpn_rules():
    """Set up rules for VPN traffic."""
    pf = PacketFilter()
    
    # Allow OpenVPN traffic
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "protocol": "udp",
        "destination": "1194",  # Default OpenVPN port
        "comment": "Allow OpenVPN"
    })
    
    # Allow IPSec traffic
    pf.add_stateful_rule("input", {
        "action": RuleAction.ACCEPT,
        "protocol": "udp",
        "destination": "500,4500",  # IKE and NAT-T ports
        "comment": "Allow IPSec"
    })

if __name__ == "__main__":
    # Example usage
    print("Setting up basic firewall rules...")
    setup_basic_firewall()
    
    print("\nSetting up NAT rules...")
    setup_nat()
    
    print("\nSetting up VPN rules...")
    setup_vpn_rules()
    
    print("\nFirewall configuration complete!") 