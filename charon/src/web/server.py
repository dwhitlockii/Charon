#!/usr/bin/env python3
"""
Web Server Module for Charon Firewall

This module provides a web interface for the Charon firewall.
"""

import os
import json
import logging
import datetime
import hashlib
from functools import wraps
import secrets
import platform
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort, current_app, make_response, send_file
import sys
import random
from datetime import datetime, timedelta
import time
import subprocess
import re
from typing import Dict, List, Optional, Tuple, Union

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Add the parent directory to sys.path to ensure imports work
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import Charon modules
try:
    from src.db.database import Database, User
    db_import_error = None
except ImportError as e:
    Database = None
    User = None
    db_import_error = str(e)
    print(f"Warning: Database module could not be imported: {e}. Using mock data.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('charon.web')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('CHARON_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('CHARON_SECURE_COOKIES', 'False').lower() == 'true'

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add CSRF exempt for API routes
def csrf_exempt(view):
    """Mark a view function as exempt from CSRF protection."""
    view.csrf_exempt = True
    return view

# Add a before_request handler to exempt API routes from CSRF protection
@app.before_request
def check_csrf():
    # Skip CSRF check for API endpoints and GET requests
    if request.endpoint and (
        request.endpoint.startswith('api_') or 
        request.method == 'GET' or
        getattr(app.view_functions.get(request.endpoint), 'csrf_exempt', False)
    ):
        return
    
    # For other routes, check CSRF token (to be implemented)
    # This is a simplified version since we don't have a full CSRF system in place
    pass

# Context processor to add current_app to all templates
@app.context_processor
def inject_current_app():
    return {'current_app': current_app}

# Context processor to add session to all templates
@app.context_processor
def inject_session():
    return {'session': session}

# Initialize database if available
db = None
if Database is not None:
    try:
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        db = Database()
        if db.connect():
            logger.info("Successfully connected to database")
            db.create_tables()
            
            # Create default admin user if none exists
            try:
                user_exists = db.session.query(
                    db.session.query(User).exists()
                ).scalar()
                
                if not user_exists:
                    default_admin_username = os.environ.get('CHARON_DEFAULT_ADMIN', 'admin')
                    default_admin_password = secrets.token_urlsafe(12)  # Generate a secure random password
                    db.add_user(default_admin_username, default_admin_password, 'admin')
                    logger.info(f"Created default admin user with username: {default_admin_username} and password: {default_admin_password}")
                    print(f"\n===== INITIAL ADMIN CREDENTIALS =====")
                    print(f"Username: {default_admin_username}")
                    print(f"Password: {default_admin_password}")
                    print(f"Please change these credentials after first login!")
                    print(f"=====================================\n")
            except Exception as e:
                logger.error(f"Error checking/creating default user: {e}")
        else:
            logger.error("Failed to connect to database")
            db = None
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        db = None

# User management
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        # Create default admin user if no users file exists
        logger.warning("No users file found, creating default admin user")
        default_admin_username = os.environ.get('CHARON_DEFAULT_ADMIN', 'admin')
        default_admin_password = secrets.token_urlsafe(12)  # Generate a secure random password
        
        users = {
            default_admin_username: {
                'password': hash_password(default_admin_password),
                'role': 'admin'
            }
        }
        save_users(users)
        
        print(f"\n===== INITIAL ADMIN CREDENTIALS =====")
        print(f"Username: {default_admin_username}")
        print(f"Password: {default_admin_password}")
        print(f"Please change these credentials after first login!")
        print(f"=====================================\n")
        
        return users

def save_users(users):
    """Save users to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return f"{salt}${pwdhash}"

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user."""
    salt, stored_hash = stored_password.split('$')
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), 
                                 salt.encode('ascii'), 100000)
    return pwdhash.hex() == stored_hash

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# System helper functions
def get_system_uptime():
    """Get system uptime."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        
        # Convert to days, hours, minutes
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        else:
            return f"{int(minutes)}m {int(seconds)}s"
    except Exception as e:
        logger.error(f"Error getting uptime: {e}")
        return "Unknown"

def get_cpu_usage() -> float:
    """Get CPU usage percentage."""
    try:
        cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
        output = subprocess.check_output(cmd, shell=True, text=True)
        return float(output.strip())
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return 0.0

def get_memory_usage() -> float:
    """Get memory usage percentage."""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            total = int(lines[0].split()[1])
            free = int(lines[1].split()[1])
            buffers = int(lines[3].split()[1])
            cached = int(lines[4].split()[1])
            used = total - free - buffers - cached
            return round((used / total) * 100, 2)
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return 0.0

def get_disk_usage() -> float:
    """Get disk usage percentage."""
    try:
        cmd = "df -h / | tail -n1 | awk '{print $5}' | sed 's/%//'"
        output = subprocess.check_output(cmd, shell=True, text=True)
        return float(output.strip())
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return 0.0

def get_network_stats() -> Dict[str, Dict[str, int]]:
    """Get network statistics."""
    try:
        # Read network stats from /proc/net/dev
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()
        
        stats = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'interfaces': {}
        }
        
        # Skip first two lines (headers)
        for line in lines[2:]:
            interface, data = line.split(':')
            interface = interface.strip()
            values = data.split()
            
            # Skip loopback interface
            if interface == 'lo':
                continue
                
            interface_stats = {
                'bytes_sent': int(values[8]),
                'bytes_recv': int(values[0]),
                'packets_sent': int(values[9]),
                'packets_recv': int(values[1])
            }
            
            stats['interfaces'][interface] = interface_stats
            stats['bytes_sent'] += interface_stats['bytes_sent']
            stats['bytes_recv'] += interface_stats['bytes_recv']
            stats['packets_sent'] += interface_stats['packets_sent']
            stats['packets_recv'] += interface_stats['packets_recv']
        
        return stats
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        return {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'interfaces': {}
        }

def get_cpu_usage():
    """Get CPU usage percentage."""
    try:
        # Read CPU usage from /proc/stat
        with open('/proc/stat', 'r') as f:
            cpu = f.readline().split()
        
        # Calculate CPU usage
        total = sum(float(x) for x in cpu[1:])
        idle = float(cpu[4])
        usage = 100 * (1 - idle/total)
        return round(usage)
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return 0

def get_memory_usage():
    """Get memory usage percentage."""
    try:
        # Read memory info from /proc/meminfo
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        # Parse memory info
        mem_info = {}
        for line in lines:
            key, value = line.split(':')
            mem_info[key.strip()] = int(value.strip().split()[0])  # Convert to KB
        
        total = mem_info['MemTotal']
        free = mem_info['MemFree']
        buffers = mem_info.get('Buffers', 0)
        cached = mem_info.get('Cached', 0)
        
        used = total - free - buffers - cached
        usage = (used / total) * 100
        return round(usage)
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return 0

def get_disk_usage():
    """Get disk usage percentage."""
    try:
        # Use df command to get disk usage
        df = subprocess.run(['df', '/'], capture_output=True, text=True)
        if df.returncode == 0:
            lines = df.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage = int(lines[1].split()[4].rstrip('%'))
                return usage
        return 0
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return 0

def get_network_stats():
    """Get network statistics."""
    try:
        # Read network stats from /proc/net/dev
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()
        
        stats = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'interfaces': {}
        }
        
        # Skip first two lines (headers)
        for line in lines[2:]:
            interface, data = line.split(':')
            interface = interface.strip()
            values = data.split()
            
            # Skip loopback interface
            if interface == 'lo':
                continue
                
            interface_stats = {
                'bytes_sent': int(values[8]),
                'bytes_recv': int(values[0]),
                'packets_sent': int(values[9]),
                'packets_recv': int(values[1])
            }
            
            stats['interfaces'][interface] = interface_stats
            stats['bytes_sent'] += interface_stats['bytes_sent']
            stats['bytes_recv'] += interface_stats['bytes_recv']
            stats['packets_sent'] += interface_stats['packets_sent']
            stats['packets_recv'] += interface_stats['packets_recv']
        
        return stats
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        return {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'interfaces': {}
        }

def parse_firewall_logs(limit=10, offset=0, log_type=None):
    """Parse firewall logs from system log files."""
    try:
        logs = []
        # Try to read from syslog or kern.log
        log_paths = ['/var/log/syslog', '/var/log/kern.log', '/var/log/messages']
        
        # Also check host mounted logs if running in Docker
        host_log_path = os.environ.get('HOST_LOG_PATH', '/host/var/log')
        if os.path.exists(host_log_path):
            log_paths.extend([
                f"{host_log_path}/syslog",
                f"{host_log_path}/kern.log", 
                f"{host_log_path}/messages"
            ])
        
        # Try each log file until we find one that exists
        for log_file in log_paths:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    # Read the entire file and filter for firewall related lines
                    lines = f.readlines()
                    firewall_lines = [line for line in lines if 'IN=' in line and ('DROP' in line or 'ACCEPT' in line)]
                    
                    # Apply log type filter if specified
                    if log_type:
                        if log_type.lower() == 'error':
                            firewall_lines = [line for line in firewall_lines if 'DROP' in line]
                        elif log_type.lower() == 'info':
                            firewall_lines = [line for line in firewall_lines if 'ACCEPT' in line]
                    
                    # Apply pagination
                    paginated_lines = firewall_lines[offset:offset+limit]
                    
                    # Parse each line
                    for i, line in enumerate(paginated_lines):
                        parts = line.split()
                        timestamp = ' '.join(parts[0:3]) if len(parts) >= 3 else 'Unknown'
                        
                        log_entry = {
                            'id': offset + i + 1,
                            'timestamp': timestamp,
                            'type': 'error' if 'DROP' in line else 'info',
                            'source': 'firewall',
                            'message': line.strip()
                        }
                        
                        logs.append(log_entry)
                
                # If we found logs, return them
                if logs:
                    return logs
        
        # If no logs were found, return empty list
        return []
    except Exception as e:
        logger.error(f"Error parsing firewall logs: {e}")
        return []

def get_system_status():
    """Get system status including CPU, memory, disk usage, and network stats."""
    try:
        # Check if firewall is actually running - platform-specific checks
        firewall_active = False
        platform_system = platform.system().lower()
        
        if platform_system == 'windows':
            # Windows-specific check
            try:
                check_cmd = ["powershell", "-Command", "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"]
                result = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
                
                # Firewall is active if any profile is enabled
                for line in result.stdout.strip().split('\n'):
                    if line.strip().lower() == 'true':
                        firewall_active = True
                        break
                        
                logger.info(f"Windows Firewall status check: {firewall_active}")
            except Exception as e:
                logger.warning(f"Failed to check Windows firewall status: {e}")
                # Don't assume it's active if we can't check
                firewall_active = False
        else:
            # Linux-specific checks
            # Try multiple methods to determine if firewall is active
            try:
                # Method 1: Check if nftables has our tables
                firewall_tables = os.environ.get('CHARON_FIREWALL_TABLES', 'charon').split(',')
                nft_cmd = ["nft", "list", "tables"]
                nft_result = subprocess.run(nft_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if nft_result.returncode == 0:
                    for table in firewall_tables:
                        if table.strip() in nft_result.stdout:
                            firewall_active = True
                            logger.info(f"nftables firewall is active with table '{table}'")
                            break
                
                # Method 2: If nft check fails or no tables found, try iptables
                if not firewall_active:
                    iptables_cmd = ["iptables", "-L"]
                    iptables_result = subprocess.run(iptables_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    # Check if iptables has any rules
                    if iptables_result.returncode == 0 and len(iptables_result.stdout.strip().split('\n')) > 6:
                        # More than just the default chains means rules exist
                        firewall_active = True
                        logger.info("iptables firewall is active with custom rules")
            except Exception as e:
                logger.warning(f"Failed to check Linux firewall status: {e}")
                # Don't assume it's active if we can't check
                firewall_active = False
        
        status = {
            'uptime': get_system_uptime(),
            'cpu_usage': get_cpu_usage(),
            'memory_usage': get_memory_usage(),
            'disk_usage': get_disk_usage(),
            'network_stats': get_network_stats(),
            'firewall_status': 'active' if firewall_active else 'inactive',
            'status': 'active' if firewall_active else 'inactive'  # Add this key explicitly as it seems to be needed by the template
        }
        return status
    except Exception as e:
        logger.error(f"Error in get_system_status: {e}")
        # Return a minimal status object to prevent dashboard errors
        return {
            'uptime': 'Unknown',
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'network_stats': {},
            'firewall_status': 'unknown',
            'status': 'unknown'  # Add this key explicitly as it seems to be needed by the template
        }

def get_recent_logs(limit=10, page=1, log_type=None):
    """Get recent firewall logs."""
    offset = (page - 1) * limit
    logs = []
    
    # Try to get logs from database if available
    if db:
        try:
            # Check if get_logs method exists
            if hasattr(db, 'get_logs') and callable(getattr(db, 'get_logs')):
                try:
                    # Try with all parameters
                    method_signature = db.get_logs.__code__.co_varnames
                    if 'log_type' in method_signature and log_type and log_type != 'all':
                        db_logs = db.get_logs(log_type=log_type, limit=limit, offset=offset)
                    elif 'limit' in method_signature and 'offset' in method_signature:
                        db_logs = db.get_logs(limit=limit, offset=offset)
                    else:
                        # Try with no parameters
                        db_logs = db.get_logs()
                        # Apply manual pagination if needed
                        if offset > 0 or limit < len(db_logs):
                            db_logs = db_logs[offset:offset+limit]
                
                    # Parse each log entry, handling missing attributes
                    for log in db_logs:
                        logs.append({
                            'id': getattr(log, 'id', 0),
                            'timestamp': getattr(log, 'timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') if hasattr(log, 'timestamp') else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'type': getattr(log, 'type', 'info'),
                            'source': getattr(log, 'source', 'system'),
                            'message': getattr(log, 'message', 'Log entry')
                        })
                    return logs
                except Exception as e:
                    logger.error(f"Database.get_logs() method signature mismatch: {e}")
                    # Continue to fallback methods
            else:
                logger.warning("Database missing get_logs method")
                # Fall back to system logs
                return parse_firewall_logs(limit, offset, log_type)
        except Exception as e:
            logger.error(f"Error getting logs from database: {e}")
            # Fall back to system logs
    
    # Try system logs if database method failed or is unavailable
    try:
        logs = parse_firewall_logs(limit, offset, log_type)
        if logs:
            return logs
    except Exception as e:
        logger.error(f"Error parsing system logs: {e}")
        # Return empty logs instead of generating mock data
        return []
    
    # Return empty logs instead of generating mock data
    logger.warning("No logs available. Database connection required.")
    return []

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_url = request.args.get('next', url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        # Try database authentication first if available
        auth_success = False
        role = 'user'
        
        if db:
            try:
                if db.verify_user(username, password):
                    user = db.get_user(username)
                    role = user.role
                    auth_success = True
                    logger.info(f"User {username} logged in via database")
            except Exception as e:
                logger.error(f"Database authentication error: {e}")
        
        # Fall back to JSON authentication if database auth failed or unavailable
        if not auth_success:
            try:
                users = load_users()
                if username in users and verify_password(users[username]['password'], password):
                    role = users[username]['role']
                    auth_success = True
                    logger.info(f"User {username} logged in via JSON fallback")
            except Exception as e:
                logger.error(f"JSON authentication error: {e}")
        
        if auth_success:
            session['user_id'] = username
            session['username'] = username  # Explicitly store username
            session['role'] = role
            session.permanent = remember
            return redirect(next_url)
        else:
            error = 'Invalid credentials. Please try again.'
            logger.warning(f"Failed login attempt for user {username}")
    
    return render_template('login.html', error=error, current_app=current_app)

@app.route('/logout')
def logout():
    if 'user_id' in session:
        logger.info(f"User {session['user_id']} logged out")
        session.pop('user_id', None)
        session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Dashboard page."""
    try:
        # Get system status
        system_status = get_system_status()
        
        # If database is available, get rule status and logs
        if db:
            try:
                # Get rule stats
                try:
                    total_rules = db.count_rules() if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')) else 0
                    enabled_rules = db.count_rules(enabled=True) if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')) else 0
                    input_rules = db.count_rules(chain='INPUT') if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')) else 0
                    output_rules = db.count_rules(chain='OUTPUT') if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')) else 0
                    forward_rules = db.count_rules(chain='FORWARD') if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')) else 0
                except Exception as e:
                    logger.warning(f"Database missing count_rules method: {e}")
                    total_rules = 0
                    enabled_rules = 0
                    input_rules = 0
                    output_rules = 0
                    forward_rules = 0
                
                rule_status = {
                    'total': total_rules,
                    'enabled': enabled_rules,
                    'input': input_rules,
                    'output': output_rules,
                    'forward': forward_rules
                }
            except Exception as e:
                logger.error(f"Error getting rule stats: {e}")
                rule_status = {
                    'total': 0,
                    'enabled': 0,
                    'input': 0,
                    'output': 0,
                    'forward': 0
                }
        else:
            # Not connected to database, use empty data
            rule_status = {
                'total': 0,
                'enabled': 0,
                'input': 0,
                'output': 0,
                'forward': 0
            }
            
        # Get recent logs
        try:
            recent_logs = get_recent_logs(limit=5)
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            recent_logs = []
        
        # Get network stats with error handling
        network_stats = system_status.get('network_stats', {})
        
        # Create initial status object with all features disabled
        status = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_rules': rule_status['enabled'],
            'content_filter_enabled': False,  # Default to False
            'blocked_domains': 0,
            'categories_enabled': 0,
            'qos_enabled': False,  # Default to False
            'traffic_classes': 0,
            'active_filters': 0,
            'cpu_usage': system_status.get('cpu_usage', 0),
            'memory_usage': system_status.get('memory_usage', 0),
            'disk_usage': system_status.get('disk_usage', 0),
            'firewall_status': system_status.get('firewall_status', 'inactive'),
            'status': system_status.get('status', 'inactive')
        }
        
        # If firewall is not active, don't even check other services
        if status['firewall_status'] != 'active':
            logger.warning("Firewall is inactive - force disabling all other services")
            
            # Get stats but set active counts to 0
            if db:
                try:
                    # Get content filter domain count
                    domains_str = db.get_config('content_filter', 'domains', '[]')
                    domains = json.loads(domains_str)
                    status['blocked_domains'] = len(domains)
                    
                    # Get traffic class count
                    classes_str = db.get_config('qos', 'classes', '[]')
                    classes = json.loads(classes_str)
                    status['traffic_classes'] = len(classes)
                except Exception as e:
                    logger.error(f"Error getting config stats: {e}")
        else:
            # Firewall is active, check content filter and QoS
            
            # Check content filter
            content_filter_active = check_content_filter_active()
            status['content_filter_enabled'] = content_filter_active
            
            # Check QoS
            qos_active = check_qos_active()
            status['qos_enabled'] = qos_active
            
            # Get counts from database
            if db:
                try:
                    # Log database vs system status mismatches
                    db_cf_enabled = db.get_config('content_filter', 'enabled', 'false').lower() == 'true'
                    db_qos_enabled = db.get_config('qos', 'enabled', 'false').lower() == 'true'
                    
                    if content_filter_active != db_cf_enabled:
                        logger.warning(f"Content filter system status ({content_filter_active}) " + 
                                       f"doesn't match database setting ({db_cf_enabled})")
                    
                    if qos_active != db_qos_enabled:
                        logger.warning(f"QoS system status ({qos_active}) " + 
                                       f"doesn't match database setting ({db_qos_enabled})")
                    
                    # Get domain counts
                    domains_str = db.get_config('content_filter', 'domains', '[]')
                    domains = json.loads(domains_str)
                    status['blocked_domains'] = len(domains)
                    
                    # Get category counts - only count as enabled if content filter is active
                    categories_str = db.get_config('content_filter', 'categories', '[]')
                    categories = json.loads(categories_str)
                    status['categories_enabled'] = len([c for c in categories if c.get('enabled', False)]) if content_filter_active else 0
                    
                    # Get traffic class counts
                    classes_str = db.get_config('qos', 'classes', '[]')
                    classes = json.loads(classes_str)
                    status['traffic_classes'] = len(classes)
                    
                    # Get filter counts - only count as active if QoS is active
                    filters_str = db.get_config('qos', 'filters', '[]')
                    filters = json.loads(filters_str)
                    status['active_filters'] = len([f for f in filters if f.get('enabled', False)]) if qos_active else 0
                except Exception as e:
                    logger.error(f"Error getting config counts: {e}")
        
        # Get username from session with fallback to user_id
        username = session.get('username', session.get('user_id', 'admin'))
        role = session.get('role', 'user')
        
        # Add logs data in expected format
        logs = []
        for log in recent_logs[:5]:  # Limit to 5 logs
            logs.append({
                'timestamp': log.get('timestamp', ''),
                'action': log.get('action', 'UNKNOWN'),
                'protocol': log.get('protocol', 'TCP'),
                'src_ip': log.get('src_ip', '0.0.0.0'),
                'src_port': log.get('src_port', '0'),
                'dst_ip': log.get('dst_ip', '0.0.0.0'),
                'dst_port': log.get('dst_port', '0')
            })
        
        return render_template('dashboard.html', 
                              system_status=system_status,
                              status=status,
                              recent_logs=recent_logs,
                              logs=logs,
                              rule_status=rule_status, 
                              network_stats=network_stats,
                              username=username, 
                              role=role,
                              using_mock_data=False, 
                              current_app=current_app)
                              
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        
        # Get username from session with fallback to user_id
        username = session.get('username', session.get('user_id', 'admin'))
        role = session.get('role', 'user')
        
        return render_template('error.html', 
                              error="Failed to load dashboard data", 
                              username=username, 
                              role=role,
                              current_app=current_app)

