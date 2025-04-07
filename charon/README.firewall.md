# Charon Firewall Development Environment

This document explains how to set up and use the Charon firewall development environment, which runs in Docker containers to simulate a real network environment.

## Overview

The Charon firewall development environment consists of the following components:

1. **Internet Gateway**: A simulated internet gateway that provides internet access to the LAN and DMZ networks.
2. **Firewall Container (Charon)**: The main firewall container that runs the Charon firewall software.
3. **LAN Clients**: Two client containers that simulate computers on the local network.
4. **DMZ Server**: A web server container that simulates a server in the DMZ network.

## Network Topology

```
Internet <---> Internet Gateway (192.168.1.1) <---> Firewall (192.168.1.2) <---> LAN (10.0.0.0/24)
                                                      |
                                                      v
                                                   DMZ (172.16.0.0/24)
```

## Prerequisites

- Docker and Docker Compose installed on your system
- Linux host with kernel support for network namespaces and nftables
- Sufficient permissions to run Docker commands
- WSL2 (if running on Windows)

## Setup Instructions

1. Clone the Charon repository:
   ```bash
   git clone https://github.com/yourusername/charon.git
   cd charon
   ```

2. Build and start the containers:
   ```bash
   docker compose -f docker-compose.firewall.yml up -d --build
   ```

3. Access the firewall web interface at http://localhost:5000

## Container Information

- **Internet Gateway**: internet-gateway
  - IP: 192.168.1.1

- **Firewall Container**: charon-firewall
  - Web Interface: http://localhost:5000
  - WAN IP: 192.168.1.2
  - LAN IP: 10.0.0.1
  - DMZ IP: 172.16.0.1

- **LAN Clients**: lan-client1, lan-client2
  - IPs: 10.0.0.10, 10.0.0.11

- **DMZ Server**: dmz-server
  - IP: 172.16.0.10
  - Web Server: http://localhost:80 (port forwarded from firewall)
  - SSH Access: ssh root@localhost -p 2222 (port forwarded from firewall)

## Firewall Rules

The firewall is configured with the following rules:

1. **Default Policies**:
   - INPUT: DROP
   - FORWARD: DROP
   - OUTPUT: ACCEPT

2. **NAT Configuration**:
   - LAN clients (10.0.0.0/24) are NATed to the WAN interface
   - DMZ servers (172.16.0.0/24) are NATed to the WAN interface

3. **Port Forwarding**:
   - Port 80 -> DMZ web server (172.16.0.10:80)
   - Port 2222 -> DMZ server SSH (172.16.0.10:22)

## Accessing the Containers

To access the shell of any container:

```bash
docker exec -it <container-name> /bin/sh
```

For example, to access the firewall container:

```bash
docker exec -it charon-firewall /bin/sh
```

## Network Testing

1. Test LAN to DMZ connectivity:
   ```bash
   docker exec -it lan-client1 ping 172.16.0.10
   ```

2. Test LAN to WAN connectivity:
   ```bash
   docker exec -it lan-client1 ping 192.168.1.1
   ```

3. Test DMZ to WAN connectivity:
   ```bash
   docker exec -it dmz-server ping 192.168.1.1
   ```

## Stopping the Environment

To stop the development environment:

```bash
docker compose -f docker-compose.firewall.yml down
```

## Troubleshooting

1. **Container Networking Issues**:
   - Check if the containers are running: `docker ps`
   - Check container logs: `docker logs <container-name>`
   - Verify network connectivity: `docker exec <container-name> ping <ip-address>`

2. **Firewall Rules Issues**:
   - Check current firewall rules: `docker exec charon-firewall nft list ruleset`
   - Check NAT rules: `docker exec charon-firewall nft list ruleset table ip charon_nat`
   - Reapply firewall rules: `docker exec charon-firewall python3 /app/firewall.py`

3. **Web Interface Access Issues**:
   - Verify the container is running: `docker ps | grep charon-firewall`
   - Check container logs: `docker logs charon-firewall`
   - Verify port mapping: `docker port charon-firewall`

## Development Workflow

1. Make changes to the Charon codebase
2. Rebuild the Docker image: `docker build -t charon-firewall -f Dockerfile.firewall .`
3. Restart the containers: `docker compose -f docker-compose.firewall.yml restart`
4. Test your changes through the web interface or by accessing the containers directly

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [nftables Documentation](https://wiki.nftables.org/wiki-nftables/index.php/Main_Page)
- [Charon Documentation](doc/documentation.md) 