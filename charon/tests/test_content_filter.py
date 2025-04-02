"""
Tests for the content_filter module.
"""

import pytest
import os
import tempfile
import platform
from unittest.mock import patch, MagicMock
from charon.src.core.content_filter import ContentFilter


def test_init():
    """Test ContentFilter initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Check if database is created
        assert os.path.exists(db_path)
        
        # Check default tables
        conn = content_filter.conn
        assert conn is not None
        cursor = conn.cursor()
        
        # Check categories table
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        assert count > 0  # Default categories should be created
        
        # Check domains table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='domains'")
        result = cursor.fetchone()
        assert result is not None


def test_platform_specific_init():
    """Test platform-specific initialization."""
    # Test without explicitly setting a path
    with patch('platform.system', return_value='Windows'):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict('os.environ', {'LOCALAPPDATA': temp_dir}):
                content_filter = ContentFilter()
                expected_path = os.path.join(temp_dir, 'Charon', 'content_filter.db')
                assert content_filter.db_path == expected_path
    
    # Test Linux path
    with patch('platform.system', return_value='Linux'):
        content_filter = ContentFilter()
        assert content_filter.db_path == "/etc/charon/content_filter.db"


def test_add_category():
    """Test adding a new category."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add new category
        result = content_filter.add_category('Test Category', 'Test category description', False)
        assert result is True
        
        # Verify it was added
        conn = content_filter.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE name=?", ('Test Category',))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'Test Category'  # name
        assert result[2] == 'Test category description'  # description
        assert result[3] == 0  # enabled (False)


def test_enable_category():
    """Test enabling and disabling a category."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add new category
        content_filter.add_category('Test Category', 'Test category description', False)
        
        # Enable category
        result = content_filter.enable_category('Test Category', True)
        assert result is True
        
        # Verify it's enabled
        conn = content_filter.conn
        cursor = conn.cursor()
        cursor.execute("SELECT enabled FROM categories WHERE name=?", ('Test Category',))
        enabled = cursor.fetchone()[0]
        assert enabled == 1  # True
        
        # Disable category
        result = content_filter.enable_category('Test Category', False)
        assert result is True
        
        # Verify it's disabled
        cursor.execute("SELECT enabled FROM categories WHERE name=?", ('Test Category',))
        enabled = cursor.fetchone()[0]
        assert enabled == 0  # False


def test_get_categories():
    """Test retrieving categories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add categories
        content_filter.add_category('Category 1', 'First test category', True)
        content_filter.add_category('Category 2', 'Second test category', False)
        
        # Get all categories
        all_categories = content_filter.get_categories()
        # Default categories + 2 new ones
        assert len(all_categories) >= 2
        
        # Check enabled filter
        enabled_categories = content_filter.get_categories(enabled_only=True)
        for category in enabled_categories:
            assert category['enabled'] == 1


def test_add_domain():
    """Test adding a domain to a category."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add category
        content_filter.add_category('Test Category', 'Test category', True)
        
        # Add domain
        result = content_filter.add_domain('example.com', 'Test Category')
        assert result is True
        
        # Verify it was added
        conn = content_filter.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM domains WHERE domain=?", ('example.com',))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 'example.com'  # domain
        assert result[2] == 'Test Category'  # category


def test_normalize_domain():
    """Test domain normalization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Test various formats
        assert content_filter._normalize_domain('http://example.com') == 'example.com'
        assert content_filter._normalize_domain('https://www.example.com') == 'example.com'
        assert content_filter._normalize_domain('www.example.com/page') == 'example.com'
        assert content_filter._normalize_domain('EXAMPLE.COM') == 'example.com'


def test_remove_domain():
    """Test removing a domain."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add category
        content_filter.add_category('Test Category', 'Test category', True)
        
        # Add domain
        content_filter.add_domain('example.com', 'Test Category')
        
        # Remove domain
        result = content_filter.remove_domain('example.com')
        assert result is True
        
        # Verify it was removed
        conn = content_filter.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM domains WHERE domain=?", ('example.com',))
        result = cursor.fetchone()
        
        assert result is None


def test_get_domains():
    """Test retrieving domains."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add categories
        content_filter.add_category('Category 1', 'First test category', True)
        content_filter.add_category('Category 2', 'Second test category', True)
        
        # Add domains
        content_filter.add_domain('example1.com', 'Category 1')
        content_filter.add_domain('example2.com', 'Category 1')
        content_filter.add_domain('example3.com', 'Category 2')
        
        # Get all domains
        all_domains = content_filter.get_domains()
        assert len(all_domains) >= 3
        
        # Get domains by category
        category1_domains = content_filter.get_domains_by_category('Category 1')
        assert len(category1_domains) == 2
        
        category2_domains = content_filter.get_domains_by_category('Category 2')
        assert len(category2_domains) == 1


