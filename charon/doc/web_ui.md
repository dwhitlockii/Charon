# Web UI Documentation

## Overview

The Web UI module in Charon provides a user-friendly interface to manage the firewall through a web browser. It includes a dashboard for monitoring status, managing rules, viewing logs, and configuring various aspects of the firewall.

## Key Components

### Web Server

The web server is built with Flask and provides:

- User authentication and session management
- RESTful API endpoints for interacting with the firewall
- HTML templates for rendering the interface

### Firewall Service

The FirewallService class integrates the web UI with the firewall functionality:

- Provides methods to get firewall status, rules, and logs
- Handles adding, updating, and deleting rules
- Connects to other modules like content filtering, QoS, and plugins

## Web UI Features

### Dashboard

The dashboard provides an overview of the firewall status and recent activity:

- Current firewall status (active/inactive)
- System uptime
- Number of active rules
- Active connections
- Traffic statistics
- Quick actions (enable/disable firewall, reload rules)

### Rules Management

The rules management page allows viewing and editing firewall rules:

- List all firewall rules
- Add new rules
- Edit existing rules
- Delete rules
- Enable/disable rules

### Content Filtering

The content filtering page provides access to URL and content filtering:

- Manage filtering categories
- View blocked domains
- Add/remove domains to block
- Import external block lists

### QoS Management

The Quality of Service management page allows configuring traffic shaping:

- Set up traffic classes
- Configure bandwidth allocation
- Apply traffic priorities
- Create QoS profiles

### Scheduler

The scheduler page allows managing time-based rules:

- Schedule rules to be enabled/disabled at specific times
- Create recurring schedules
- View upcoming scheduled tasks

### Plugins

The plugins page allows managing firewall extensions:

- View available plugins
- Enable/disable plugins
- Configure plugin settings

### Logs

The logs page provides access to firewall logs and events:

- View real-time logs
- Filter logs by criteria
- Export logs

### Settings

The settings page allows configuring general firewall settings:

- User management
- Backup/restore configuration
- System settings

## Access Control

The Web UI implements role-based access control:

- **admin**: Full access to all features
- **user**: Limited access based on permissions

## Installation and Usage

### Prerequisites

- Python 3.6+
- Flask
- MySQL/MariaDB
- Web browser

### Starting the Web Server

```python
from charon.src.web import run_server

# Run the server on the default port (5000)
run_server(host='0.0.0.0', port=5000)
```

### Accessing the Web UI

Once the server is running, you can access the Web UI by navigating to:

```
http://server-ip:5000
```

Default login credentials:
- Username: admin
- Password: admin

(Make sure to change these in production)

## Security Considerations

When deploying the Web UI in production:

1. Use HTTPS by setting up SSL/TLS
2. Change default login credentials
3. Run behind a reverse proxy like Nginx or Apache
4. Configure a proper authentication system
5. Restrict access to trusted networks or use VPN

## API Endpoints

The Web UI exposes the following API endpoints:

- **GET /api/status**: Get current firewall status
- **GET /api/rules**: Get list of firewall rules
- **POST /api/rule**: Add a new firewall rule
- **PUT /api/rule/{id}**: Update an existing rule
- **DELETE /api/rule/{id}**: Delete a rule
- **GET /api/logs**: Get firewall logs

These endpoints return JSON responses and can be used for automation or integration with other systems.

## Customization

The Web UI can be customized by:

1. Modifying the HTML templates in `templates/` directory
2. Updating the CSS styles
3. Adding new routes to the Flask application
4. Extending the FirewallService class with new methods 