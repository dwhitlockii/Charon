# Docker Setup for Charon Firewall

This document provides detailed information about the Docker setup for running the Charon firewall in a containerized environment.

## Overview

The Charon firewall can be deployed using Docker containers, allowing for isolated network environments and easy testing of firewall rules. The setup includes:

- A main firewall container running the Charon application
- Test client containers in the LAN network
- A DMZ server container for testing public-facing services

## Prerequisites

- Docker and Docker Compose installed
- Linux host with kernel support for network namespaces
- Sufficient permissions to run privileged containers

## Directory Structure

```
charon/
├── Dockerfile.firewall      # Dockerfile for the firewall container
├── docker-compose.firewall.yml  # Docker Compose configuration
├── scripts/
│   └── setup_network.sh     # Network setup script
└── ...
```

## Container Architecture

The Docker setup creates the following network topology:

```
[Internet] <---> [WAN Interface] <---> [Charon Firewall] <---> [LAN Interface] <---> [LAN Clients]
                                                      |
                                                      v
                                                [DMZ Interface]
                                                      |
                                                      v
                                                [DMZ Server]
```

### Network Configuration

- **WAN Network**: 172.20.0.0/24
  - Firewall: 172.20.0.1
  - Internet Gateway: 172.20.0.2

- **LAN Network**: 172.21.0.0/24
  - Firewall: 172.21.0.1
  - LAN Clients: 172.21.0.2+

- **DMZ Network**: 172.22.0.0/24
  - Firewall: 172.22.0.1
  - DMZ Server: 172.22.0.2

## Container Configuration

### Firewall Container

The firewall container runs the Charon application with the following configuration:

- **Base Image**: Ubuntu 22.04
- **Network Mode**: Host (for direct access to host network interfaces)
- **Capabilities**: NET_ADMIN, NET_RAW (required for firewall operations)
- **Volumes**:
  - `./data:/app/data`: Persistent storage for configuration and database
  - `./logs:/app/logs`: Log files
  - `/var/run/netns:/var/run/netns:rw`: Access to network namespaces
- **Environment Variables**:
  - `CHARON_DB_TYPE`: Database type (sqlite)
  - `CHARON_DB_PATH`: Path to the database file
  - `CHARON_SECRET_KEY`: Secret key for web interface
  - `CHARON_SECURE_COOKIES`: Cookie security setting

### Client Containers

- **LAN Clients**: Alpine-based containers for testing LAN connectivity
- **DMZ Server**: Nginx container for testing public-facing services

## Network Setup

The `setup_network.sh` script performs the following operations:

1. Creates network namespaces for WAN, LAN, and DMZ
2. Sets up virtual ethernet pairs for each network
3. Configures IP addresses for all interfaces
4. Enables IP forwarding
5. Sets up NAT rules for outbound traffic

## Usage

### Building and Starting Containers

```bash
# Build the containers
docker-compose -f docker-compose.firewall.yml build

# Start the containers
docker-compose -f docker-compose.firewall.yml up -d
```

### Accessing the Web Interface

Once the containers are running, the Charon web interface is accessible at:

```
http://localhost:5000
```

### Stopping Containers

```bash
docker-compose -f docker-compose.firewall.yml down
```

## Troubleshooting

### Common Issues

1. **Network Interface Creation Fails**
   - Ensure the host has sufficient capabilities to create network interfaces
   - Check if the required kernel modules are loaded

2. **Container Networking Issues**
   - Verify that no other containers are using the same IP ranges
   - Check for conflicts with host network interfaces

3. **Firewall Rules Not Applied**
   - Ensure the container has the necessary capabilities
   - Check the logs for any error messages

### Debugging

To debug network issues:

```bash
# Check network interfaces in the firewall container
docker exec charon-firewall ip addr

# Check routing tables
docker exec charon-firewall ip route

# Check iptables rules
docker exec charon-firewall iptables -L -n -v
```

## Security Considerations

- The firewall container runs with privileged access, which is necessary for network operations
- In production environments, consider using more restrictive capabilities
- The default secret key should be changed in production
- The web interface should be secured with HTTPS in production

## Future Enhancements

- Implement container health checks
- Add support for custom network configurations
- Create a more isolated network environment using Docker's built-in networking
- Add support for persistent firewall rules across container restarts 