def test_is_domain_blocked():
    """Test checking if a domain is blocked."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add category and domains
        content_filter.add_category('Test', 'Test category', True)
        content_filter.add_domain('example.com', 'Test')
        content_filter.add_domain('*.test.com', 'Test')
        
        # Test exact match
        assert content_filter.is_domain_blocked('example.com') is True
        assert content_filter.is_domain_blocked('other.com') is False
        
        # Test wildcard match
        assert content_filter.is_domain_blocked('sub.test.com') is True
        assert content_filter.is_domain_blocked('deep.sub.test.com') is True


def test_get_blocked_domains():
    """Test getting blocked domains from enabled categories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Add categories
        content_filter.add_category('Enabled', 'Enabled category', True)
        content_filter.add_category('Disabled', 'Disabled category', False)
        
        # Add domains
        content_filter.add_domain('enabled1.com', 'Enabled')
        content_filter.add_domain('enabled2.com', 'Enabled')
        content_filter.add_domain('disabled1.com', 'Disabled')
        
        # Get blocked domains
        domains = content_filter._get_blocked_domains()
        
        # Should only include domains from enabled categories
        assert 'enabled1.com' in domains
        assert 'enabled2.com' in domains
        assert 'disabled1.com' not in domains


@patch('subprocess.run')
@patch('platform.system', return_value='Linux')
def test_apply_to_nftables(mock_platform, mock_run):
    """Test applying filters to nftables (Linux)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Configure mock
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test with empty domains list
        result = content_filter._apply_to_nftables([], 'test-table')
        assert result is False
        
        # Test with domains
        domains = ['example1.com', 'example2.com']
        result = content_filter._apply_to_nftables(domains, 'test-table')
        
        # Verify result
        assert result is True
        
        # Check that subprocess.run was called multiple times
        assert mock_run.call_count >= 3
        
        # Verify command structure for nftables
        for call in mock_run.call_args_list:
            args = call[0][0]
            if len(args) > 3 and args[0] == 'nft':
                # Should be a valid nftables command
                assert args[1] in ['add', 'delete']


@patch('subprocess.run')
@patch('platform.system', return_value='Windows')
def test_apply_to_windows_firewall(mock_platform, mock_run):
    """Test applying filters to Windows firewall."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Configure mock
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test with domains
        domains = ['example1.com', 'example2.com']
        result = content_filter._apply_to_windows_firewall(domains)
        
        # Verify result
        assert result is True
        
        # Check that subprocess.run was called for each domain (plus delete rule)
        assert mock_run.call_count >= len(domains) + 1
        
        # Verify command structure for Windows firewall
        netsh_calls = 0
        for call in mock_run.call_args_list:
            args = call[0][0]
            if len(args) > 1 and args[0] == 'netsh':
                netsh_calls += 1
                # Should be a valid netsh command
                assert 'advfirewall' in args
                assert 'firewall' in args
        
        # Should have at least one netsh command
        assert netsh_calls > 0


@patch('platform.system', return_value='Linux')
@patch('charon.src.core.content_filter.ContentFilter._apply_to_nftables')
@patch('charon.src.core.content_filter.ContentFilter._get_blocked_domains')
def test_apply_to_firewall_linux(mock_get_domains, mock_apply_nft, mock_platform):
    """Test applying filters to the firewall on Linux."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Configure mocks
        mock_get_domains.return_value = ['example1.com', 'example2.com']
        mock_apply_nft.return_value = True
        
        # Apply to firewall
        result = content_filter.apply_to_firewall('test-table')
        
        # Verify result
        assert result is True
        
        # Verify that the appropriate methods were called
        mock_get_domains.assert_called_once()
        mock_apply_nft.assert_called_once_with(['example1.com', 'example2.com'], 'test-table')


@patch('platform.system', return_value='Windows')
@patch('charon.src.core.content_filter.ContentFilter._apply_to_windows_firewall')
@patch('charon.src.core.content_filter.ContentFilter._get_blocked_domains')
def test_apply_to_firewall_windows(mock_get_domains, mock_apply_win, mock_platform):
    """Test applying filters to the firewall on Windows."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Configure mocks
        mock_get_domains.return_value = ['example1.com', 'example2.com']
        mock_apply_win.return_value = True
        
        # Apply to firewall
        result = content_filter.apply_to_firewall()
        
        # Verify result
        assert result is True
        
        # Verify that the appropriate methods were called
        mock_get_domains.assert_called_once()
        mock_apply_win.assert_called_once_with(['example1.com', 'example2.com'])


def test_get_connection():
    """Test database connection handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, 'test.db')
        content_filter = ContentFilter(db_path)
        
        # Test getting a valid connection
        conn = content_filter._get_connection()
        assert conn is not None
        
        # Test with invalid path
        with patch.object(content_filter, 'db_path', '/invalid/path/that/cannot/exist/db.sqlite'):
            # Should return None for invalid path if directory creation fails
            with patch('os.makedirs', side_effect=PermissionError):
                conn = content_filter._get_connection()
                assert conn is None 