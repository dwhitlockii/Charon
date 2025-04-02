#!/bin/bash
set -e

# Install iptables, netfilter tools, and other dependencies if not already installed
apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    nftables \
    iproute2 \
    ipset \
    tcpdump \
    net-tools \
    procps \
    sudo \
    vim \
    curl \
    conntrack \
    default-mysql-client

# Ensure data directories exist
mkdir -p /etc/charon /var/log/charon /var/lib/charon

# Wait for MySQL to be ready
if [ "$CHARON_DB_TYPE" = "mysql" ]; then
    echo "Waiting for MySQL to be ready..."
    
    # Give some time for MySQL to start
    sleep 5
    
    # Try to connect to MySQL
    for i in {1..30}; do
        if mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --silent; then
            echo "MySQL is ready!"
            break
        fi
        echo "Waiting for MySQL ($i/30)..."
        sleep 2
    done
fi

# Ensure database tables exist
cd /app
python -c "from src.db.database import Database; db = Database(); db.connect(); db.create_tables()"

# Collect real firewall data
echo "Collecting real firewall data..."

# Check if iptables is available and get current rules
if command -v iptables >/dev/null 2>&1; then
    echo "Firewall Rules (iptables):"
    iptables-save > /etc/charon/iptables-rules.conf
    cat /etc/charon/iptables-rules.conf
fi

# Check if nftables is available
if command -v nft >/dev/null 2>&1; then
    echo "Firewall Rules (nftables):"
    nft list ruleset > /etc/charon/nft-rules.conf
    cat /etc/charon/nft-rules.conf
fi

# Capture network statistics
echo "Network Interface Statistics:"
ip -s link > /etc/charon/network-stats.txt
cat /etc/charon/network-stats.txt

# If host logs are mounted, parse them for firewall events
if [ -d "$HOST_LOG_PATH" ]; then
    echo "Processing host logs for firewall events..."
    if [ -f "$HOST_LOG_PATH/kern.log" ]; then
        grep -i "iptables\|firewall\|drop\|reject\|accept" "$HOST_LOG_PATH/kern.log" | tail -n 1000 > /var/log/charon/firewall-events.log
    fi
fi

# Go to the src/web directory
cd /app/src/web

# Start the web server
echo "Starting the Charon web server..."
python server.py 