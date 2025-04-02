#!/usr/bin/env python3
"""
Database Module for Charon Firewall

This module provides functionality to interact with a MySQL database for storing
logs, configurations, and other data.
"""

import logging
import os
import secrets
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import datetime
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

logger = logging.getLogger('charon.db')

Base = declarative_base()

class FirewallRule(Base):
    """Model for firewall rules."""
    __tablename__ = 'firewall_rules'
    
    id = Column(Integer, primary_key=True)
    chain = Column(String(20), nullable=False)
    action = Column(String(20), nullable=False)
    protocol = Column(String(20), nullable=True)
    src_ip = Column(String(50), nullable=True)
    dst_ip = Column(String(50), nullable=True)
    src_port = Column(String(50), nullable=True)
    dst_port = Column(String(50), nullable=True)
    description = Column(String(200), nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class FirewallLog(Base):
    """Model for firewall logs."""
    __tablename__ = 'firewall_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    chain = Column(String(20), nullable=False)
    action = Column(String(20), nullable=False)
    protocol = Column(String(20), nullable=True)
    src_ip = Column(String(50), nullable=True)
    dst_ip = Column(String(50), nullable=True)
    src_port = Column(String(50), nullable=True)
    dst_port = Column(String(50), nullable=True)
    rule_id = Column(Integer, ForeignKey('firewall_rules.id'), nullable=True)
    rule = relationship("FirewallRule")

class ConfigSetting(Base):
    """Model for configuration settings."""
    __tablename__ = 'config_settings'
    
    id = Column(Integer, primary_key=True)
    section = Column(String(50), nullable=False)
    key = Column(String(50), nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    __table_args__ = (
        UniqueConstraint('section', 'key', name='_section_key_uc'),
    )

class User(Base):
    """Model for user accounts."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    salt = Column(String(50), nullable=False)
    role = Column(String(20), default='user')
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    last_login = Column(DateTime, nullable=True)

class Database:
    """Database manager for Charon firewall."""
    
    def __init__(self, connection_string=None):
        """Initialize the database manager.
        
        Args:
            connection_string: SQLAlchemy connection string. If None, uses environment variables
                or defaults to SQLite for development.
        """
        self.session = None
        self.engine = None
        
        # If no connection string is provided, try to use environment variables or default to SQLite
        if not connection_string:
            # Check for environment variables
            db_type = os.environ.get('CHARON_DB_TYPE', 'sqlite').lower()
            
            if db_type == 'mysql':
                # MySQL connection
                host = os.environ.get('MYSQL_HOST', 'localhost')
                port = os.environ.get('MYSQL_PORT', '3306')
                database = os.environ.get('MYSQL_DATABASE', 'charon')
                user = os.environ.get('MYSQL_USER', 'charon')
                password = os.environ.get('MYSQL_PASSWORD', 'charon')
                
                connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            else:
                # SQLite connection (default for development)
                db_path = os.environ.get('CHARON_DB_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'charon.db'))
                # Ensure the directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                connection_string = f"sqlite:///{db_path}"
                logger.info(f"Using SQLite database at {db_path}")
        
        self.connection_string = connection_string
    
    def connect(self):
        """Connect to the database."""
        try:
            # Create engine and session
            self.engine = create_engine(self.connection_string)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            logger.info("Connected to database")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def create_tables(self):
        """Create all necessary tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Created database tables")
            return True
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.session:
            self.session.close()
            logger.info("Closed database connection")
    
    # User management methods
    def add_user(self, username, password, role='user', email=None):
        """Add a new user to the database.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role (default: 'user')
            email: User email (optional)
            
        Returns:
            The ID of the created user, or None if it fails
        """
        try:
            # Check if user already exists
            existing_user = self.get_user(username)
            if existing_user:
                logger.warning(f"User {username} already exists")
                return None
                
            # Generate salt and hash password
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            
            user = User(
                username=username,
                password_hash=password_hash,
                salt=salt,
                role=role,
                email=email
            )
            
            self.session.add(user)
            self.session.commit()
            logger.info(f"Added user: {username}")
            return user.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_user(self, username):
        """Get a user by username.
        
        Args:
            username: Username to lookup
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return self.session.query(User).filter_by(username=username).first()
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_all_users(self):
        """Get all users.
        
        Returns:
            List of User objects
        """
        try:
            return self.session.query(User).all()
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def delete_user(self, username):
        """Delete a user.
        
        Args:
            username: Username to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get_user(username)
            if not user:
                logger.warning(f"User {username} not found")
                return False
            
            self.session.delete(user)
            self.session.commit()
            logger.info(f"Deleted user: {username}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting user: {e}")
            return False
    
    def verify_user(self, username, password):
        """Verify user credentials.
        
        Args:
            username: Username to verify
            password: Password to verify
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            user = self.get_user(username)
            if not user:
                return False
            
            hashed = self._hash_password(password, user.salt)
            if hashed == user.password_hash:
                # Update last login time
                user.last_login = datetime.datetime.now()
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False
    
    def update_user_password(self, username, new_password):
        """Update a user's password.
        
        Args:
            username: Username to update
            new_password: New password (plain text)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get_user(username)
            if not user:
                logger.warning(f"User {username} not found")
                return False
            
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(new_password, salt)
            
            user.password_hash = password_hash
            user.salt = salt
            user.updated_at = datetime.datetime.now()
            
            self.session.commit()
            logger.info(f"Updated password for user: {username}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating user password: {e}")
            return False
    
    def update_user(self, username, data):
        """Update user details.
        
        Args:
            username: Username to update
            data: Dictionary of fields to update (role, email)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get_user(username)
            if not user:
                logger.warning(f"User {username} not found")
                return False
            
            # Update attributes
            for key, value in data.items():
                if key in ['role', 'email'] and hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.datetime.now()
            self.session.commit()
            logger.info(f"Updated user: {username}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating user: {e}")
            return False
    
    def _hash_password(self, password, salt):
        """Hash a password with the given salt.
        
        Args:
            password: Plain text password
            salt: Salt string
            
        Returns:
            Hexadecimal string of hashed password
        """
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('ascii'), 
            100000
        )
        return pwdhash.hex()
    
    # Firewall rule methods
    def add_rule(self, rule_data):
        """Add a firewall rule to the database.
        
        Args:
            rule_data: Dictionary containing rule data
            
        Returns:
            The ID of the created rule, or None if it fails
        """
        try:
            rule = FirewallRule(**rule_data)
            self.session.add(rule)
            self.session.commit()
            logger.info(f"Added firewall rule: {rule.id}")
            return rule.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding firewall rule: {e}")
            return None
    
    def update_rule(self, rule_id, rule_data):
        """Update an existing firewall rule.
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary containing updated rule data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rule = self.session.query(FirewallRule).filter_by(id=rule_id).first()
            if not rule:
                logger.warning(f"Rule with ID {rule_id} not found")
                return False
            
            for key, value in rule_data.items():
                setattr(rule, key, value)
            
            self.session.commit()
            logger.info(f"Updated firewall rule: {rule_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating firewall rule: {e}")
            return False
    
    def delete_rule(self, rule_id):
        """Delete a firewall rule.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rule = self.session.query(FirewallRule).filter_by(id=rule_id).first()
            if not rule:
                logger.warning(f"Rule with ID {rule_id} not found")
                return False
            
            self.session.delete(rule)
            self.session.commit()
            logger.info(f"Deleted firewall rule: {rule_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting firewall rule: {e}")
            return False
    
    def get_rules(self, filters=None):
        """Get firewall rules from the database.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            List of firewall rules
        """
        try:
            query = self.session.query(FirewallRule)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(FirewallRule, key):
                        query = query.filter(getattr(FirewallRule, key) == value)
            
            # Order by ID by default
            query = query.order_by(FirewallRule.id)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting firewall rules: {e}")
            return []
    
    # Log methods
    def add_log(self, log_data):
        """Add a log entry to the database.
        
        Args:
            log_data: Dictionary containing log data
            
        Returns:
            The ID of the created log entry, or None if it fails
        """
        try:
            log = FirewallLog(**log_data)
            self.session.add(log)
            self.session.commit()
            logger.debug(f"Added firewall log: {log.id}")
            return log.id
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding firewall log: {e}")
            return None
    
    def get_logs(self, filters=None, limit=100):
        """Get log entries from the database.
        
        Args:
            filters: Dictionary of filters to apply
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        try:
            query = self.session.query(FirewallLog).order_by(FirewallLog.timestamp.desc())
            
            if filters:
                for key, value in filters.items():
                    if hasattr(FirewallLog, key):
                        query = query.filter(getattr(FirewallLog, key) == value)
            
            if limit:
                query = query.limit(limit)
            
            logs = query.all()
            return logs
        except Exception as e:
            logger.error(f"Error getting firewall logs: {e}")
            return []
    
    # Configuration methods
    def set_config(self, section, key, value, description=None):
        """Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the config already exists
            config = self.session.query(ConfigSetting).filter_by(section=section, key=key).first()
            
            if config:
                # Update existing config
                config.value = value
                if description:
                    config.description = description
            else:
                # Create new config
                config = ConfigSetting(
                    section=section,
                    key=key,
                    value=value,
                    description=description
                )
                self.session.add(config)
            
            self.session.commit()
            logger.info(f"Set config {section}.{key} = {value}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error setting config {section}.{key}: {e}")
            return False
    
    def get_config(self, section, key, default=None):
        """Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value, or default if not found
        """
        try:
            config = self.session.query(ConfigSetting).filter_by(section=section, key=key).first()
            
            if config:
                return config.value
            else:
                return default
        except Exception as e:
            logger.error(f"Error getting config {section}.{key}: {e}")
            return default
    
    def get_config_section(self, section):
        """Get all configuration values in a section.
        
        Args:
            section: Configuration section
            
        Returns:
            Dictionary of configuration values
        """
        try:
            configs = self.session.query(ConfigSetting).filter_by(section=section).all()
            
            return {config.key: config.value for config in configs}
        except Exception as e:
            logger.error(f"Error getting config section {section}: {e}")
            return {}
    
    def get_all_config(self, section=None):
        """Get all configuration values, optionally filtered by section.
        
        Args:
            section: Optional configuration section to filter by
            
        Returns:
            Dictionary of configuration values
        """
        try:
            if section:
                return self.get_config_section(section)
                
            # Get all configs grouped by section
            configs = self.session.query(ConfigSetting).all()
            result = {}
            
            for config in configs:
                if config.section not in result:
                    result[config.section] = {}
                result[config.section][config.key] = config.value
                
            return result
        except Exception as e:
            logger.error(f"Error getting all config: {e}")
            return {}
    
    # Rule management methods
    def clear_rules(self):
        """Delete all firewall rules from the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.session.query(FirewallRule).delete()
            self.session.commit()
            logger.info("Cleared all firewall rules")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error clearing firewall rules: {e}")
            return False
    
    def verify_password(self, username, password):
        """Verify a user's password.
        
        Args:
            username: Username to verify
            password: Plain text password to check
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            user = self.get_user(username)
            
            if not user:
                logger.warning(f"User {username} not found")
                return False
                
            # Hash the provided password with the user's salt
            password_hash = self._hash_password(password, user.salt)
            
            # Compare hashes
            return password_hash == user.password_hash
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False 