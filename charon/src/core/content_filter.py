#!/usr/bin/env python3
"""
Content Filter Module for Charon Firewall

This module provides URL blocking and content filtering functionality.
"""

import os
import logging
import subprocess
import re
import platform
import tempfile
from typing import List, Dict, Optional, Set, Tuple, Union
import sqlite3
import ipaddress

logger = logging.getLogger('charon.content_filter')

class ContentFilter:
    """Content filtering for blocking unwanted websites and content."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the content filter.
        
        Args:
            db_path: Path to the SQLite database for storing blocked domains.
                    If None, a platform-specific default path will be used.
        """
        if db_path is None:
            # Use platform-specific default paths
            if platform.system() == 'Windows':
                base_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Charon')
                self.db_path = os.path.join(base_dir, 'content_filter.db')
            else:
                self.db_path = "/etc/charon/content_filter.db"
        else:
            self.db_path = db_path
            
        self._check_permissions()
        self._initialize_database()
        # Create a connection for use in tests
        self.conn = self._get_connection()
        
    def _check_permissions(self) -> None:
        """Check if the current user has permissions to modify filter settings."""
        # Skip permission check on Windows as geteuid() is not available
        if platform.system() == 'Windows':
            # On Windows, check if we can write to the database directory
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except PermissionError:
                    logger.warning(f"Cannot create directory {db_dir}. Permission denied.")
                    return
            
            if not os.access(db_dir, os.W_OK):
                logger.warning(f"No write access to {db_dir}. Content filtering operations may fail.")
            return
        
        # Unix-specific permission check
        try:
            if os.geteuid() != 0:
                logger.warning("Not running as root. Content filtering operations may fail.")
        except AttributeError:
            # Fallback for any other platform that doesn't have geteuid
            logger.warning("Cannot check root privileges. Content filtering operations may fail.")
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database for storing block lists."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to the database and create tables if they don't exist
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create domains table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY,
                    domain TEXT UNIQUE,
                    category TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    description TEXT,
                    enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Add default categories if they don't exist
            default_categories = [
                ("adult", "Adult content and pornography", 1),
                ("gambling", "Gambling websites", 1),
                ("social", "Social media", 0),
                ("ads", "Advertisements and tracking", 1),
                ("malware", "Malware and phishing", 1)
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO categories (name, description, enabled)
                VALUES (?, ?, ?)
            ''', default_categories)
            
            conn.commit()
            conn.close()
            
            logger.info("Content filter database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize a domain by removing protocol, www prefix, and path.
        
        Args:
            domain: The domain to normalize
            
        Returns:
            str: The normalized domain
        """
        # Remove protocol (http://, https://, etc.)
        domain = re.sub(r'^https?://', '', domain)
        
        # Remove path and query string
        domain = domain.split('/')[0]
        
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        
        # Convert to lowercase
        domain = domain.lower()
        
        return domain
    
    def add_domain(self, domain: str, category: str = "uncategorized") -> bool:
        """Add a domain to the block list.
        
        Args:
            domain: The domain to block (e.g., example.com)
            category: The category of the domain
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Normalize the domain (remove http://, www., etc.)
            domain = self._normalize_domain(domain)
            
            # Add the domain
            cursor.execute('''
                INSERT OR REPLACE INTO domains (domain, category)
                VALUES (?, ?)
            ''', (domain, category))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added domain {domain} to category {category}")
            return True
        except Exception as e:
            logger.error(f"Failed to add domain {domain}: {e}")
            return False
    
    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from the block list.
        
        Args:
            domain: The domain to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize the domain
            domain = self._normalize_domain(domain)
            
            conn = self._get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM domains WHERE domain = ?', (domain,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Removed domain {domain} from block list")
            else:
                logger.warning(f"Domain {domain} not found in block list")
                
            return deleted
        except Exception as e:
            logger.error(f"Failed to remove domain {domain}: {e}")
            return False
    
    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a domain is blocked.
        
        Args:
            domain: The domain to check
            
        Returns:
            bool: True if the domain is blocked, False otherwise
        """
        try:
            # Normalize the domain
            domain = self._normalize_domain(domain)
            
            conn = self._get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Check for exact match
            cursor.execute('''
                SELECT d.domain, c.enabled 
                FROM domains d
                JOIN categories c ON d.category = c.name
                WHERE d.domain = ?
            ''', (domain,))
            
            result = cursor.fetchone()
            
            if result and result[1]:
                conn.close()
                return True
                
            # Check for wildcard match (e.g., *.example.com)
            parts = domain.split('.')
            for i in range(1, len(parts)):
                wildcard = '*.' + '.'.join(parts[i:])
                
                cursor.execute('''
                    SELECT d.domain, c.enabled 
                    FROM domains d
                    JOIN categories c ON d.category = c.name
                    WHERE d.domain = ?
                ''', (wildcard,))
                
                result = cursor.fetchone()
                
                if result and result[1]:
                    conn.close()
                    return True
            
            conn.close()
            return False
        except Exception as e:
            logger.error(f"Failed to check if domain {domain} is blocked: {e}")
            return False
    
    def add_category(self, name: str, description: str, enabled: bool = True) -> bool:
        """Add a new category for content filtering.
        
        Args:
            name: The name of the category
            description: A description of the category
            enabled: Whether the category is enabled by default
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO categories (name, description, enabled)
                VALUES (?, ?, ?)
            ''', (name, description, 1 if enabled else 0))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added category: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add category {name}: {e}")
            return False
    
    def enable_category(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a category.
        
        Args:
            name: The name of the category
            enabled: Whether to enable or disable the category
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE categories
                SET enabled = ?
                WHERE name = ?
            ''', (1 if enabled else 0, name))
            
            if cursor.rowcount == 0:
                logger.warning(f"Category {name} not found")
                conn.close()
                return False
                
            conn.commit()
            conn.close()
            
            status = "enabled" if enabled else "disabled"
            logger.info(f"Category {name} {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to {'enable' if enabled else 'disable'} category {name}: {e}")
            return False
    
    def get_categories(self, enabled_only: bool = False) -> List[Dict[str, any]]:
        """Get a list of all categories.
        
        Args:
            enabled_only: If True, only return enabled categories
            
        Returns:
            List of dictionaries with category information
        """
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT name, description, enabled,
                       (SELECT COUNT(*) FROM domains WHERE category = categories.name) as domain_count
                FROM categories
            '''
            
            if enabled_only:
                query += ' WHERE enabled = 1'
            
            query += ' ORDER BY name'
            
            cursor.execute(query)
            
            categories = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []
    
    def get_domains_by_category(self, category: str) -> List[str]:
        """Get a list of all domains in a specific category.
        
        Args:
            category: The category to get domains for
            
        Returns:
            List of domain names
        """
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT domain FROM domains
                WHERE category = ?
                ORDER BY domain
            ''', (category,))
            
            domains = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return domains
        except Exception as e:
            logger.error(f"Failed to get domains for category {category}: {e}")
            return []
    
    def apply_to_firewall(self, table_name: str = "charon") -> bool:
        """Apply the content filters to the firewall.
        
        This method creates firewall rules to block access to the
        domains in the database. Implementation varies by platform:
        - On Linux: uses nftables
        - On Windows: uses Windows Defender Firewall (netsh)
        
        Args:
            table_name: The name of the firewall table/group to use
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get enabled categories and domains
        domains = self._get_blocked_domains()
        if not domains:
            return False
            
        # Apply to the appropriate firewall based on the platform
        if platform.system() == 'Windows':
            return self._apply_to_windows_firewall(domains)
        else:
            return self._apply_to_nftables(domains, table_name)
    
    def _get_blocked_domains(self) -> List[str]:
        """Get a list of domains to block from enabled categories.
        
        Returns:
            List of domain names to block
        """
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            # Get enabled categories
            cursor.execute('''
                SELECT name FROM categories
                WHERE enabled = 1
            ''')
            
            enabled_categories = [row[0] for row in cursor.fetchall()]
            
            if not enabled_categories:
                logger.warning("No enabled categories found")
                conn.close()
                return []
            
            # Get domains for enabled categories
            placeholders = ','.join(['?'] * len(enabled_categories))
            cursor.execute(f'''
                SELECT domain FROM domains
                WHERE category IN ({placeholders})
            ''', enabled_categories)
            
            domains = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not domains:
                logger.warning("No domains found in enabled categories")
                return []
                
            return domains
        except Exception as e:
            logger.error(f"Failed to get blocked domains: {e}")
            return []
            
    def _apply_to_nftables(self, domains: List[str], table_name: str) -> bool:
        """Apply content filters using nftables (Linux).
        
        Args:
            domains: List of domains to block
            table_name: Name of the nftables table
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary file with the list of domains
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                for domain in domains:
                    tmp_file.write(domain + "\n")
            
            # Create or update the nftables set
            try:
                # Try to delete the set if it exists
                cmd = [
                    "nft", "delete", "set", "inet", table_name, "blocked_domains"
                ]
                subprocess.run(cmd, check=False, capture_output=True)
            except subprocess.SubprocessError:
                pass  # Ignore errors from trying to delete a non-existent set
            
            # Create the set
            cmd = [
                "nft", "add", "set", "inet", table_name, "blocked_domains",
                "{", "type", "string", ";", "flags", "interval", ";", "auto-merge", ";", "}"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Populate the set from the file
            cmd = [
                "nft", "add", "element", "inet", table_name, "blocked_domains", "{",
                f'elements="{tmp_path}"', "}"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Add a rule to block access to the domains in the set
            # This assumes there's an existing chain called "input"
            cmd = [
                "nft", "add", "rule", "inet", table_name, "input",
                "meta", "l4proto", "tcp", "tcp", "dport", "53",
                "reject", "comment", "\"Block DNS requests for filtered domains\""
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            logger.info(f"Applied content filter with {len(domains)} domains using nftables")
            return True
        except Exception as e:
            logger.error(f"Failed to apply content filter to nftables: {e}")
            return False
            
    def _apply_to_windows_firewall(self, domains: List[str]) -> bool:
        """Apply content filters using Windows Defender Firewall.
        
        Args:
            domains: List of domains to block
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, create a rule group for Charon if it doesn't exist
            rule_name = "Charon-ContentFilter"
            
            # Remove existing rules with the same name
            delete_cmd = ["netsh", "advfirewall", "firewall", "delete", "rule", 
                         f"name={rule_name}"]
            try:
                subprocess.run(delete_cmd, check=False, capture_output=True)
            except subprocess.SubprocessError:
                pass  # Ignore errors from trying to delete non-existent rules
            
            # Create a hosts file-style text file for handling in Windows
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as hosts_file:
                hosts_path = hosts_file.name
                for domain in domains:
                    # Format as hosts file entry (127.0.0.1 domain.com)
                    hosts_file.write(f"127.0.0.1 {domain}\n")
            
            # Create a blocking rule for each domain (limited to 25 for performance)
            # Windows firewall doesn't support domain blocking directly, so we'll
            # use a combination of hosts file approach and some basic port blocking
            for i, domain in enumerate(domains[:25]):  # Limit to first 25 domains
                # Block outgoing connections to this domain on common web ports
                add_cmd = [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={rule_name}-{i}", "dir=out", "action=block",
                    "enable=yes", f"remotehost={domain}", "protocol=TCP",
                    "localport=80,443,8080"
                ]
                subprocess.run(add_cmd, check=True, capture_output=True)
            
            # Log instruction for manual hosts file update
            logger.info(f"Created Windows firewall rules for {min(25, len(domains))} domains")
            logger.info(f"For complete blocking, manually add entries from {hosts_path} to your hosts file")
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply content filter to Windows firewall: {e}")
            return False
    
    def _get_connection(self) -> Optional[sqlite3.Connection]:
        """Get a connection to the SQLite database.
        
        Returns:
            sqlite3.Connection: A connection to the database, or None if failed
        """
        try:
            # Ensure directory exists before connecting
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None
    
    def get_domains(self) -> List[Dict[str, any]]:
        """Get a list of all domains.
        
        Returns:
            List of dictionaries with domain information
        """
        try:
            conn = self._get_connection()
            if not conn:
                return []
                
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT d.id, d.domain, d.category, d.added_date, c.enabled
                FROM domains d
                JOIN categories c ON d.category = c.name
                ORDER BY d.domain
            ''')
            
            domains = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return domains
        except Exception as e:
            logger.error(f"Failed to get domains: {e}")
            return [] 