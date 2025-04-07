# Charon Firewall

A modern and cross-platform firewall management system with web interface and API access.

## Features

* **Web Interface** - Modern, responsive web dashboard for managing firewall settings
* **Firewall Rules Management** - Create, edit, and manage firewall rules
* **Content Filtering** - Block specific websites or categories of content
* **Quality of Service (QoS)** - Prioritize traffic based on type, source, or destination
* **Real-Time Data** - Display actual system firewall data and statistics
* **Logs and Analytics** - Track and analyze firewall events
* **User Management** - Role-based access control with admin and user accounts
* **API Access** - RESTful API for automation and integration
* **Cross-Platform** - Works on Linux and Windows (with platform-specific adapters)
* **Backup & Restore** - Save and load your firewall configuration

## Installation

### Prerequisites

* Python 3.8 or higher
* SQLite (development) or MySQL (production)
* Linux with iptables/nftables (for full functionality)
* Docker and Docker Compose (for development environment)

### Basic Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/charon.git
   cd charon
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the setup script:
   ```bash
   python setup.py
   ```

4. Start the server:
   ```bash
   python -m charon.src.web.server
   ```

5. Access the web interface at http://localhost:5000
   - Default credentials: admin/admin

## Docker Development Environment

For a quick start with a complete development environment:

1. Start the Docker environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Access the web interface at http://localhost:5000
   - Default credentials: admin/admin

3. Access the database management interface at http://localhost:8081
   - Server: charon-mysql-dev
   - Username: root
   - Password: example
   - Database: charon

The development environment includes:
- Charon application container with real firewall data from the host
- MySQL database for persistent storage
- Adminer database management interface
- All necessary tools for development

See [DEV_ENVIRONMENT.md](DEV_ENVIRONMENT.md) for more details.

## Docker Firewall Environment

For testing firewall rules in an isolated environment:

1. Start the firewall environment:
   ```bash
   docker-compose -f docker-compose.firewall.yml up -d
   ```

2. Access the web interface at http://localhost:5000
   - Default credentials: admin/admin

The firewall environment includes:
- Charon firewall container with isolated network interfaces
- Test client containers in the LAN network
- DMZ server container for testing public-facing services

See [doc/docker_setup.md](doc/docker_setup.md) for detailed information about the Docker firewall setup.

## Documentation

For more information, check out these documentation files:

* [Project Roadmap](ROADMAP.md)
* [Contribution Guidelines](CONTRIBUTION.md)
* [Security Policy](SECURITY.md)
* [Cross-Platform Support](CROSS_PLATFORM.md)
* [QoS Implementation](QOS_IMPLEMENTATION.md)
* [API Documentation](documentation.md)
* [Database Schema](doc/database.md)
* [Development Environment](DEV_ENVIRONMENT.md)
* [Docker Setup](doc/docker_setup.md)

## License

Charon Firewall is open-source software licensed under the [MIT License](LICENSE). This means you are free to use, modify, distribute, and commercialize the software with minimal restrictions. See the [LICENSE](LICENSE) file for the full terms.

## Acknowledgments

- Contributors and maintainers
- Open source libraries and tools used in this project 