def check_content_filter_active():
    """Check if content filtering is actually active on the system."""
    try:
        platform_system = platform.system().lower()
        
        if platform_system == 'windows':
            # On Windows, check for DNS client blocking rules
            dns_cmd = ["powershell", "-Command", "Get-DnsClientNrptRule | Where-Object {$_.Namespace -like '*'} | Measure-Object | Select-Object -ExpandProperty Count"]
            dns_result = subprocess.run(dns_cmd, capture_output=True, text=True)
            content_filter_active = dns_result.returncode == 0 and int(dns_result.stdout.strip() or '0') > 0
            logger.info(f"Windows content filter active check: {content_filter_active}")
        else:
            # On Linux, check for DNS blocking in hosts file or dnsmasq
            hosts_filter = False
            dnsmasq_filter = False
            
            # Check hosts file for blocked domains
            hosts_file = "/etc/hosts"
            if os.path.exists(hosts_file):
                with open(hosts_file, 'r') as f:
                    hosts_content = f.read()
                    # Check if there are entries that redirect to 0.0.0.0 or 127.0.0.1
                    if re.search(r'(0\.0\.0\.0|127\.0\.0\.1)\s+[a-zA-Z0-9.-]+', hosts_content):
                        hosts_filter = True
            
            # Check if dnsmasq is running
            dnsmasq_cmd = ["ps", "-A"]
            ps_result = subprocess.run(dnsmasq_cmd, capture_output=True, text=True)
            dnsmasq_running = 'dnsmasq' in ps_result.stdout
            
            if dnsmasq_running:
                # Check for dnsmasq config files
                for conf_path in ["/etc/dnsmasq.conf", "/etc/dnsmasq.d"]:
                    if os.path.exists(conf_path):
                        dnsmasq_filter = True
                        break
            
            # Content filter is active if either method is in use
            content_filter_active = hosts_filter or dnsmasq_filter
            logger.info(f"Linux content filter active check: hosts={hosts_filter}, dnsmasq={dnsmasq_filter}")
            
        return content_filter_active
    except Exception as e:
        logger.warning(f"Failed to check content filter status on system: {e}")
        return False

