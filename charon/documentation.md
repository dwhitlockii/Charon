# Charon Firewall - Documentation

## Overview

Charon is a cross-platform firewall management system with a web interface and API access. It supports Linux (using nftables/iptables) and Windows (using Windows Firewall API) through platform-specific adapters.

## Architecture

Charon follows a modular architecture with the following components:

1. **Core Firewall Engine**: Handles packet filtering, content filtering, and QoS
2. **Database Layer**: Stores configurations, rules, and logs
3. **Web Interface**: User-friendly dashboard for management
4. **API**: RESTful endpoints for automation
5. **Plugin System**: Extensibility through custom plugins
6. **Scheduler**: Time-based rule activation/deactivation

## API Documentation

### Authentication

All API endpoints require authentication. The API uses session-based authentication shared with the web interface.

### Endpoints

#### Status

```
GET /api/status
```

Returns the current status of the firewall system.

**Response**
```json
{
  "status": "active",
  "uptime": "up 3 days, 2 hours",
  "rules_active": 12,
  "connections": 24,
  "plugins_loaded": 3
}
```

#### Firewall Rules

```
GET /api/rules
```

Returns a list of all firewall rules.

**Response**
```json
[
  {
    "id": 1,
    "chain": "input",
    "action": "accept",
    "protocol": "tcp",
    "src_ip": "192.168.1.0/24",
    "dst_ip": null,
    "src_port": null,
    "dst_port": "80",
    "description": "Allow HTTP traffic from LAN",
    "enabled": true
  }
]
```

```
POST /api/rules
```

Creates a new firewall rule.

**Request Body**
```json
{
  "chain": "input",
  "action": "accept",
  "protocol": "tcp",
  "src_ip": "192.168.1.0/24",
  "dst_port": "80",
  "description": "Allow HTTP traffic from LAN"
}
```

```
GET /api/rules/{id}
```

Returns a specific rule by ID.

```
PUT /api/rules/{id}
```

Updates a specific rule.

```
DELETE /api/rules/{id}
```

Deletes a specific rule.

```
PATCH /api/rules/{id}/toggle
```

Toggles a rule's enabled status.

#### Content Filtering

```
GET /api/content_filter/categories
```

Returns all content filter categories.

```
POST /api/content_filter/categories
```

Creates a new category.

```
GET /api/content_filter/categories/{id}
```

Returns a specific category.

```
PUT /api/content_filter/categories/{id}
```

Updates a specific category.

```
DELETE /api/content_filter/categories/{id}
```

Deletes a specific category.

```
POST /api/content_filter/toggle
```

Toggles content filtering on/off.

#### QoS

```
POST /api/qos/toggle
```

Toggles QoS on/off.

#### Logs

```
GET /api/logs
```

Returns firewall logs.

**Query Parameters**
- `limit`: Maximum number of logs to return (default: 100)
- `offset`: Pagination offset
- `type`: Log type filter (e.g., "block", "allow")

#### Users

```
POST /api/users
```

Creates a new user.

```
DELETE /api/users/{username}
```

Deletes a user.

```
POST /api/change_password
```

Changes the current user's password.

```
POST /api/admin/change-password
```

Allows an admin to change another user's password.

#### Settings

```
POST /api/settings
```

Updates system settings.

#### Backup & Restore

```
GET /api/backup/download
```

Downloads a backup of the current configuration.

```
POST /api/backup/restore
```

Restores a configuration from a backup file.

#### Factory Reset

```
POST /api/factory_reset
```

Resets the system to factory settings.

## Configuration

Charon uses environment variables for configuration. These can be set in a `.env` file in the root directory.

### Database Configuration

- `CHARON_DB_TYPE`: Database type (`sqlite` or `mysql`)
- `CHARON_DB_PATH`: Path to SQLite database file (when using SQLite)
- `MYSQL_HOST`: MySQL host (when using MySQL)
- `MYSQL_PORT`: MySQL port
- `MYSQL_DATABASE`: MySQL database name
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password

### Web Server Configuration

- `CHARON_HOST`: Host to bind the web server (default: `0.0.0.0`)
- `CHARON_PORT`: Port for the web server (default: `5000`)
- `CHARON_DEBUG`: Enable debug mode (default: `false`)
- `CHARON_SECRET_KEY`: Secret key for sessions (auto-generated if not set)
- `CHARON_SECURE_COOKIES`: Use secure cookies (default: `false`)

