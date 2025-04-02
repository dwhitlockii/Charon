# API Documentation

## Overview

The API module in Charon provides a RESTful API for external applications to interact with the firewall. It allows for programmatic control of firewall settings, rules, and other features.

## Authentication

The API uses token-based authentication with JWT (JSON Web Tokens). To access the API:

1. Obtain an API key from the administrator
2. Use the API key to request a JWT token
3. Include the JWT token in all subsequent requests

### Getting a Token

```
POST /api/v1/auth/token
Header: X-API-Key: <your_api_key>
Body: {"expires_in": 3600}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### Using a Token

Include the JWT token in the Authorization header of all API requests:

```
Header: Authorization: Bearer <jwt_token>
```

## API Endpoints

### Firewall Status

#### Get Firewall Status

```
GET /api/v1/status
```

Response:
```json
{
  "status": "active",
  "timestamp": 1632512345
}
```

### Firewall Rules

#### List Rules

```
GET /api/v1/rules
```

Optional query parameters:
- `chain`: Filter by chain (e.g., input, output)
- `action`: Filter by action (e.g., accept, drop)
- `enabled`: Filter by enabled status (true/false)

Response:
```json
{
  "rules": [
    {
      "id": 1,
      "chain": "input",
      "action": "accept",
      "protocol": "tcp",
      "dst_port": "22",
      "description": "Allow SSH",
      "enabled": true
    }
  ]
}
```

#### Get a Specific Rule

```
GET /api/v1/rules/{rule_id}
```

Response:
```json
{
  "rule": {
    "id": 1,
    "chain": "input",
    "action": "accept",
    "protocol": "tcp",
    "dst_port": "22",
    "description": "Allow SSH",
    "enabled": true
  }
}
```

#### Add a Rule

```
POST /api/v1/rules
Body: {
  "chain": "input",
  "action": "accept",
  "protocol": "tcp",
  "dst_port": "80",
  "description": "Allow HTTP"
}
```

Response:
```json
{
  "success": true,
  "id": 2
}
```

#### Update a Rule

```
PUT /api/v1/rules/{rule_id}
Body: {
  "action": "drop",
  "description": "Block HTTP"
}
```

Response:
```json
{
  "success": true
}
```

#### Delete a Rule

```
DELETE /api/v1/rules/{rule_id}
```

Response:
```json
{
  "success": true
}
```

### Logs

#### Get Logs

```
GET /api/v1/logs
```

Optional query parameters:
- `limit`: Maximum number of logs to return (default: 100)
- `action`: Filter by action
- `src_ip`: Filter by source IP
- `dst_ip`: Filter by destination IP

Response:
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2023-09-25T12:34:56",
      "action": "drop",
      "protocol": "tcp",
      "src_ip": "192.168.1.100",
      "dst_ip": "10.0.0.1",
      "dst_port": "80"
    }
  ]
}
```

### Content Filter

#### Get Categories

```
GET /api/v1/content-filter/categories
```

Response:
```json
{
  "categories": [
    {
      "name": "adult",
      "description": "Adult content and pornography",
      "enabled": true,
      "domain_count": 1500
    }
  ]
}
```

#### Get Domains in a Category

```
GET /api/v1/content-filter/domains?category=adult
```

Response:
```json
{
  "domains": [
    "example1.com",
    "example2.com"
  ]
}
```

#### Add a Domain

```
POST /api/v1/content-filter/domains
Body: {
  "domain": "example.com",
  "category": "adult"
}
```

Response:
```json
{
  "success": true
}
```

#### Apply Content Filter

```
POST /api/v1/content-filter/apply
```

Response:
```json
{
  "success": true
}
```

### QoS (Quality of Service)

#### Get QoS Profiles

```
GET /api/v1/qos/profiles
```

Response:
```json
{
  "profiles": [
    {
      "id": "default",
      "name": "Default Profile"
    },
    {
      "id": "gaming",
      "name": "Gaming Profile"
    }
  ]
}
```

#### Set Up QoS

```
POST /api/v1/qos/setup
Body: {
  "profile": "default"
}
```

Response:
```json
{
  "success": true
}
```

### Plugins

#### List Plugins

```
GET /api/v1/plugins
```

Response:
```json
{
  "plugins": {
    "hello_world": {
      "name": "Hello World",
      "description": "A simple example plugin",
      "enabled": false,
      "loaded": true
    }
  }
}
```

#### Enable a Plugin

```
POST /api/v1/plugins/{plugin_name}/enable
```

Response:
```json
{
  "success": true
}
```

#### Disable a Plugin

```
POST /api/v1/plugins/{plugin_name}/disable
```

Response:
```json
{
  "success": true
}
```

### Scheduler

#### List Scheduled Tasks

```
GET /api/v1/scheduler/tasks
```

Response:
```json
{
  "tasks": [
    {
      "name": "enable_ssh",
      "enabled": true,
      "start_time": "2023-09-25T08:00:00",
      "end_time": "2023-09-25T17:00:00",
      "days": [0, 1, 2, 3, 4],
      "interval": null,
      "last_run": "2023-09-25T08:00:00"
    }
  ]
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include an error message:

```json
{
  "error": "Rule not found: 123"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Each API key is limited to 100 requests per minute. If you exceed this limit, you will receive a `429 Too Many Requests` response.

## Usage Examples

### Python Example

```python
import requests
import json

# API base URL
base_url = "http://firewall-server:5000/api/v1"

# Get a token
api_key = "your_api_key"
response = requests.post(
    f"{base_url}/auth/token",
    headers={"X-API-Key": api_key},
    json={"expires_in": 3600}
)
token = response.json()["token"]

# Use the token to get firewall status
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{base_url}/status", headers=headers)
status = response.json()["status"]
print(f"Firewall status: {status}")

# Add a rule
rule_data = {
    "chain": "input",
    "action": "accept",
    "protocol": "tcp",
    "dst_port": "80",
    "description": "Allow HTTP"
}
response = requests.post(f"{base_url}/rules", headers=headers, json=rule_data)
rule_id = response.json()["id"]
print(f"Added rule with ID: {rule_id}")
```

### Curl Example

```bash
# Get a token
curl -X POST "http://firewall-server:5000/api/v1/auth/token" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"expires_in": 3600}'

# Use the token to get firewall status
curl -X GET "http://firewall-server:5000/api/v1/status" \
  -H "Authorization: Bearer your_jwt_token"

# Add a rule
curl -X POST "http://firewall-server:5000/api/v1/rules" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "input",
    "action": "accept",
    "protocol": "tcp",
    "dst_port": "80",
    "description": "Allow HTTP"
  }'
``` 