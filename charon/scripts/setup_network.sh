#!/bin/sh

# Create network namespaces if they don't exist
ip netns list | grep -q wan || ip netns add wan
ip netns list | grep -q lan || ip netns add lan
ip netns list | grep -q dmz || ip netns add dmz

# Create virtual ethernet pairs
ip link add wan0 type veth peer name wan1
ip link add lan0 type veth peer name lan1
ip link add dmz0 type veth peer name dmz1

# Move interfaces to their respective namespaces
ip link set wan1 netns wan
ip link set lan1 netns lan
ip link set dmz1 netns dmz

# Configure IP addresses
ip addr add 192.168.1.1/24 dev wan0
ip netns exec wan ip addr add 192.168.1.2/24 dev wan1

ip addr add 10.0.0.1/24 dev lan0
ip netns exec lan ip addr add 10.0.0.2/24 dev lan1

ip addr add 172.16.0.1/24 dev dmz0
ip netns exec dmz ip addr add 172.16.0.2/24 dev dmz1

# Bring up interfaces
ip link set wan0 up
ip netns exec wan ip link set wan1 up
ip link set lan0 up
ip netns exec lan ip link set lan1 up
ip link set dmz0 up
ip netns exec dmz ip link set dmz1 up

# Enable IP forwarding in each namespace
ip netns exec wan sysctl -w net.ipv4.ip_forward=1
ip netns exec lan sysctl -w net.ipv4.ip_forward=1
ip netns exec dmz sysctl -w net.ipv4.ip_forward=1

# Set up NAT
iptables -t nat -A POSTROUTING -o wan0 -j MASQUERADE
iptables -A FORWARD -i wan0 -o lan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i lan0 -o wan0 -j ACCEPT
iptables -A FORWARD -i wan0 -o dmz0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i dmz0 -o wan0 -j ACCEPT

echo "Network interfaces configured successfully!" 