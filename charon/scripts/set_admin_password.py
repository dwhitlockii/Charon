#!/usr/bin/env python3
"""
Script to set the admin password for the Charon Firewall

This script updates the admin user's password in the users.json file.
"""

import os
import sys
import json
import argparse
import hashlib
import secrets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('charon.scripts.set_admin_password')

# Add the parent directory to the path so we can import the Charon modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def hash_password(password):
    """Hash a password for storage."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return f"{salt}${pwdhash}"

def main():
    """Main function to update the admin password."""
    parser = argparse.ArgumentParser(description='Set the admin password for Charon Firewall')
    parser.add_argument('--username', default='admin', help='Username to set password for (default: admin)')
    parser.add_argument('--password', required=True, help='New password')
    parser.add_argument('--role', default='admin', help='User role (default: admin)')
    parser.add_argument('--users-file', help='Path to users.json file')
    
    args = parser.parse_args()
    
    # Determine the users file path
    if args.users_file:
        users_file = args.users_file
    else:
        web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'web')
        users_file = os.path.join(web_dir, 'users.json')
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    
    # Load existing users or create a new users dictionary
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
                logger.info(f"Loaded existing users file from {users_file}")
        except Exception as e:
            logger.error(f"Error loading users file: {e}")
            users = {}
    else:
        users = {}
        logger.info(f"Creating new users file at {users_file}")
    
    # Update the user's password
    users[args.username] = {
        'password': hash_password(args.password),
        'role': args.role
    }
    
    # Save the updated users file
    try:
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=4)
        logger.info(f"Updated password for user '{args.username}' with role '{args.role}'")
        return 0
    except Exception as e:
        logger.error(f"Failed to save users file: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 