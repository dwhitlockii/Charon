#!/usr/bin/env python3
"""
Database Setup Script for Charon Firewall

This script creates the MySQL database and tables for Charon.
"""

import os
import sys
import logging
import argparse
import pymysql
from getpass import getpass

# Add the parent directory to the path so we can import the Charon modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Base, Database, create_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.scripts.setup_database')

def create_database(args):
    """Create the MySQL database."""
    # Get MySQL root password if not provided
    if not args.root_password:
        args.root_password = getpass("Enter MySQL root password: ")

    try:
        # Connect to MySQL server as root
        connection = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.root_user,
            password=args.root_password
        )
        
        logger.info(f"Connected to MySQL server at {args.host}:{args.port}")
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {args.database}")
            logger.info(f"Database '{args.database}' created or already exists")
            
            # Create user if it doesn't exist
            try:
                # MySQL 8+ uses different syntax for creating users
                cursor.execute(f"CREATE USER IF NOT EXISTS '{args.user}'@'%' IDENTIFIED BY '{args.password}'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON {args.database}.* TO '{args.user}'@'%'")
            except pymysql.err.OperationalError:
                # Try older MySQL syntax
                cursor.execute(f"GRANT ALL PRIVILEGES ON {args.database}.* TO '{args.user}'@'%' IDENTIFIED BY '{args.password}'")
            
            cursor.execute("FLUSH PRIVILEGES")
            logger.info(f"User '{args.user}' created and granted privileges")
        
        connection.close()
        logger.info("MySQL database and user setup complete")
        return True
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        return False

def create_tables(args):
    """Create the database tables."""
    try:
        # Set environment variables for the Database class to use
        os.environ['CHARON_DB_HOST'] = args.host
        os.environ['CHARON_DB_PORT'] = str(args.port)
        os.environ['CHARON_DB_USER'] = args.user
        os.environ['CHARON_DB_PASSWORD'] = args.password
        os.environ['CHARON_DB_NAME'] = args.database
        
        # Create database connection and tables
        db = Database()
        if db.connect():
            db.create_tables()
            logger.info("Database tables created successfully")
            
            # Create initial settings if needed
            create_initial_settings(db)
            
            return True
        else:
            logger.error("Failed to connect to database")
            return False
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False

def create_initial_settings(db):
    """Create initial default settings."""
    try:
        # Add default firewall settings
        db.set_config("firewall", "default_action", "drop", "Default action for firewall")
        db.set_config("firewall", "log_level", "info", "Logging level for firewall")
        
        # Add default content filter settings
        db.set_config("content_filter", "enabled", "true", "Whether content filtering is enabled")
        
        # Add default QoS settings
        db.set_config("qos", "enabled", "false", "Whether QoS is enabled")
        
        logger.info("Initial settings created")
    except Exception as e:
        logger.error(f"Error creating initial settings: {str(e)}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Setup Charon database')
    parser.add_argument('--host', default='localhost', help='MySQL server host')
    parser.add_argument('--port', type=int, default=3306, help='MySQL server port')
    parser.add_argument('--database', default='charon', help='Database name')
    parser.add_argument('--user', default='charon', help='Database user')
    parser.add_argument('--password', default='charon', help='Database password')
    parser.add_argument('--root-user', default='root', help='MySQL root user')
    parser.add_argument('--root-password', help='MySQL root password')
    parser.add_argument('--skip-db-creation', action='store_true', help='Skip database creation')
    parser.add_argument('--skip-tables-creation', action='store_true', help='Skip tables creation')
    
    args = parser.parse_args()
    
    # Create database and user
    if not args.skip_db_creation:
        if not create_database(args):
            logger.error("Failed to set up database")
            return 1
    
    # Create tables
    if not args.skip_tables_creation:
        if not create_tables(args):
            logger.error("Failed to create tables")
            return 1
    
    logger.info("Database setup complete")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 