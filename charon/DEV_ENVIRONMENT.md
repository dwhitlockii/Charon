# Charon Development Environment

This document explains how to set up and use the Docker-based development environment for the Charon Firewall project.

## Prerequisites

Make sure you have the following software installed on your system:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/charon.git
   cd charon
   ```

2. Start the development environment:
   ```
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. Access the web interface at [http://localhost:5000](http://localhost:5000)
   - Default credentials: username `admin`, password `admin`

4. Access the database management interface at [http://localhost:8081](http://localhost:8081)
   - System: MySQL
   - Server: mysql-dev
   - Username: charon
   - Password: charonpass
   - Database: charon

## Development Environment Features

The development environment provides:

- A complete Linux environment with all necessary tools
- Access to real firewall data from the host system
- Proper permissions for firewall and QoS operations 
- Integration with MySQL for database development
- Adminer for database management at [http://localhost:8081](http://localhost:8081)
- Volume mounts for persistent data
- Host system log and proc directory access for real-time data

## Container Structure

- `/app` - Mount point for the project code
- `/etc/charon` - Configuration directory
- `/var/log/charon` - Log directory
- `/var/lib/charon` - Data directory
- `/host/var/log` - Mount point for host system logs
- `/host/proc` - Mount point for host system information

## Environment Variables

The following environment variables are available in the development environment:

- `CHARON_DB_TYPE` - Database type (`sqlite` or `mysql`)
- `MYSQL_HOST` - MySQL hostname
- `MYSQL_PORT` - MySQL port
- `MYSQL_DATABASE` - MySQL database name
- `MYSQL_USER` - MySQL username
- `MYSQL_PASSWORD` - MySQL password
- `USE_MOCK_DATA` - Whether to use mock data (set to `false` by default)
- `USE_REAL_FIREWALL` - Whether to use real firewall data (set to `true` by default)
- `HOST_LOG_PATH` - Path to mounted host log directory
- `HOST_PROC_PATH` - Path to mounted host proc directory

## Real Firewall Data

The development environment is configured to collect and use real firewall data from your host system. This includes:

1. Actual firewall rules from iptables/nftables
2. Real network interface statistics
3. System logs for firewall events
4. Current system resource usage (CPU, memory, disk)

The dashboard will indicate whether real data is being displayed with a green success message at the top.

## Troubleshooting

### Port Conflicts

If you encounter port conflicts:

1. The default ports used are:
   - 5000: Web interface
   - 3307: MySQL (mapped from internal 3306)
   - 8081: Adminer

2. If these ports are already in use, edit the `docker-compose.dev.yml` file to change them.

### Permissions Issues

If you encounter permission issues with accessing real firewall data:

1. The Docker container runs with the `user: root` setting to ensure proper permissions
2. Check that your host system allows the Docker container to access system files
3. Verify that the volume mounts for `/var/log` and `/proc` are working correctly

### Navigation Issues

If navigation buttons in the web interface don't work:

1. Check the browser console for JavaScript errors
2. Ensure that routes in `src/web/server.py` are correctly defined for the navigation links
3. Verify that the user has proper permissions for accessing the requested pages

## Additional Resources

- [CONTRIBUTION.md](CONTRIBUTION.md) - Guidelines for contributors
- [CROSS_PLATFORM.md](CROSS_PLATFORM.md) - Information about cross-platform support
- [ROADMAP.md](ROADMAP.md) - Project roadmap and milestones
- [QOS_IMPLEMENTATION.md](QOS_IMPLEMENTATION.md) - QoS module implementation details 