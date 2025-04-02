# Charon - Advanced Linux Firewall

Charon is a state-of-the-art Linux firewall application that is secure, modular, and user-friendly.

## Core Features

- **Security & Packet Filtering**: Uses nftables for stateful packet filtering
- **Modular Architecture**: Plugin system for extending functionality
- **Quality of Service (QoS)**: Traffic shaping and bandwidth management
- **Family Filters & Content Control**: URL blocking and content filtering
- **MySQL Database Integration**: Logging firewall events and storing configurations
- **Time Scheduling & NTP**: Time-based access control rules
- **Web UI & Dashboard**: React-based web interface for management
- **API Integration**: RESTful API for automation

## Project Structure

```
charon/
├── src/                    # Source code
│   ├── core/               # Core firewall functionality
│   ├── plugins/            # Plugin system and plugins
│   ├── db/                 # Database integration
│   ├── api/                # RESTful API
│   └── web/                # Web UI
├── doc/                    # Documentation
├── tests/                  # Test suite
└── scripts/                # Utility scripts
```

## Setup Instructions

1. Ensure you have the following dependencies installed:
   - Linux kernel 4.x or later
   - nftables (or iptables) package
   - MySQL/MariaDB
   - Python 3.8+

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/charon.git
   cd charon
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run setup script:
   ```
   ./scripts/setup.sh
   ```

## Development Workflow

- Work in small, testable increments (20-30 lines of code at a time)
- Update documentation with each feature
- Commit code frequently to maintain traceability 