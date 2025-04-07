#!/bin/sh

# Wait for Docker networking to be ready
echo "Waiting for Docker networking to be ready..."
sleep 5

# Install required packages
apk add --no-cache nftables python3-dev py3-pip gcc musl-dev linux-headers

# Set up Python path
export PYTHONPATH=/app:/app/src:$PYTHONPATH
echo "PYTHONPATH set to: $PYTHONPATH"

# Install Python dependencies
cd /app && pip3 install -r requirements.txt

# Create data directory for the web interface
mkdir -p /app/src/web/data
echo "Created data directory at /app/src/web/data"

# Generate a random secret key for Flask
export CHARON_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
echo "Generated Flask secret key"

# Generate a random admin password
export CHARON_ADMIN_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')
echo "===== INITIAL ADMIN CREDENTIALS ====="
echo "Username: admin"
echo "Password: $CHARON_ADMIN_PASSWORD"
echo "==================================="

# Start the firewall service in the background
echo "Starting firewall service..."
cd /app/src/core && python3 firewall_service.py &

# Start the web interface
echo "Starting web interface..."
cd /app/src/web
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la
echo "Starting Flask server..."
FLASK_APP=server.py FLASK_ENV=production FLASK_DEBUG=1 python3 -m flask run --host=0.0.0.0 --port=5000 &

# Keep the container running
tail -f /dev/null 