### Firewall Configuration

- `CHARON_PLATFORM`: Platform type (`linux` or `windows`)
- `CHARON_FIREWALL_TABLES`: Comma-separated list of firewall tables (Linux)
- `CHARON_CONTENT_FILTER_ENABLED`: Enable content filtering (default: `true`)
- `CHARON_QOS_ENABLED`: Enable QoS (default: `false`)
- `CHARON_QOS_DEFAULT_BANDWIDTH`: Default bandwidth limit for QoS (default: `10Mbit`)

## Setup Guide

### Prerequisites

- Python 3.8 or higher
- For Linux: nftables/iptables
- For Windows: PowerShell 5.0+ and Administrator privileges
- Database: SQLite (included) or MySQL/MariaDB

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure as needed
3. Install Python dependencies: `pip install -r requirements.txt`
4. Start the server: `python -m charon.src.web.server`
5. Access the web interface at `http://localhost:5000`

## Docker Deployment

Charon can be deployed using Docker:

```bash
docker-compose up -d
```

This will start:
- The Charon application container
- A MySQL database (if configured)
- All necessary services

## Plugins

Charon supports plugins to extend functionality. Plugins are placed in the `src/plugins` directory.

### Creating a Plugin

A plugin is a Python module with a class that inherits from `BasePlugin`:

```python
from charon.src.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("My Plugin", "1.0.0")
    
    def initialize(self):
        # Setup plugin
        return True
    
    def on_rule_add(self, rule):
        # Called when a rule is added
        pass
    
    def on_rule_delete(self, rule_id):
        # Called when a rule is deleted
        pass
```

## Troubleshooting

### Database Connection Issues

1. Check database credentials in `.env` file
2. Ensure the database server is running
3. Verify network connectivity

### Firewall Not Applying Rules

1. Check if the user has sufficient privileges
2. Verify that the appropriate firewall service is installed
3. Check the logs for detailed error messages

### Docker Container Issues

#### DNS Resolution Problems
If you encounter DNS resolution issues in the container (e.g., package installation failures), try the following:

1. Check the container's DNS configuration:
   ```bash
   docker exec charon-firewall cat /etc/resolv.conf
   ```

2. If using WSL, ensure proper network connectivity:
   ```bash
   wsl --list --verbose
   ```

3. Try using alternative DNS servers in the Dockerfile:
   ```dockerfile
   RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
       echo "nameserver 8.8.4.4" >> /etc/resolv.conf
   ```

#### Container Restart Issues
If the container keeps restarting:

1. Check container logs:
   ```bash
   docker logs charon-firewall
   ```

2. Common issues:
   - Missing dependencies (check requirements.txt)
   - Network namespace issues
   - Firewall rules file permissions

3. Verify container status:
   ```bash
   docker ps -a
   ```

#### Network Configuration
The firewall container requires specific network setup:

1. Ensure proper network mode in docker-compose:
   ```yaml
   network_mode: host
   privileged: true
   ```

2. Required volumes:
   ```yaml
   volumes:
     - /var/run/netns:/var/run/netns
   ```

3. DNS configuration:
   ```yaml
   dns:
     - 8.8.8.8
     - 8.8.4.4
   dns_search: .
   ```

## Support

For support, please:
1. Check the documentation
2. Look for similar issues in the issue tracker
3. Open a new issue if needed

## Dashboard

The Charon dashboard provides real-time information about the firewall system:

### System Status

The dashboard displays actual system status by checking:

1. **Firewall Status**: Performs platform-specific checks to verify if the firewall is actually active
   - On Linux: Checks for nftables/iptables rules
   - On Windows: Verifies Windows Firewall profiles are enabled

2. **Content Filter Status**: Verifies if content filtering is active
   - On Linux: Checks hosts file and dnsmasq configuration
   - On Windows: Checks DNS client rules

3. **QoS Status**: Confirms if traffic shaping is enabled
   - On Linux: Checks traffic control (tc) rules
   - On Windows: Verifies QoS policies

4. **System Resource Usage**: Shows real-time CPU, memory, and disk usage

The dashboard always displays the actual system state rather than relying solely on saved configuration settings. This ensures that what you see reflects the actual protection status of your system.

---

Documentation last updated: April 3, 2024 