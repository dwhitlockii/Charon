# Charon - Advanced Cross-Platform Firewall

Charon is a state-of-the-art firewall application that is secure, modular, and user-friendly. It supports both Linux and Windows platforms with platform-specific adapters.

## Core Features

- **Security & Packet Filtering**: Uses nftables/iptables on Linux and Windows Firewall API
- **Modular Architecture**: Plugin system for extending functionality
- **Quality of Service (QoS)**: Traffic shaping and bandwidth management
- **Family Filters & Content Control**: URL blocking and content filtering
- **Database Integration**: Supports both SQLite (development) and MySQL/MariaDB (production)
- **Time Scheduling**: Time-based access control rules
- **Web UI & Dashboard**: Modern web interface for management with:
  - Dark/Light mode support
  - Customizable dashboard widgets
  - Interactive traffic visualization
  - Real-time system monitoring
  - Toast notifications for system events
- **API Integration**: RESTful API for automation

## Project Structure

```
charon/
├── src/                    # Source code
│   ├── core/               # Core firewall functionality
│   ├── plugins/            # Plugin system and plugins
│   ├── db/                 # Database integration
│   ├── api/                # RESTful API
│   ├── web/                # Web UI
│   └── scheduler/          # Time-based scheduling
├── doc/                    # Documentation
├── tests/                  # Test suite
├── scripts/                # Utility scripts2

└── data/                   # Data storage directory
```

## Setup Instructions

1. Ensure you have the following dependencies installed:
   - Python 3.8+
   - For Linux: nftables/iptables package
   - For Windows: PowerShell 5.0+ and Administrator privileges
   - MySQL/MariaDB (optional, for production)

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/charon.git
   cd charon
   ```

3. Create a .env file based on .env.example:
   ```
   cp .env.example .env
   # Edit the .env file with your preferred settings
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the setup script:
   ```
   python -m charon.src.web.server
   ```

6. Access the web interface at http://localhost:5000
   - Default credentials will be displayed during first-time setup

## Docker Development Environment

For a quick start with Docker:

```
docker-compose up -d
```

See [DEV_ENVIRONMENT.md](charon/DEV_ENVIRONMENT.md) for more details.

## Development Workflow

- Work in small, testable increments
- Update documentation with each feature
- Follow the guidelines in [CONTRIBUTION.md](charon/CONTRIBUTION.md)

## UI Features

The Charon web interface includes:

- **Modern Dashboard**:
  - Draggable and customizable widgets
  - Real-time system status monitoring
  - Interactive traffic charts
  - Quick action buttons
  - Recent activity log

- **Theme System**:
  - Light/Dark mode support
  - Persistent theme preferences
  - Smooth transitions
  - Consistent styling across components

- **Interactive Elements**:
  - Toast notifications for system events
  - Progress bars for resource usage
  - Collapsible sidebar
  - Responsive design for all devices

- **Data Visualization**:
  - Real-time traffic graphs
  - System resource monitoring
  - Connection statistics
  - Blocked traffic analysis 