#!/usr/bin/env python3
"""
Reset Password Script for Charon Firewall

This script creates or updates a user in the users.json file.
"""

import os
import json
import hashlib
import secrets

def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return f"{salt}${pwdhash}"

def reset_admin_password():
    """Reset or create admin user with password 'admin'."""
    # Define the path to users.json
    users_file = os.path.join('src', 'web', 'users.json')
    
    # Define the admin user credentials
    admin_user = {
        'admin': {
            'password': hash_password('admin'),
            'role': 'admin'
        }
    }
    
    # Write to the file
    with open(users_file, 'w') as f:
        json.dump(admin_user, f, indent=4)
    
    print(f"Reset admin credentials to username: 'admin', password: 'admin'")
    print(f"Updated file: {users_file}")

if __name__ == "__main__":
    reset_admin_password() 