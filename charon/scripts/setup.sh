#!/bin/bash
# Charon Firewall Setup Script

# Exit on any error
set -e

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Try 'sudo $0'" >&2
  exit 1
fi

# Check for nftables
if ! command -v nft &> /dev/null; then
  echo "nftables not found. Installing..."
  
  # Detect the distribution
  if [ -f /etc/debian_version ]; then
    apt-get update
    apt-get install -y nftables
  elif [ -f /etc/redhat-release ]; then
    dnf install -y nftables
  else
    echo "Unsupported distribution. Please install nftables manually."
    exit 1
  fi
fi

# Enable and start nftables service
systemctl enable nftables
systemctl start nftables

# Create Python virtual environment
if ! command -v python3 &> /dev/null; then
  echo "Python 3 not found. Please install Python 3.8 or later."
  exit 1
fi

echo "Creating Python virtual environment..."
cd "$(dirname "$0")/.."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Initialize the firewall
echo "Initializing Charon firewall..."
python3 -c "from charon.src.core.packet_filter import PacketFilter; pf = PacketFilter(); pf.setup_base_table()"

# Add default rules for essential services
python3 -c "from charon.src.core.packet_filter import PacketFilter; pf = PacketFilter(); pf.add_rule('input', 'ct state established,related accept')"
python3 -c "from charon.src.core.packet_filter import PacketFilter; pf = PacketFilter(); pf.add_rule('input', 'iif lo accept')"

echo "Charon firewall setup complete!"
echo "You may need to add rules to allow specific services like SSH."
echo "Example: sudo python3 -c \"from charon.src.core.packet_filter import PacketFilter; pf = PacketFilter(); pf.add_rule('input', 'tcp dport 22 accept')\"" 