def check_qos_active():
    """Check if QoS is actually active on the system."""
    try:
        platform_system = platform.system().lower()
        
        if platform_system == 'windows':
            # On Windows, check for QoS policies
            qos_cmd = ["powershell", "-Command", "Get-NetQosPolicy | Measure-Object | Select-Object -ExpandProperty Count"]
            qos_result = subprocess.run(qos_cmd, capture_output=True, text=True)
            qos_active = qos_result.returncode == 0 and int(qos_result.stdout.strip() or '0') > 0
            logger.info(f"Windows QoS active check: {qos_active}")
        else:
            # On Linux, check for traffic control (tc) rules
            tc_cmd = ["tc", "qdisc", "show"]
            tc_result = subprocess.run(tc_cmd, capture_output=True, text=True)
            # QoS is active if we have any non-default qdisc rules
            tc_lines = tc_result.stdout.strip().split('\n')
            qos_active = tc_result.returncode == 0 and any("htb" in line or "hfsc" in line or "sfq" in line for line in tc_lines)
            logger.info(f"Linux QoS active check: {qos_active}")
            
        return qos_active
    except Exception as e:
        logger.warning(f"Failed to check QoS status on system: {e}")
        return False

@app.route('/firewall_rules')
@login_required
def firewall_rules():
    """Firewall rules page."""
    per_page = 10
    page = request.args.get('page', 1, type=int)
    chain = request.args.get('chain', None)
    action = request.args.get('action', None)
    search = request.args.get('search', None)
    
    # Default to empty rules list
    rules = []
    total_pages = 1
    using_mock_data = False
    
    # Apply filters
    filters = {}
    if chain and chain != 'all':
        filters['chain'] = chain
    if action and action != 'all':
        filters['action'] = action
    
    # Try to get rules from database if available
    if db:
        try:
            # Check if get_rules method exists
            if hasattr(db, 'get_rules') and callable(getattr(db, 'get_rules')):
                try:
                    # Try with filters and pagination
                    db_rules = db.get_rules(filters, limit=per_page, offset=(page-1)*per_page)
                    
                    # Convert rules to dictionary for template
                    for rule in db_rules:
                        rules.append({
                            'id': getattr(rule, 'id', 0),
                            'chain': getattr(rule, 'chain', 'INPUT'),
                            'action': getattr(rule, 'action', 'ACCEPT'),
                            'protocol': getattr(rule, 'protocol', 'any'),
                            'source_ip': getattr(rule, 'src_ip', 'any'),
                            'dest_ip': getattr(rule, 'dst_ip', 'any'),
                            'source_port': getattr(rule, 'src_port', 'any'),
                            'dest_port': getattr(rule, 'dst_port', 'any'),
                            'description': getattr(rule, 'description', ''),
                            'enabled': getattr(rule, 'enabled', True)
                        })
                    
                    # Apply search filter if provided
                    if search:
                        search = search.lower()
                        filtered_rules = []
                        for rule in rules:
                            if (search in (rule['source_ip'] or '').lower() or
                                search in (rule['dest_ip'] or '').lower() or
                                search in (rule['source_port'] or '').lower() or
                                search in (rule['dest_port'] or '').lower() or
                                search in (rule['description'] or '').lower()):
                                filtered_rules.append(rule)
                        rules = filtered_rules
                    
                    # Try to get total count for pagination
                    try:
                        if hasattr(db, 'count_rules') and callable(getattr(db, 'count_rules')):
                            total_rules = db.count_rules(filters)
                            total_pages = (total_rules + per_page - 1) // per_page  # Ceiling division
                        else:
                            total_pages = 1 if not rules else 2  # Assume there might be more
                    except Exception:
                        total_pages = 1 if not rules else 2  # Assume there might be more
                except Exception as e:
                    logger.error(f"Error calling db.get_rules: {e}")
                    rules = []
                    using_mock_data = True
            else:
                logger.warning("Database missing get_rules method")
                rules = []
                using_mock_data = True
        except Exception as e:
            logger.error(f"Error getting rules from database: {e}")
            rules = []
            using_mock_data = True
    else:
        logger.warning("No database connection")
        using_mock_data = True
    
    # Return empty rules list instead of generating mock data
    if not rules:
        logger.warning("No rules found. Database connection required.")
    
    # Get username from session with fallback to user_id
    username = session.get('username', session.get('user_id', 'admin'))
    role = session.get('role', 'user')
    
    return render_template('firewall_rules.html', rules=rules, page=page, total_pages=total_pages,
                          username=username, role=role,
                          using_mock_data=using_mock_data, current_app=current_app)

