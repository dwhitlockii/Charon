#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Migration Script for Charon Firewall

This script migrates users from the JSON file to the database.
"""

import os
import sys
import json
import logging
import argparse

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database, User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('charon.scripts.migrate_users')

def load_users():
    """Load users from JSON file."""
    users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'web', 'users.json')
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                return json.load(f)
        else:
            logger.error(f"Users file not found at {users_file}")
            return {}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def migrate_users(args):
    """Migrate users from JSON to database."""
    try:
        # Load existing users from JSON
        users = load_users()
        if not users:
            logger.error("No users found in JSON file")
            return False
            
        logger.info(f"Loaded {len(users)} users from JSON file")
        
        # Connect to database
        db = Database()
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Ensure tables exist
        db.create_tables()
        
        # Get count before migration
        before_count = 0
        try:
            before_count = db.session.query(User).count()
        except Exception as e:
            logger.warning(f"Could not get initial user count: {e}")
        
        # For each user in the JSON file
        for username, data in users.items():
            try:
                # Extract password parts
                salt, hashed = data['password'].split('$')
                
                # Check if user already exists
                existing_user = db.get_user(username)
                if existing_user:
                    if args.force:
                        logger.info(f"User {username} already exists, updating with JSON data")
                        existing_user.password_hash = hashed
                        existing_user.salt = salt
                        existing_user.role = data.get('role', 'user')
                    else:
                        logger.info(f"User {username} already exists in database, skipping")
                    continue
                
                # Add user directly to avoid rehashing
                user = User(
                    username=username,
                    password_hash=hashed,
                    salt=salt,
                    role=data.get('role', 'user')
                )
                db.session.add(user)
                logger.info(f"Added user {username} to database")
            except Exception as e:
                logger.error(f"Error processing user {username}: {e}")
        
        # Commit all changes
        db.session.commit()
        
        # Get count after migration
        after_count = 0
        try:
            after_count = db.session.query(User).count()
        except Exception as e:
            logger.warning(f"Could not get final user count: {e}")
        
        added_count = after_count - before_count
        logger.info(f"Migration complete. Added {added_count} new users")
        
        # Create backup of the users.json file if requested
        if args.backup:
            users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'web', 'users.json')
            backup_file = users_file + '.bak'
            try:
                import shutil
                shutil.copy2(users_file, backup_file)
                logger.info(f"Created backup of users.json at {backup_file}")
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def main():
    """Main function."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Migrate users from JSON to database')
    parser.add_argument('--force', action='store_true', help='Update existing users')
    parser.add_argument('--backup', action='store_true', help='Create backup of users.json')
    args = parser.parse_args()
    
    success = migrate_users(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
