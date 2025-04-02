# Database Module Documentation

## Overview

The Database module provides functionality to interact with a MySQL database for storing firewall rules, logs, and configuration settings. It uses SQLAlchemy as an ORM (Object-Relational Mapping) framework to abstract the database operations.

## Key Components

### Database Models

The module defines the following database models:

1. **FirewallRule**: Represents a firewall rule with properties like chain, action, protocol, IP addresses, and ports.
2. **FirewallLog**: Stores log entries for firewall events.
3. **ConfigSetting**: Stores configuration settings organized by section and key.

### Database Manager

The `Database` class provides methods to:

- Connect to the database
- Create database tables
- Manage firewall rules (add, update, delete, get)
- Store and retrieve logs
- Manage configuration settings

## Database Schema

### FirewallRule Table

| Column      | Type      | Description                       |
|-------------|-----------|-----------------------------------|
| id          | Integer   | Primary key                       |
| chain       | String    | Firewall chain (input, output, etc.) |
| action      | String    | Action (accept, drop, reject)     |
| protocol    | String    | Network protocol (tcp, udp, etc.) |
| src_ip      | String    | Source IP address                 |
| dst_ip      | String    | Destination IP address            |
| src_port    | String    | Source port                       |
| dst_port    | String    | Destination port                  |
| description | Text      | Rule description                  |
| enabled     | Boolean   | Whether the rule is enabled       |
| created_at  | DateTime  | When the rule was created         |
| updated_at  | DateTime  | When the rule was last updated    |

### FirewallLog Table

| Column      | Type      | Description                       |
|-------------|-----------|-----------------------------------|
| id          | Integer   | Primary key                       |
| timestamp   | DateTime  | When the event occurred           |
| chain       | String    | Firewall chain                    |
| action      | String    | Action taken                      |
| protocol    | String    | Network protocol                  |
| src_ip      | String    | Source IP address                 |
| dst_ip      | String    | Destination IP address            |
| src_port    | String    | Source port                       |
| dst_port    | String    | Destination port                  |
| rule_id     | Integer   | ID of the rule that matched (optional) |

### ConfigSetting Table

| Column      | Type      | Description                       |
|-------------|-----------|-----------------------------------|
| id          | Integer   | Primary key                       |
| section     | String    | Configuration section             |
| key         | String    | Setting key                       |
| value       | Text      | Setting value                     |
| description | Text      | Setting description               |
| created_at  | DateTime  | When the setting was created      |
| updated_at  | DateTime  | When the setting was last updated |

## Usage

### Connecting to the Database

```python
from charon.src.db.database import Database

# Connect to the database using environment variables
db = Database()
db.connect()

# Or specify a connection string directly
db = Database("mysql+mysqldb://user:password@localhost:3306/charon")
db.connect()

# Create tables if they don't exist
db.create_tables()
```

### Managing Firewall Rules

```python
# Add a rule
rule_id = db.add_rule(
    chain="INPUT",
    action="ACCEPT",
    protocol="TCP",
    dst_port="80",
    description="Allow HTTP"
)

# Get all rules
rules = db.get_rules()

# Get filtered rules
rules = db.get_rules({"chain": "INPUT", "action": "ACCEPT"})

# Update a rule
db.update_rule(1, {"enabled": False, "description": "Updated description"})

# Delete a rule
db.delete_rule(1)

# Clear all rules
db.clear_rules()
```

### Managing Configuration Settings

```python
# Set a configuration value
db.set_config("network", "interface", "eth0")

# Get a configuration value (with default)
interface = db.get_config("network", "interface", "eth0")

# Get all settings in a section
network_settings = db.get_config_section("network")

# Get all configuration settings
all_settings = db.get_all_config()
```

### User Management

```python
# Add a user
user_id = db.add_user("admin", "password123", role="admin", email="admin@example.com")

# Get a user by username
user = db.get_user("admin")

# Verify a user's password
if db.verify_password("admin", "password123"):
    print("Password is correct")

# Update a user's password
db.update_user_password("admin", "newpassword")

# Update a user
db.update_user("admin", {"email": "new.email@example.com"})

# Delete a user
db.delete_user("admin")
```

### Managing Logs

```python
# Add a log entry
log_id = db.add_log({
    "timestamp": datetime.datetime.now(),
    "action": "DROP",
    "src_ip": "192.168.1.100",
    "dst_ip": "8.8.8.8",
    "protocol": "TCP",
    "dst_port": "443"
})

# Get logs (with optional filtering and limit)
logs = db.get_logs({"action": "DROP"}, limit=100)
```

## Environment Variables

The database connection can be configured using the following environment variables:

- `CHARON_DB_HOST`: Database hostname (default: "localhost")
- `CHARON_DB_PORT`: Database port (default: "3306")
- `CHARON_DB_USER`: Database username (default: "charon")
- `CHARON_DB_PASSWORD`: Database password (default: "")
- `CHARON_DB_NAME`: Database name (default: "charon")

## Requirements

- MySQL/MariaDB server
- Python MySQL connector (mysqlclient)
- SQLAlchemy 