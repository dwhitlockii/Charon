# Charon Firewall Documentation

## Overview

Charon is a web-based firewall management system that provides an intuitive interface for managing firewall rules, monitoring network traffic, and configuring security policies. It can be run in docker containers for development and testing, or installed directly on a Linux server for production use.

## Features

- **Firewall Rule Management**: Create, edit, and manage iptables/nftables firewall rules.
- **Content Filtering**: Block unwanted websites and content categories.
- **Quality of Service (QoS)**: Prioritize network traffic for critical applications.
- **Real-time Monitoring**: Monitor network traffic and firewall events.
- **User Authentication**: Secure access with user accounts and roles.
- **Web Interface**: Modern, responsive web interface for easy management.
- **API Access**: RESTful API for automation and integration.
- **Backup & Restore**: Save and restore firewall configurations.

## Web Interface

The web interface provides access to all Charon features:

- **Dashboard**: Overview of system status, recent logs, and statistics.
- **Firewall Rules**: Manage firewall rules and policies.
- **Content Filter**: Configure content filtering for blocking unwanted content.
- **QoS**: Set up traffic prioritization and bandwidth control.
- **Logs**: View and analyze firewall logs.
- **Settings**: Configure system settings and manage user accounts.

## API Endpoints

Charon provides a RESTful API for programmatic control. All API endpoints require authentication.

### Status & Information

- `GET /api/status`: Get system status information.
- `GET /api/logs`: Get recent firewall logs.
- `GET /api/rules`: Get all firewall rules.

### Firewall Management

- `POST /api/rules`: Create a new firewall rule.
- `PUT /api/rules/<id>`: Update a firewall rule.
- `DELETE /api/rules/<id>`: Delete a firewall rule.

### Content Filter

- `POST /api/content_filter/toggle`: Toggle content filter on/off.
- `GET /api/content_filter/categories`: List all content filter categories.
- `POST /api/content_filter/categories`: Create a new category.
- `GET /api/content_filter/categories/<id>`: Get a specific category.
- `PUT /api/content_filter/categories/<id>`: Update a category.
- `DELETE /api/content_filter/categories/<id>`: Delete a category.
- `POST /api/content_filter/categories/<id>/toggle`: Toggle a category on/off.

### QoS Management

- `POST /api/qos/toggle`: Toggle QoS on/off.
- `POST /api/qos/bandwidth`: Update bandwidth settings.
- `GET /api/qos/classes`: List all traffic classes.
- `POST /api/qos/classes`: Create a new traffic class.
- `GET /api/qos/classes/<id>`: Get a specific traffic class.
- `PUT /api/qos/classes/<id>`: Update a traffic class.
- `DELETE /api/qos/classes/<id>`: Delete a traffic class.
- `GET /api/qos/rules`: List all QoS rules.
- `POST /api/qos/rules`: Create a new QoS rule.
- `GET /api/qos/rules/<id>`: Get a specific QoS rule.
- `PUT /api/qos/rules/<id>`: Update a QoS rule.
- `DELETE /api/qos/rules/<id>`: Delete a QoS rule.
- `PATCH /api/qos/rules/<id>/toggle`: Toggle a QoS rule on/off.

### User Management

- `POST /api/change_password`: Change current user's password.
- `GET /api/users`: List all users (admin only).
- `POST /api/users`: Create a new user (admin only).
- `DELETE /api/users/<username>`: Delete a user (admin only).
- `POST /api/admin/change-password`: Change another user's password (admin only).

### System Settings

- `POST /api/settings`: Update system settings.
- `GET /api/backup/download`: Download a backup of settings.
- `POST /api/backup/restore`: Restore from a backup file.
- `POST /api/factory_reset`: Reset to factory defaults.

## Database

Charon can use either SQLite (for development) or MySQL (for production) as its database backend. The database stores:

- Firewall rules
- Content filter configuration
- QoS configuration
- User accounts
- Firewall logs
- System settings

For more details on the database schema and usage, see `doc/database.md`.

## Development Environment

Charon includes a Docker-based development environment that provides:

1. Charon application container
2. MySQL database container
3. Adminer database management interface

For development setup instructions, see `DEV_ENVIRONMENT.md`.

## Customization

### Templates

All web interface templates are located in `src/web/templates/`. They use the Jinja2 templating language and can be customized as needed.

### Static Files

Static assets (CSS, JavaScript, images) are located in `src/web/static/`.

## Security Considerations

- Charon should be installed behind a secure reverse proxy for production use.
- Strong passwords should be used for all accounts.
- Regular backups of the configuration are recommended.
- Keep the system updated with security patches.

## Troubleshooting

Common issues and their solutions:

- **Connection refused**: Check if the Charon service is running.
- **Authentication failure**: Verify username and password.
- **Rules not applied**: Check if the firewall service is active and verify permissions.
- **Database errors**: Check database connection settings.
- **Navigation errors**: Ensure all routes and API endpoints are functioning.

For more troubleshooting information, consult the logs in the Charon container. 