@app.route('/content_filter')
@login_required
def content_filter():
    """Content filter page."""
    using_mock_data = False
    enabled = False
    categories = []
    all_domains = []
    
    if db:
        try:
            # Get content filter status and settings
            enabled_str = db.get_config('content_filter', 'enabled', 'false')
            enabled = enabled_str.lower() == 'true'
            
            # Get categories
            categories_str = db.get_config('content_filter', 'categories', '[]')
            categories = json.loads(categories_str)
            
            # Get domains
            domains_str = db.get_config('content_filter', 'domains', '[]')
            all_domains = json.loads(domains_str)
        except Exception as e:
            logger.error(f"Error getting content filter data: {e}")
            using_mock_data = True
    else:
        using_mock_data = True
        logger.warning("No database connection for content filter")
    
    # Get domains with pagination
    per_page = 10
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', None, type=int)
    search = request.args.get('search', None)
    
    # Filter domains
    filtered_domains = []
    for domain in all_domains:
        if category_id is not None and domain.get('category_id') != category_id:
            continue
        
        if search and search.lower() not in domain.get('domain', '').lower():
            continue
        
        filtered_domains.append(domain)
    
    # Simple pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    domains = filtered_domains[start_idx:end_idx]
    
    # Calculate total pages
    total_pages = (len(filtered_domains) + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1
    
    # Get username from session with fallback to user_id
    username = session.get('username', session.get('user_id', 'admin'))
    role = session.get('role', 'user')
    
    return render_template('content_filter.html', enabled=enabled, categories=categories, 
                          domains=domains, page=page, total_pages=total_pages,
                          domain_page=page, domain_total_pages=total_pages,
                          current_category=category_id, search=search,
                          username=username, role=role,
                          using_mock_data=using_mock_data, current_app=current_app)

@app.route('/qos')
@login_required
def qos():
    """QoS (Quality of Service) page."""
    using_mock_data = False
    enabled = False
    classes = []
    all_apps = []
    
    if db:
        try:
            # Get QoS status and settings
            enabled_str = db.get_config('qos', 'enabled', 'false')
            enabled = enabled_str.lower() == 'true'
            
            # Get traffic classes
            classes_str = db.get_config('qos', 'classes', '[]')
            classes = json.loads(classes_str)
            
            # Get applications
            apps_str = db.get_config('qos', 'applications', '[]')
            all_apps = json.loads(apps_str)
        except Exception as e:
            logger.error(f"Error getting QoS data: {e}")
            using_mock_data = True
    else:
        using_mock_data = True
        logger.warning("No database connection for QoS")
    
    # Get applications with pagination
    per_page = 10
    page = request.args.get('page', 1, type=int)
    class_id = request.args.get('class', None, type=int)
    search = request.args.get('search', None)
    
    # Filter applications
    filtered_apps = []
    for app in all_apps:
        if class_id is not None and app.get('class_id') != class_id:
            continue
        
        if search and search.lower() not in app.get('name', '').lower():
            continue
        
        filtered_apps.append(app)
    
    # Simple pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    apps = filtered_apps[start_idx:end_idx]
    
    # Calculate total pages
    total_pages = (len(filtered_apps) + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1
    
    # Get username from session with fallback to user_id
    username = session.get('username', session.get('user_id', 'admin'))
    role = session.get('role', 'user')
    
    return render_template('qos.html', enabled=enabled, classes=classes, 
                          applications=apps, page=page, total_pages=total_pages,
                          current_class=class_id, search=search,
                          username=username, role=role,
                          using_mock_data=using_mock_data, current_app=current_app)

@app.route('/logs')
@login_required
def logs():
    """Logs page."""
    using_mock_data = False
    logs = []
    total_entries = 0
    log_stats = {
        'total': 0,
        'error': 0,
        'warning': 0,
        'info': 0
    }
    
    per_page = 50
    page = request.args.get('page', 1, type=int)
    log_type = request.args.get('type', 'all')
    
    if db:
        try:
            logs = get_recent_logs(limit=per_page, page=page, log_type=log_type)
            
            # Count total entries for pagination
            total_entries = db.count_logs(log_type=log_type if log_type != 'all' else None)
            log_stats = {
                'total': total_entries,
                'error': db.count_logs(log_type='error'),
                'warning': db.count_logs(log_type='warning'),
                'info': db.count_logs(log_type='info')
            }
        except Exception as e:
            logger.error(f"Error getting logs data: {e}")
            using_mock_data = True
    else:
        using_mock_data = True
        logger.warning("No database connection for logs")
    
    # Calculate total pages
    total_pages = (total_entries + per_page - 1) // per_page if total_entries > 0 else 1
    
    # Get username from session with fallback to user_id
    username = session.get('username', session.get('user_id', 'admin'))
    role = session.get('role', 'user')
    
    return render_template('logs.html', logs=logs, page=page, total_pages=total_pages, 
                          log_stats=log_stats, log_type=log_type, total_entries=total_entries,
                          username=username, role=role,
                          using_mock_data=using_mock_data, current_app=current_app)

@app.route('/settings')
@login_required
def settings():
    """Settings page."""
    # Default empty settings
    users = []
    system_settings = {}
    network_settings = {}
    security_settings = {}
    theme_settings = {}
    notification_settings = {}
    
    # Combine all settings into a single settings object
    settings = {
        'general': system_settings,
        'network': network_settings,
        'security': security_settings,
        'theme': theme_settings,
        'notification': notification_settings
    }
    
    # Get settings from database
    using_mock_data = False
    
    if db:
        try:
            # Get users
            db_users = db.get_all_users()
            for user in db_users:
                users.append({
                    'id': getattr(user, 'id', 0),
                    'username': user.username,
                    'role': user.role,
                    'email': getattr(user, 'email', '')
                })
                
            # Get system settings
            system_settings = db.get_all_config('general')
            network_settings = db.get_all_config('network')
            security_settings = db.get_all_config('security')
            theme_settings = db.get_all_config('theme')
            notification_settings = db.get_all_config('notification')
            
            # Update settings object
            settings = {
                'general': system_settings,
                'network': network_settings,
                'security': security_settings,
                'theme': theme_settings,
                'notification': notification_settings
            }
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            using_mock_data = True
    else:
        using_mock_data = True
        logger.warning("No database connection for settings")
    
    # Get username from session with fallback to user_id
    username = session.get('username', session.get('user_id', 'admin'))
    role = session.get('role', 'user')
    
    return render_template(
        'settings.html',
        settings=settings,
        users=users,
        username=username,
        role=role,
        using_mock_data=using_mock_data,
        db_error=db_import_error if db_import_error else None,
        current_app=current_app
    )

# API Routes
@app.route('/api/status')
@login_required
def api_status():
    """API endpoint to get system status."""
    status = get_system_status()
    return jsonify(status)

@app.route('/api/content_filter/toggle', methods=['POST'])
@login_required
def api_content_filter_toggle():
    """API endpoint to toggle content filter on/off."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get current status
        current_status = db.get_config('content_filter', 'enabled', 'false')
        # Toggle status
        new_status = 'false' if current_status.lower() == 'true' else 'true'
        # Save new status
        db.set_config('content_filter', 'enabled', new_status)
        
        return jsonify({'success': True, 'enabled': new_status == 'true'}), 200
    except Exception as e:
        logger.error(f"Error toggling content filter: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content_filter/categories/<int:category_id>/toggle', methods=['POST'])
@login_required
def api_content_filter_category_toggle(category_id):
    """API endpoint to toggle a content filter category on/off."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get categories
        categories_str = db.get_config('content_filter', 'categories', '[]')
        categories = json.loads(categories_str)
        
        # Find the category
        for category in categories:
            if category.get('id') == category_id:
                # Toggle enabled status
                category['enabled'] = not category.get('enabled', True)
                break
        else:
            return jsonify({'error': 'Category not found'}), 404
        
        # Save updated categories
        db.set_config('content_filter', 'categories', json.dumps(categories))
        
        return jsonify({'success': True, 'enabled': category['enabled']}), 200
    except Exception as e:
        logger.error(f"Error toggling category: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content_filter/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_content_filter_category(category_id):
    """API endpoint to manage a content filter category."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get categories
        categories_str = db.get_config('content_filter', 'categories', '[]')
        categories = json.loads(categories_str)
        
        if request.method == 'GET':
            # Find the category
            for category in categories:
                if category.get('id') == category_id:
                    return jsonify(category)
            
            return jsonify({'error': 'Category not found'}), 404
        
        elif request.method == 'PUT':
            # Update the category
            data = request.json
            for i, category in enumerate(categories):
                if category.get('id') == category_id:
                    categories[i].update({
                        'name': data.get('name', category['name']),
                        'description': data.get('description', category.get('description', '')),
                        'enabled': data.get('enabled', category.get('enabled', True))
                    })
                    
                    # Save updated categories
                    db.set_config('content_filter', 'categories', json.dumps(categories))
                    return jsonify({'success': True})
            
            return jsonify({'error': 'Category not found'}), 404
        
        elif request.method == 'DELETE':
            # Delete the category
            for i, category in enumerate(categories):
                if category.get('id') == category_id:
                    del categories[i]
                    
                    # Delete associated domains
                    domains_str = db.get_config('content_filter', 'domains', '[]')
                    domains = json.loads(domains_str)
                    domains = [d for d in domains if d.get('category_id') != category_id]
                    
                    # Save updated categories and domains
                    db.set_config('content_filter', 'categories', json.dumps(categories))
                    db.set_config('content_filter', 'domains', json.dumps(domains))
                    
                    return jsonify({'success': True})
            
            return jsonify({'error': 'Category not found'}), 404
    
    except Exception as e:
        logger.error(f"Error managing category: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content_filter/categories', methods=['GET', 'POST'])
@login_required
def api_content_filter_categories():
    """API endpoint to list and create content filter categories."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get categories
        categories_str = db.get_config('content_filter', 'categories', '[]')
        categories = json.loads(categories_str)
        
        if request.method == 'GET':
            return jsonify(categories)
        
        elif request.method == 'POST':
            # Create a new category
            data = request.json
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'Category name is required'}), 400
            
            # Generate a new ID
            new_id = 1
            if categories:
                new_id = max(c.get('id', 0) for c in categories) + 1
            
            # Create the category
            new_category = {
                'id': new_id,
                'name': data['name'],
                'description': data.get('description', ''),
                'enabled': data.get('enabled', True),
                'count': 0
            }
            
            categories.append(new_category)
            
            # Save updated categories
            db.set_config('content_filter', 'categories', json.dumps(categories))
            
            return jsonify({'success': True, 'id': new_id})
    
    except Exception as e:
        logger.error(f"Error managing categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qos/toggle', methods=['POST'])
@login_required
def api_qos_toggle():
    """API endpoint to toggle QoS on/off."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get current status
        current_status = db.get_config('qos', 'enabled', 'false')
        # Toggle status
        new_status = 'false' if current_status.lower() == 'true' else 'true'
        # Save new status
        db.set_config('qos', 'enabled', new_status)
        
        return jsonify({'success': True, 'enabled': new_status == 'true'}), 200
    except Exception as e:
        logger.error(f"Error toggling QoS: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules')
@login_required
def api_rules():
    """Get firewall rules for API."""
    if not db:
        return jsonify({'error': 'Database connection required'}), 500
    
    try:
        db_rules = db.get_rules()
        rules = []
        for rule in db_rules:
            rules.append({
                'id': rule.id,
                'chain': rule.chain,
                'action': rule.action,
                'protocol': rule.protocol or 'any',
                'src_ip': rule.src_ip or 'any',
                'dst_ip': rule.dst_ip or 'any',
                'src_port': rule.src_port or 'any',
                'dst_port': rule.dst_port or 'any',
                'description': rule.description,
                'enabled': rule.enabled
            })
        return jsonify(rules)
    except Exception as e:
        logger.error(f"Error getting rules from database: {e}")
        return jsonify({'error': 'Error retrieving rules'}), 500

@app.route('/api/rules/<int:rule_id>', methods=['GET'])
@login_required
@csrf_exempt
def api_get_rule(rule_id):
    """API endpoint to get a single firewall rule by ID."""
    if not db:
        return jsonify({'error': 'Database connection required'}), 500
    
    try:
        rules = db.get_rules({'id': rule_id})
        if rules and len(rules) > 0:
            rule = rules[0]
            return jsonify({
                'id': rule.id,
                'chain': rule.chain,
                'action': rule.action,
                'protocol': rule.protocol or '',
                'src_ip': rule.src_ip or '',
                'dst_ip': rule.dst_ip or '',
                'src_port': rule.src_port or '',
                'dst_port': rule.dst_port or '',
                'description': rule.description or '',
                'enabled': rule.enabled,
                'priority': 0  # Default priority value
            })
        return jsonify({'error': 'Rule not found'}), 404
    except Exception as e:
        logger.error(f"Error getting rule {rule_id} from database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
@login_required
def api_logs():
    """Get recent logs for API."""
    if not db:
        return jsonify({'error': 'Database connection required'}), 500
    
    logs = get_recent_logs(limit=50)
    return jsonify(logs)

@app.route('/api/change_password', methods=['POST'])
@login_required
def api_change_password():
    """API endpoint to change user password."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        username = session.get('username', '')
        user = db.get_user(username)
        
        if not user or not db.verify_password(username, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password in database
        db.update_user_password(username, new_password)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/download')
@login_required
def api_backup_download():
    """API endpoint to download a backup of settings."""
    try:
        # Create backup file
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'settings': {}
        }
        
        # Include settings from database if available
        if db:
            # Get all configuration
            for section in ['general', 'network', 'security']:
                backup_data['settings'][section] = {}
                for key, value in db.get_all_config(section).items():
                    backup_data['settings'][section][key] = value
            
            # Include rules
            backup_data['firewall_rules'] = []
            rules = db.get_rules()
            for rule in rules:
                backup_data['firewall_rules'].append({
                    'chain': rule.chain,
                    'action': rule.action,
                    'protocol': rule.protocol,
                    'src_ip': rule.src_ip,
                    'dst_ip': rule.dst_ip,
                    'src_port': rule.src_port,
                    'dst_port': rule.dst_port,
                    'description': rule.description,
                    'enabled': rule.enabled
                })
        
        # Create backup file
        backup_json = json.dumps(backup_data, indent=2)
        
        # Generate response with file download
        response = make_response(backup_json)
        response.headers['Content-Disposition'] = f'attachment; filename=charon_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        response.headers['Content-Type'] = 'application/json'
        
        return response
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
@login_required
def api_backup_restore():
    """API endpoint to restore from a backup file."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Check if file was uploaded
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file uploaded'}), 400
        
        file = request.files['backup_file']
        
        # Read and parse backup file
        backup_data = json.loads(file.read().decode('utf-8'))
        
        # Validate backup format
        if 'version' not in backup_data or 'settings' not in backup_data:
            return jsonify({'error': 'Invalid backup file format'}), 400
        
        # Restore settings
        for section in backup_data['settings']:
            for key, value in backup_data['settings'][section].items():
                db.set_config(section, key, value)
        
        # Restore firewall rules if present
        if 'firewall_rules' in backup_data:
            # First, clear existing rules
            db.clear_rules()
            
            # Add rules from backup
            for rule_data in backup_data['firewall_rules']:
                db.add_rule(
                    chain=rule_data['chain'],
                    action=rule_data['action'],
                    protocol=rule_data['protocol'],
                    src_ip=rule_data['src_ip'],
                    dst_ip=rule_data['dst_ip'],
                    src_port=rule_data['src_port'],
                    dst_port=rule_data['dst_port'],
                    description=rule_data['description'],
                    enabled=rule_data['enabled']
                )
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/factory_reset', methods=['POST'])
@login_required
def api_factory_reset():
    """API endpoint to reset all settings to defaults."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Clear existing settings
        # Firewall rules
        db.clear_rules()
        
        # Set default config values
        db.set_config('firewall', 'enabled', 'true', 'Enable/disable firewall')
        db.set_config('firewall', 'default_policy', 'accept', 'Default policy for firewall')
        db.set_config('firewall', 'log_dropped', 'true', 'Log dropped packets')
        
        db.set_config('content_filter', 'enabled', 'false', 'Enable/disable content filter')
        db.set_config('content_filter', 'block_malware', 'true', 'Block malware sites')
        db.set_config('content_filter', 'block_adult', 'false', 'Block adult content')
        
        db.set_config('qos', 'enabled', 'false', 'Enable/disable QoS')
        db.set_config('qos', 'prioritize_voip', 'true', 'Prioritize VoIP traffic')
        
        db.set_config('system', 'hostname', 'charon', 'System hostname')
        db.set_config('system', 'timezone', 'UTC', 'System timezone')
        
        # Add default rules
        default_rules = [
            {
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': '22',
                'description': 'Allow SSH',
                'enabled': True
            },
            {
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': '80',
                'description': 'Allow HTTP',
                'enabled': True
            },
            {
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': '443',
                'description': 'Allow HTTPS',
                'enabled': True
            }
        ]
        
        for rule in default_rules:
            # Pass each rule as a dictionary
            db.add_rule(rule)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error performing factory reset: {e}")
        return jsonify({'error': str(e)}), 500

# User management routes (admin only)
@app.route('/users')
@login_required
def user_management():
    """User management page."""
    # Only admin can access this page
    if session.get('role') != 'admin':
        flash('Access denied. You need administrator privileges.', 'error')
        return redirect(url_for('dashboard'))
    
    users = []
    
    # Try to get users from database first
    if db:
        try:
            db_users = db.get_all_users()
            for user in db_users:
                users.append({
                    'username': user.username,
                    'role': user.role,
                    'email': user.email,
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            return render_template('user_management.html', users=users, source='database', current_app=current_app)
        except Exception as e:
            logger.error(f"Error getting users from database: {e}")
    
    # Fall back to JSON if database unavailable
    try:
        users_dict = load_users()
        for username, data in users_dict.items():
            users.append({
                'username': username,
                'role': data.get('role', 'user'),
                'email': None,
                'last_login': 'Unknown',
                'created_at': 'Unknown'
            })
        return render_template('user_management.html', users=users, source='json', current_app=current_app)
    except Exception as e:
        logger.error(f"Error getting users from JSON: {e}")
        flash('Error loading user data', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/users', methods=['POST'])
@login_required
def api_add_user():
    """Add a new user via API."""
    # Only admin can add users
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Validate role
    if role not in ['admin', 'user']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400
    
    # Try to add user to database first
    success = False
    
    if db:
        try:
            user_id = db.add_user(username, password, role, email)
            if user_id:
                success = True
                logger.info(f"User {username} added to database")
        except Exception as e:
            logger.error(f"Error adding user to database: {e}")
    
    # Fall back to JSON if database unavailable
    if not success:
        try:
            users = load_users()
            if username in users:
                return jsonify({'success': False, 'message': 'User already exists'}), 400
            
            users[username] = {
                'password': hash_password(password),
                'role': role
            }
            save_users(users)
            success = True
            logger.info(f"User {username} added to JSON (fallback)")
        except Exception as e:
            logger.error(f"Error adding user to JSON: {e}")
            return jsonify({'success': False, 'message': 'Error adding user'}), 500
    
    if success:
        return jsonify({'success': True, 'message': 'User added successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to add user'}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def api_delete_user(username):
    """Delete a user via API."""
    # Only admin can delete users, and can't delete themselves
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if username == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    # Try to delete from database first
    success = False
    
    if db:
        try:
            if db.delete_user(username):
                success = True
                logger.info(f"User {username} deleted from database")
        except Exception as e:
            logger.error(f"Error deleting user from database: {e}")
    
    # Fall back to JSON if database unavailable
    if not success:
        try:
            users = load_users()
            if username not in users:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            del users[username]
            save_users(users)
            success = True
            logger.info(f"User {username} deleted from JSON (fallback)")
        except Exception as e:
            logger.error(f"Error deleting user from JSON: {e}")
            return jsonify({'success': False, 'message': 'Error deleting user'}), 500
    
    if success:
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to delete user'}), 500

@app.route('/api/admin/change-password', methods=['POST'])
@login_required
def api_admin_change_password():
    """Change password for another user (admin only)."""
    # Only admin can change other users' passwords
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    if not username or not new_password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Try to change password in database first
    success = False
    
    if db:
        try:
            if db.update_user_password(username, new_password):
                success = True
                logger.info(f"Admin {session['user_id']} changed password for user {username}")
        except Exception as e:
            logger.error(f"Error changing password in database: {e}")
    
    # Fall back to JSON if database unavailable
    if not success:
        try:
            users = load_users()
            if username not in users:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            users[username]['password'] = hash_password(new_password)
            save_users(users)
            success = True
            logger.info(f"Admin {session['user_id']} changed password for user {username} in JSON (fallback)")
        except Exception as e:
            logger.error(f"Error changing password in JSON: {e}")
            return jsonify({'success': False, 'message': 'Error changing password'}), 500
    
    if success:
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to change password'}), 500

@app.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    """API endpoint to save settings."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Process form data and save to database
        for section in ['general', 'network', 'security']:
            for key in request.form:
                if key.startswith(f"{section}_"):
                    continue  # Skip composite keys
                
                # Get the actual value, handle checkboxes
                value = request.form.get(key, '')
                if key in ['auto_update', 'require_strong_passwords']:
                    value = 'true' if value == 'on' else 'false'
                
                # Save to database
                db.set_config(section, key, value)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'error': str(e)}), 500

# Add missing API route for creating a new rule
@app.route('/api/rules', methods=['POST'])
@login_required
@csrf_exempt
def api_create_rule():
    """API endpoint to create a new firewall rule."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('chain') or not data.get('action'):
            return jsonify({'error': 'Chain and action are required'}), 400
        
        # Create rule_data dictionary with all parameters
        rule_data = {
            'chain': data.get('chain'),
            'action': data.get('action'),
            'protocol': data.get('protocol') if data.get('protocol') != 'any' else None,
            'src_ip': data.get('src_ip') if data.get('src_ip') != 'any' else None,
            'dst_ip': data.get('dst_ip') if data.get('dst_ip') != 'any' else None,
            'src_port': data.get('src_port') if data.get('src_port') != 'any' else None,
            'dst_port': data.get('dst_port') if data.get('dst_port') != 'any' else None,
            'description': data.get('description'),
            'enabled': data.get('enabled', True)
        }
        
        # Add rule to database - pass the rule_data dictionary directly
        rule_id = db.add_rule(rule_data)
        
        if rule_id:
            return jsonify({'success': True, 'id': rule_id})
        else:
            return jsonify({'error': 'Failed to create rule'}), 500
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        return jsonify({'error': str(e)}), 500

# Add missing API route for updating a rule
@app.route('/api/rules/<int:rule_id>', methods=['PUT'])
@login_required
@csrf_exempt
def api_update_rule(rule_id):
    """API endpoint to update a firewall rule."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        data = request.json
        
        # Prepare rule data
        rule_data = {}
        if 'chain' in data:
            rule_data['chain'] = data['chain']
        if 'action' in data:
            rule_data['action'] = data['action']
        if 'protocol' in data:
            rule_data['protocol'] = data['protocol'] if data['protocol'] != 'any' else None
        if 'src_ip' in data:
            rule_data['src_ip'] = data['src_ip'] if data['src_ip'] != 'any' else None
        if 'dst_ip' in data:
            rule_data['dst_ip'] = data['dst_ip'] if data['dst_ip'] != 'any' else None
        if 'src_port' in data:
            rule_data['src_port'] = data['src_port'] if data['src_port'] != 'any' else None
        if 'dst_port' in data:
            rule_data['dst_port'] = data['dst_port'] if data['dst_port'] != 'any' else None
        if 'description' in data:
            rule_data['description'] = data['description']
        if 'enabled' in data:
            rule_data['enabled'] = data['enabled']
        
        # Update rule in database
        success = db.update_rule(rule_id, rule_data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Rule not found or update failed'}), 404
    except Exception as e:
        logger.error(f"Error updating rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Add missing API route for deleting a rule
@app.route('/api/rules/<int:rule_id>', methods=['DELETE'])
@login_required
@csrf_exempt
def api_delete_rule(rule_id):
    """API endpoint to delete a firewall rule."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Delete rule from database
        success = db.delete_rule(rule_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Rule not found or delete failed'}), 404
    except Exception as e:
        logger.error(f"Error deleting rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Add missing API route for toggling a rule (enable/disable)
@app.route('/api/rules/<int:rule_id>/toggle', methods=['PATCH'])
@login_required
@csrf_exempt
def api_toggle_rule(rule_id):
    """API endpoint to toggle a firewall rule's enabled status."""
    if not db:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        # Get current rule
        rules = db.get_rules({'id': rule_id})
        if not rules or len(rules) == 0:
            return jsonify({'error': 'Rule not found'}), 404
        
        rule = rules[0]
        
        # Toggle enabled status
        new_status = not rule.enabled
        
        # Update rule
        success = db.update_rule(rule_id, {'enabled': new_status})
        
        if success:
            return jsonify({'success': True, 'enabled': new_status})
        else:
            return jsonify({'error': 'Failed to update rule status'}), 500
    except Exception as e:
        logger.error(f"Error toggling rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found", current_app=current_app), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Internal server error", current_app=current_app), 500

# Main entry point
if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('CHARON_WEB_PORT', 5000))
    host = os.environ.get('CHARON_WEB_HOST', '0.0.0.0')
    debug = os.environ.get('CHARON_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Charon web interface on {host}:{port}")
    app.run(host=host, port=port, debug=debug) 