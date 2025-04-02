# Database User Authentication Implementation Plan

## Overview
This document outlines the plan to migrate the Charon Firewall's user authentication system from the current JSON file-based approach to a proper database-backed system using SQLAlchemy.

## Current Implementation
- Users are stored in `src/web/users.json`
- Password hashing uses PBKDF2 with SHA-256
- Authentication is handled directly in `server.py`
- No user management API beyond password changes

## Implementation Steps

### 1. Create User Database Model

Add a `User` model to `src/db/database.py`:

```python
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
```

### 2. Add User Management Methods to Database Class

Extend the `Database` class in `src/db/database.py` with the following methods:

```python
def add_user(self, username, password, role='user', email=None):
    """Add a new user to the database."""
    try:
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
    """Get a user by username."""
    try:
        return self.session.query(User).filter_by(username=username).first()
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def verify_user(self, username, password):
    """Verify user credentials."""
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
    """Update a user's password."""
    try:
        user = self.get_user(username)
        if not user:
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

def _hash_password(self, password, salt):
    """Hash a password with the given salt."""
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('ascii'), 
        100000
    )
    return pwdhash.hex()
```

### 3. Create Migration Script

Create a script at `scripts/migrate_users.py` to transfer existing users from the JSON file to the database:

```python
#!/usr/bin/env python3
"""
User Migration Script for Charon Firewall

This script migrates users from the JSON file to the database.
"""

import os
import sys
import json
import logging

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.web.server import load_users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('charon.scripts.migrate_users')

def migrate_users():
    """Migrate users from JSON to database."""
    try:
        # Load existing users from JSON
        users = load_users()
        logger.info(f"Loaded {len(users)} users from JSON file")
        
        # Connect to database
        db = Database()
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Ensure tables exist
        db.create_tables()
        
        # For each user in the JSON file
        for username, data in users.items():
            # Extract password parts
            salt, hashed = data['password'].split('$')
            
            # Check if user already exists
            existing_user = db.get_user(username)
            if existing_user:
                logger.info(f"User {username} already exists in database")
                continue
            
            # Add user directly to avoid rehashing
            try:
                user = db.session.model.User(
                    username=username,
                    password_hash=hashed,
                    salt=salt,
                    role=data.get('role', 'user')
                )
                db.session.add(user)
                logger.info(f"Added user {username} to database")
            except Exception as e:
                logger.error(f"Error adding user {username}: {e}")
        
        # Commit all changes
        db.session.commit()
        logger.info("User migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_users()
    sys.exit(0 if success else 1)
```

### 4. Update Server Authentication

Modify `src/web/server.py` to use the database for authentication:

```python
# Old JSON-based methods to replace:
# - load_users()
# - save_users()
# - hash_password()
# - verify_password()

# Replace login route with:
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_url = request.args.get('next', url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        if db and db.verify_user(username, password):
            # Get user details
            user = db.get_user(username)
            session['user_id'] = username
            session['role'] = user.role
            session.permanent = remember
            logger.info(f"User {username} logged in")
            return redirect(next_url)
        else:
            # Fallback to JSON if database is unavailable
            try:
                users = load_users()
                if username in users and verify_password(users[username]['password'], password):
                    session['user_id'] = username
                    session['role'] = users[username]['role']
                    session.permanent = remember
                    logger.info(f"User {username} logged in (fallback)")
                    return redirect(next_url)
            except Exception as e:
                logger.error(f"Error in fallback authentication: {e}")
            
            error = 'Invalid credentials. Please try again.'
            logger.warning(f"Failed login attempt for user {username}")
    
    return render_template('login.html', error=error)

# Replace change password route with:
@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password."""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    username = session['user_id']
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    if db:
        # Verify current password
        if not db.verify_user(username, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 403
        
        # Update password
        if db.update_user_password(username, new_password):
            logger.info(f"Password changed for user {username}")
            return jsonify({'success': True, 'message': 'Password changed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Database error'}), 500
    else:
        # Fallback to JSON
        try:
            users = load_users()
            if not verify_password(users[username]['password'], current_password):
                return jsonify({'success': False, 'message': 'Current password is incorrect'}), 403
            
            users[username]['password'] = hash_password(new_password)
            save_users(users)
            
            logger.info(f"Password changed for user {username} (fallback)")
            return jsonify({'success': True, 'message': 'Password changed successfully'})
        except Exception as e:
            logger.error(f"Error in fallback password change: {e}")
            return jsonify({'success': False, 'message': 'System error'}), 500
```

### 5. Add User Management Interface

Create a new template at `src/web/templates/user_management.html` for administrators to manage users.

Add routes to `server.py`:

```python
@app.route('/users', methods=['GET'])
@login_required
def user_management():
    """User management page."""
    # Only allow admin access
    if session.get('role') != 'admin':
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = []
    if db:
        try:
            users = db.session.query(db.session.model.User).all()
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            flash('Error loading users from database', 'error')
    else:
        # Fallback to JSON
        try:
            users_dict = load_users()
            users = [{'username': u, 'role': d['role']} for u, d in users_dict.items()]
        except Exception as e:
            logger.error(f"Error loading users from JSON: {e}")
            flash('Error loading users from file', 'error')
    
    return render_template('user_management.html', users=users)

@app.route('/api/users', methods=['POST'])
@login_required
def api_add_user():
    """Add a new user."""
    # Only allow admin access
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    if db:
        user_id = db.add_user(username, password, role)
        if user_id:
            return jsonify({'success': True, 'message': 'User added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Error adding user to database'}), 500
    else:
        # Fallback to JSON
        try:
            users = load_users()
            if username in users:
                return jsonify({'success': False, 'message': 'User already exists'}), 400
            
            users[username] = {
                'password': hash_password(password),
                'role': role
            }
            save_users(users)
            return jsonify({'success': True, 'message': 'User added successfully'})
        except Exception as e:
            logger.error(f"Error adding user to JSON: {e}")
            return jsonify({'success': False, 'message': 'System error'}), 500
```

### 6. Update TODO List

Add the following to the TODO list:

```markdown
## Core Features

### High Priority
- [x] Migrate user authentication from JSON to database
- [ ] Implement full user management API
- [ ] Add user profile management
```

### 7. Database Initialization

Update `scripts/setup_database.py` to create a default admin user in the database:

```python
def create_default_admin(db):
    """Create a default admin user if none exists."""
    try:
        # Check if any users exist
        users = db.session.query(db.session.model.User).count()
        if users == 0:
            # Create default admin
            db.add_user('admin', 'admin', 'admin')
            logger.info("Created default admin user")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
```

### 8. Testing

Create tests for the user authentication system in `tests/test_user_auth.py`.

## Timeline and Dependencies

1. Database Model & Methods (1-2 days)
2. Migration Script (1 day)
3. Server Authentication Updates (1-2 days)
4. User Management Interface (2-3 days)
5. Testing (1-2 days)

Total estimated time: 6-10 days

## Benefits

- Improved security with centralized authentication
- Better user management capabilities
- Consistent storage with other application data
- Groundwork for future user-related features
- Easier backup and restore of all application data

## Potential Future Enhancements

- Role-based access control system
- Two-factor authentication
- Password policies (complexity, expiration)
- Account lockout after failed attempts
- User activity logging
- Self-service password reset 