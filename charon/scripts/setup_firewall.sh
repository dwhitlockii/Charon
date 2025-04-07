#!/bin/bash
set -e

# This script sets up basic firewall rules for the Charon firewall container
# It configures NAT, port forwarding, and basic security rules

echo "Setting up firewall rules..."

# Create necessary directories
mkdir -p /etc/iptables
mkdir -p /run/netns

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
echo 1 > /proc/sys/net/ipv6/conf/all/forwarding

# Clear existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback traffic
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH access to the firewall
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow web interface access
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# Configure NAT for LAN clients
iptables -t nat -A POSTROUTING -o eth0 -s 10.0.0.0/24 -j MASQUERADE
iptables -t nat -A POSTROUTING -o eth0 -s 172.16.0.0/24 -j MASQUERADE

# Allow LAN clients to access the internet
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# Allow DMZ servers to access the internet
iptables -A FORWARD -i eth2 -o eth0 -j ACCEPT

# Port forwarding: Web server in DMZ
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 172.16.0.10:80
iptables -A FORWARD -p tcp -d 172.16.0.10 --dport 80 -j ACCEPT

# Port forwarding: SSH to DMZ server
iptables -t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 172.16.0.10:22
iptables -A FORWARD -p tcp -d 172.16.0.10 --dport 22 -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4
chmod 644 /etc/iptables/rules.v4

echo "Firewall rules configured successfully!" 