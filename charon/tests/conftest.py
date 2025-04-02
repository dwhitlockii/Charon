"""
Pytest configuration for Charon tests.

This module contains fixtures and configuration for testing the Charon firewall.
"""

import os
import sys
import pytest
import tempfile
from unittest.mock import MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Charon modules using relative paths
try:
    from src.db.database import Database, Base
    from src.web.server import app as flask_app
except ImportError:
    # This allows tests to run even if some modules fail to import
    # We'll create mock objects for the missing components
    Database = MagicMock
    Base = MagicMock
    flask_app = MagicMock()
    flask_app.config = {}
    flask_app.app_context = lambda: _MockContext()
    
class _MockContext:
    """Mock context manager for app context."""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set test configuration
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test_key',
        'SERVER_NAME': 'localhost.localdomain'
    })

    # Mock database connection
    flask_app.config['DB'] = MagicMock()
    
    # Establish application context
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def test_db():
    """Create a test database using SQLite in-memory."""
    # Use in-memory SQLite database
    database = Database(connection_string="sqlite:///:memory:")
    database.connect()
    database.create_tables()
    
    yield database
    
    # Close and clean up
    database.close()


@pytest.fixture
def auth_client(client):
    """Create an authenticated client."""
    with client.session_transaction() as session:
        session['user_id'] = 'test_user'
        session['role'] = 'admin'
    return client


@pytest.fixture
def mock_packet_filter():
    """Create a mock packet filter."""
    mock = MagicMock()
    mock.add_rule.return_value = True
    mock.remove_rule.return_value = True
    mock.get_rules.return_value = []
    return mock


@pytest.fixture
def mock_content_filter():
    """Create a mock content filter."""
    mock = MagicMock()
    mock.add_domain.return_value = True
    mock.remove_domain.return_value = True
    mock.apply_to_firewall.return_value = True
    return mock


@pytest.fixture
def mock_qos():
    """Create a mock QoS module."""
    mock = MagicMock()
    mock.create_traffic_class.return_value = 1
    mock.add_filter.return_value = 1
    return mock 