#!/bin/bash
set -e

# This script sets up a development environment for the Charon firewall
# It builds the Docker image and runs the container with the necessary configurations

echo "Setting up Charon firewall development environment..."

# Create necessary directories if they don't exist
mkdir -p data logs

# Build the Docker image
echo "Building Docker image..."
docker build -t charon-firewall -f Dockerfile.firewall .

# Run the container using docker-compose
echo "Starting containers..."
docker-compose -f docker-compose.firewall.yml up -d

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 5

# Copy the firewall setup script to the container
echo "Configuring firewall rules..."
docker cp scripts/setup_firewall.sh charon-firewall:/app/setup_firewall.sh
docker exec charon-firewall chmod +x /app/setup_firewall.sh
docker exec charon-firewall /app/setup_firewall.sh

echo "Development environment setup complete!"
echo "Firewall web interface: http://localhost:5000"
echo "SSH access: ssh root@localhost -p 22"
echo ""
echo "Container information:"
docker ps | grep charon-firewall
echo ""
echo "To access the firewall container shell:"
echo "docker exec -it charon-firewall /bin/bash"
echo ""
echo "To stop the environment:"
echo "docker-compose -f docker-compose.firewall.yml down" 