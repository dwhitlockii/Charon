#!/bin/bash
# Initialize development environment for Charon

set -e

# Default values
DB_TYPE=${DB_TYPE:-sqlite}
RESET_DB=${RESET_DB:-0}
DEV_MODE=${DEV_MODE:-1}
FLASK_ENV=${FLASK_ENV:-development}
FLASK_DEBUG=${FLASK_DEBUG:-1}

echo "Initializing Charon development environment..."

# Define paths
if [ "$DB_TYPE" = "sqlite" ]; then
    DB_PATH=${DB_PATH:-/etc/charon/charon.db}
    echo "Using SQLite database at $DB_PATH"
    
    # Create DB directory if it doesn't exist
    DB_DIR=$(dirname "$DB_PATH")
    if [ ! -d "$DB_DIR" ]; then
        sudo mkdir -p "$DB_DIR"
        sudo chown -R $(whoami) "$DB_DIR"
    fi
else
    echo "Using MySQL database"
fi

# Setup database
if [ "$RESET_DB" = "1" ] || [ ! -f "$DB_PATH" ]; then
    echo "Setting up database..."
    python /app/scripts/setup_database.py
fi

# Set up content filter database
CONTENT_FILTER_DB="/etc/charon/content_filter.db"
if [ ! -f "$CONTENT_FILTER_DB" ]; then
    echo "Setting up content filter database..."
    python -c "from src.core.content_filter import ContentFilter; cf = ContentFilter(); cf.setup_database()"
fi

# Initialize QoS configuration
if sudo which tc > /dev/null 2>&1; then
    echo "Traffic Control (tc) is available for QoS testing"
    # Test interface setup
    sudo ip link add dev test0 type dummy || echo "Dummy interface already exists or not supported"
    sudo ip link set dev test0 up || echo "Failed to set dummy interface up"
fi

# Set permissions for development
sudo chown -R $(whoami) /etc/charon /var/log/charon /var/lib/charon

# Initialize config if needed
if [ ! -f "/etc/charon/config.ini" ]; then
    echo "Initializing configuration..."
    python /app/scripts/init_config.py
fi

# Print development environment info
cat << EOF
==================================
Charon Development Environment
==================================
- Python $(python --version 2>&1 | cut -d' ' -f2)
- $(pip --version)
- Flask $(pip show flask | grep Version | cut -d' ' -f2)
- Database: $DB_TYPE
- Dev Mode: $DEV_MODE
- Debug: $FLASK_DEBUG
==================================

Development commands:
- pytest -xvs                # Run tests
- python -m src.web.server   # Start web server
- python -m black .          # Format code
- python -m pylint src       # Lint code
- python -m mypy src         # Type checking

For assistance, see:
- /app/CONTRIBUTION.md
- /app/ROADMAP.md
- /app/TODO.md
==================================
EOF

# Start server if requested
if [ "$1" = "server" ]; then
    echo "Starting development server..."
    cd /app
    FLASK_ENV=$FLASK_ENV FLASK_DEBUG=$FLASK_DEBUG python -m src.web.server
elif [ "$1" = "test" ]; then
    echo "Running tests..."
    cd /app
    python -m pytest
else
    echo "Ready for development!"
    echo "Use 'python -m src.web.server' to start the web server."
fi 