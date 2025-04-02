#!/usr/bin/env python3
"""
Web Server Module for Charon Firewall

This module provides a web interface for the Charon firewall.
"""

import os
import json
import logging
import datetime
import psutil
import hashlib
from functools import wraps
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort, current_app, make_response
import sys

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
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=12)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('CHARON_SECURE_COOKIES', 'False').lower() == 'true'

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
                    db.add_user('admin', 'admin', 'admin')
                    logger.info("Created default admin user in database")
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
        logger.warning("No users file found, created default admin user")
        users = {
            'admin': {
                'password': hash_password('admin'),
                'role': 'admin'
            }
        }
        save_users(users)
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

# Helper functions for getting system data
def get_system_status():
    """Get the current system status."""
    try:
        use_mock_data = os.environ.get('USE_MOCK_DATA', 'false').lower() == 'true'
        use_real_firewall = os.environ.get('USE_REAL_FIREWALL', 'true').lower() == 'true'
        
        # Get firewall rules count from database if available
        active_rules = 0
        if db:
            active_rules = len(db.get_rules(filters={'enabled': True}))
        
        # If using real firewall data, try to get actual firewall information
        if use_real_firewall and not use_mock_data:
            try:
                # Try to read iptables rules
                iptables_rules_file = '/etc/charon/iptables-rules.conf'
                if os.path.exists(iptables_rules_file):
                    with open(iptables_rules_file, 'r') as f:
                        rules = f.readlines()
                        active_rules = sum(1 for line in rules if line.strip().startswith('-A'))
                
                # Get content filter status from logs
                content_filter_enabled = os.path.exists('/etc/charon/content-filter.enabled')
                
                # Try to count blocked domains from actual files
                blocked_domains_file = '/etc/charon/blocked_domains.txt'
                blocked_domains = 0
                if os.path.exists(blocked_domains_file):
                    with open(blocked_domains_file, 'r') as f:
                        blocked_domains = sum(1 for _ in f)
                
                # Count categories from files
                categories_enabled = 0
                categories_dir = '/etc/charon/categories'
                if os.path.exists(categories_dir):
                    categories_enabled = len([f for f in os.listdir(categories_dir) 
                                            if os.path.isfile(os.path.join(categories_dir, f)) and 
                                            f.endswith('.enabled')])
                
                # Get QoS status from actual config
                qos_enabled = os.path.exists('/etc/charon/qos.enabled')
                
                # Get traffic classes and filters from tc command if available
                traffic_classes = 0
                active_filters = 0
                
                # Try to get TC info by running the command
                try:
                    import subprocess
                    tc_output = subprocess.check_output(['tc', 'class', 'show']).decode('utf-8')
                    traffic_classes = len([line for line in tc_output.split('\n') if 'class' in line])
                    
                    tc_filter_output = subprocess.check_output(['tc', 'filter', 'show']).decode('utf-8')
                    active_filters = len([line for line in tc_filter_output.split('\n') if 'filter' in line])
                except:
                    # Fall back to checking if files exist
                    if os.path.exists('/etc/charon/tc_classes.conf'):
                        with open('/etc/charon/tc_classes.conf', 'r') as f:
                            traffic_classes = len(f.readlines())
                    
                    if os.path.exists('/etc/charon/tc_filters.conf'):
                        with open('/etc/charon/tc_filters.conf', 'r') as f:
                            active_filters = len(f.readlines())
                
                # Get real system stats
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage('/').percent
                
                return {
                    'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'active_rules': active_rules,
                    'content_filter_enabled': content_filter_enabled,
                    'blocked_domains': blocked_domains,
                    'categories_enabled': categories_enabled,
                    'qos_enabled': qos_enabled,
                    'traffic_classes': traffic_classes,
                    'active_filters': active_filters,
                    'cpu_usage': round(cpu_usage),
                    'memory_usage': round(memory_usage),
                    'disk_usage': round(disk_usage),
                    'is_real_data': True
                }
            except Exception as e:
                logger.error(f"Error getting real firewall data: {e}")
                # Fall through to database or mock data if we can't get real data
        
        # Get data from database if available
        if db and not use_mock_data:
            try:
                # Get content filter status from database if available
                cf_enabled = db.get_config('content_filter', 'enabled', 'false').lower()
                content_filter_enabled = cf_enabled == 'true'
                
                # Get count of domains and categories if available
                domains_data = db.get_config('content_filter', 'domains_count', '0')
                blocked_domains = int(domains_data) if domains_data.isdigit() else 0
                
                categories_data = db.get_config('content_filter', 'categories_enabled', '0')
                categories_enabled = int(categories_data) if categories_data.isdigit() else 0
                
                # Get QoS status from database if available
                qos_status = db.get_config('qos', 'enabled', 'false').lower()
                qos_enabled = qos_status == 'true'
                
                tc_data = db.get_config('qos', 'traffic_classes', '0')
                traffic_classes = int(tc_data) if tc_data.isdigit() else 0
                
                af_data = db.get_config('qos', 'active_filters', '0')
                active_filters = int(af_data) if af_data.isdigit() else 0
                
                return {
                    'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'active_rules': active_rules,
                    'content_filter_enabled': content_filter_enabled,
                    'blocked_domains': blocked_domains,
                    'categories_enabled': categories_enabled,
                    'qos_enabled': qos_enabled,
                    'traffic_classes': traffic_classes,
                    'active_filters': active_filters,
                    'cpu_usage': round(psutil.cpu_percent()),
                    'memory_usage': round(psutil.virtual_memory().percent),
                    'disk_usage': round(psutil.disk_usage('/').percent),
                    'is_real_data': True
                }
            except Exception as e:
                logger.error(f"Error getting system status from database: {e}")
                # Fall through to mock data
        
        # Use mock data as last resort
        if use_mock_data:
            logger.warning("Using mock data for system status")
            return {
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active_rules': 15,
                'content_filter_enabled': True,
                'blocked_domains': 1250,
                'categories_enabled': 5,
                'qos_enabled': False,
                'traffic_classes': 4,
                'active_filters': 0,
                'cpu_usage': round(psutil.cpu_percent()),
                'memory_usage': round(psutil.virtual_memory().percent),
                'disk_usage': round(psutil.disk_usage('/').percent),
                'is_real_data': False
            }
        else:
            # If we get here, neither real data nor database data was available
            # Return minimal non-mock data
            return {
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'active_rules': active_rules if active_rules > 0 else 0,
                'content_filter_enabled': False,
                'blocked_domains': 0,
                'categories_enabled': 0,
                'qos_enabled': False,
                'traffic_classes': 0,
                'active_filters': 0,
                'cpu_usage': round(psutil.cpu_percent()),
                'memory_usage': round(psutil.virtual_memory().percent),
                'disk_usage': round(psutil.disk_usage('/').percent),
                'is_real_data': True
            }
            
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_rules': 0,
            'content_filter_enabled': False,
            'blocked_domains': 0,
            'categories_enabled': 0,
            'qos_enabled': False,
            'traffic_classes': 0,
            'active_filters': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'is_real_data': False,
            'error': str(e)
        }

def get_recent_logs(limit=10):
    """Get recent firewall logs."""
    use_mock_data = os.environ.get('USE_MOCK_DATA', 'false').lower() == 'true'
    use_real_firewall = os.environ.get('USE_REAL_FIREWALL', 'true').lower() == 'true'
    
    # First try to get logs from real firewall logs
    if use_real_firewall and not use_mock_data:
        try:
            # Try to read the firewall logs
            logs = []
            log_file = '/var/log/charon/firewall-events.log'
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_lines = f.readlines()[-limit:]
                    
                    for line in log_lines:
                        # Parse the log line
                        parts = line.split()
                        if len(parts) >= 9:
                            timestamp = ' '.join(parts[0:3])
                            action = 'ACCEPT' if 'ACCEPT' in line else 'DROP' if 'DROP' in line else 'UNKNOWN'
                            
                            # Try to extract protocol and IPs
                            protocol = 'TCP'
                            src_ip = '0.0.0.0'
                            dst_ip = '0.0.0.0'
                            src_port = ''
                            dst_port = ''
                            
                            # Look for SRC= and DST= patterns
                            for part in parts:
                                if part.startswith('PROTO='):
                                    protocol = part.split('=')[1]
                                elif part.startswith('SRC='):
                                    src_ip = part.split('=')[1]
                                elif part.startswith('DST='):
                                    dst_ip = part.split('=')[1]
                                elif part.startswith('SPT='):
                                    src_port = part.split('=')[1]
                                elif part.startswith('DPT='):
                                    dst_port = part.split('=')[1]
                            
                            logs.append({
                                'timestamp': timestamp,
                                'action': action,
                                'protocol': protocol,
                                'src_ip': src_ip,
                                'src_port': src_port,
                                'dst_ip': dst_ip,
                                'dst_port': dst_port
                            })
                
                return logs
            
            # Alternative: try to read from syslog or kern.log if we couldn't get our parsed logs
            host_log_path = os.environ.get('HOST_LOG_PATH', '/host/var/log')
            if os.path.exists(f"{host_log_path}/kern.log"):
                logs = []
                with open(f"{host_log_path}/kern.log", 'r') as f:
                    # Read the last 1000 lines and filter for firewall related lines
                    lines = f.readlines()[-1000:]
                    firewall_lines = [line for line in lines if 'IN=' in line and ('DROP' in line or 'ACCEPT' in line)]
                    
                    # Take only the last 'limit' lines
                    firewall_lines = firewall_lines[-limit:]
                    
                    for line in firewall_lines:
                        # Parse the log line (similar to above)
                        parts = line.split()
                        if len(parts) >= 9:
                            timestamp = ' '.join(parts[0:3])
                            action = 'ACCEPT' if 'ACCEPT' in line else 'DROP' if 'DROP' in line else 'UNKNOWN'
                            
                            # Try to extract protocol and IPs
                            protocol = 'TCP'
                            src_ip = '0.0.0.0'
                            dst_ip = '0.0.0.0'
                            src_port = ''
                            dst_port = ''
                            
                            # Look for SRC= and DST= patterns
                            for part in parts:
                                if part.startswith('PROTO='):
                                    protocol = part.split('=')[1]
                                elif part.startswith('SRC='):
                                    src_ip = part.split('=')[1]
                                elif part.startswith('DST='):
                                    dst_ip = part.split('=')[1]
                                elif part.startswith('SPT='):
                                    src_port = part.split('=')[1]
                                elif part.startswith('DPT='):
                                    dst_port = part.split('=')[1]
                            
                            logs.append({
                                'timestamp': timestamp,
                                'action': action,
                                'protocol': protocol,
                                'src_ip': src_ip,
                                'src_port': src_port,
                                'dst_ip': dst_ip,
                                'dst_port': dst_port
                            })
                
                return logs
        except Exception as e:
            logger.error(f"Error getting real firewall logs: {e}")
            # Fall through to database or mock data
    
    # If we couldn't get real logs, try database
    if db and not use_mock_data:
        try:
            db_logs = db.get_logs(limit=limit)
            logs = []
            for log in db_logs:
                logs.append({
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'action': log.action,
                    'protocol': log.protocol,
                    'src_ip': log.src_ip,
                    'src_port': log.src_port,
                    'dst_ip': log.dst_ip,
                    'dst_port': log.dst_port
                })
            return logs
        except Exception as e:
            logger.error(f"Error getting logs from database: {e}")
            # Fall through to mock data
    
    # Use mock data as last resort
    if use_mock_data:
        logger.warning("Using mock data for firewall logs")
        # Return mock data for logs
        logs = []
        for i in range(limit):
            action = 'DROP' if i % 3 == 0 else 'ACCEPT'
            timestamp = (datetime.datetime.now() - datetime.timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M:%S')
            protocol = 'TCP' if i % 2 == 0 else 'UDP'
            src_port = str(1024 + (i * 100)) if i % 2 == 0 else ''
            dst_port = '80' if i % 4 == 0 else '443' if i % 4 == 1 else '22' if i % 4 == 2 else '53'
            
            logs.append({
                'timestamp': timestamp,
                'action': action,
                'protocol': protocol,
                'src_ip': f'192.168.1.{i+10}',
                'src_port': src_port,
                'dst_ip': f'10.0.0.{i+1}',
                'dst_port': dst_port
            })
        return logs
    else:
        # If neither real nor database logs are available, and we're not using mock data
        # Return an empty list
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
    # Get system status
    status = get_system_status()
    
    # Get recent logs
    logs = get_recent_logs()
    
    # Check if using mock data
    using_mock_data = db is None
    
    # Add current_app to the template context and session for user info
    return render_template(
        'dashboard.html', 
        status=status, 
        logs=logs, 
        using_mock_data=using_mock_data,
        db_error=db_import_error if db_import_error else None,
        current_app=current_app, 
        session=session
    )

@app.route('/firewall_rules')
@login_required
def firewall_rules():
    """Firewall rules management page."""
    # Get firewall rules
    rules = []
    
    if db:
        try:
            db_rules = db.get_rules()
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
        except Exception as e:
            logger.error(f"Error getting rules from database: {e}")
    
    # Return mock data if no database or error
    if not rules:
        # Basic set of default rules for demonstration
        rules = [
            {
                'id': 1,
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': 'any',
                'dst_ip': 'any',
                'src_port': 'any',
                'dst_port': '22',
                'description': 'Allow SSH',
                'enabled': True
            },
            {
                'id': 2,
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': 'any',
                'dst_ip': 'any',
                'src_port': 'any',
                'dst_port': '80',
                'description': 'Allow HTTP',
                'enabled': True
            },
            {
                'id': 3,
                'chain': 'INPUT',
                'action': 'ACCEPT',
                'protocol': 'TCP',
                'src_ip': 'any',
                'dst_ip': 'any',
                'src_port': 'any',
                'dst_port': '443',
                'description': 'Allow HTTPS',
                'enabled': True
            }
        ]
    
    return render_template('firewall_rules.html', rules=rules, current_app=current_app, session=session)

@app.route('/content_filter')
@login_required
def content_filter():
    """Content filtering page."""
    # Get content filter configuration
    config = {
        'enabled': False,
        'categories': [],
        'domains': []
    }
    
    if db:
        try:
            # Get filter status from database
            enabled = db.get_config('content_filter', 'enabled', 'false').lower() == 'true'
            config['enabled'] = enabled
            
            # Get categories and domains if available
            categories_str = db.get_config('content_filter', 'categories', '[]')
            domains_str = db.get_config('content_filter', 'domains', '[]')
            
            try:
                config['categories'] = json.loads(categories_str)
                config['domains'] = json.loads(domains_str)
            except json.JSONDecodeError:
                logger.error("Error decoding content filter configuration")
        except Exception as e:
            logger.error(f"Error getting content filter config: {e}")
    
    # Sample data if none exists
    if not config['categories']:
        config['categories'] = [
            {'id': 1, 'name': 'Advertising', 'enabled': True, 'count': 451},
            {'id': 2, 'name': 'Malware', 'enabled': True, 'count': 623},
            {'id': 3, 'name': 'Adult Content', 'enabled': False, 'count': 1254},
            {'id': 4, 'name': 'Social Media', 'enabled': False, 'count': 103},
            {'id': 5, 'name': 'Gambling', 'enabled': True, 'count': 87}
        ]
    
    if not config['domains']:
        config['domains'] = [
            {'id': 1, 'domain': 'ads.example.com', 'category_id': 1, 'category': 'Advertising', 'added_date': '2023-01-15'},
            {'id': 2, 'domain': 'malware.example.com', 'category_id': 2, 'category': 'Malware', 'added_date': '2023-01-20'},
            {'id': 3, 'domain': 'tracker.example.com', 'category_id': 1, 'category': 'Advertising', 'added_date': '2023-02-01'}
        ]
    
    # Calculate statistics
    filter_enabled = config['enabled']
    category_count = len(config['categories'])
    domain_count = len(config['domains'])
    blocked_today = 157  # Example value, should be retrieved from logs in a real implementation
    last_update = "2023-04-01 08:30"  # Example value
    
    # For domain pagination
    domain_page = request.args.get('page', 1, type=int)
    domain_total_pages = max(1, (domain_count + 9) // 10)  # 10 items per page
    
    # For category filtering
    category_filter = request.args.get('category', 'all')
    
    # Pass all variables to the template
    return render_template(
        'content_filter.html',
        categories=config['categories'],
        domains=config['domains'],
        filter_enabled=filter_enabled,
        category_count=category_count,
        domain_count=domain_count,
        blocked_today=blocked_today,
        last_update=last_update,
        domain_page=domain_page,
        domain_total_pages=domain_total_pages,
        username=session.get('username', 'Admin'),
        current_app=current_app,
        session=session
    )

@app.route('/qos')
@login_required
def qos():
    """Quality of Service (QoS) page."""
    # Get QoS configuration
    config = {
        'enabled': False,
        'interface': 'eth0',
        'total_bandwidth': 100,
        'classes': [],
        'filters': []
    }
    
    if db:
        try:
            # Get QoS status from database
            enabled = db.get_config('qos', 'enabled', 'false').lower() == 'true'
            config['enabled'] = enabled
            
            # Get interface and bandwidth
            config['interface'] = db.get_config('qos', 'interface', 'eth0')
            bandwidth_str = db.get_config('qos', 'total_bandwidth', '100')
            config['total_bandwidth'] = int(bandwidth_str) if bandwidth_str.isdigit() else 100
            
            # Get classes and filters if available
            classes_str = db.get_config('qos', 'classes', '[]')
            filters_str = db.get_config('qos', 'filters', '[]')
            
            try:
                config['classes'] = json.loads(classes_str)
                config['filters'] = json.loads(filters_str)
            except json.JSONDecodeError:
                logger.error("Error decoding QoS configuration")
        except Exception as e:
            logger.error(f"Error getting QoS config: {e}")
    
    # Sample data if none exists
    if not config['classes']:
        config['classes'] = [
            {'id': 1, 'name': 'High Priority', 'priority': 1, 'bandwidth': 20},
            {'id': 2, 'name': 'Medium Priority', 'priority': 2, 'bandwidth': 30},
            {'id': 3, 'name': 'Low Priority', 'priority': 3, 'bandwidth': 40},
            {'id': 4, 'name': 'Background', 'priority': 4, 'bandwidth': 10}
        ]
    
    if not config['filters']:
        config['filters'] = [
            {'id': 1, 'class_id': 1, 'protocol': 'TCP', 'src_ip': 'any', 'dst_ip': 'any', 'dst_port': '22,80,443', 'description': 'Important Web Traffic'},
            {'id': 2, 'class_id': 2, 'protocol': 'TCP', 'src_ip': 'any', 'dst_ip': 'any', 'dst_port': '22', 'description': 'SSH Traffic'},
            {'id': 3, 'class_id': 3, 'protocol': 'UDP', 'src_ip': 'any', 'dst_ip': 'any', 'dst_port': 'any', 'description': 'UDP Traffic'},
        ]
    
    # Add pagination variables
    page = request.args.get('page', 1, type=int)
    total_pages = max(1, (len(config['filters']) + 9) // 10)  # 10 items per page
    
    # Add all variables needed by the template
    qos_enabled = config['enabled']
    bandwidth_usage = 65  # Example usage data
    active_policies = len(config['filters'])
    prioritized_traffic = 35  # Example percentage
    throttled_traffic = 15    # Example percentage
    
    # Network bandwidth settings
    uplink_speed = 100       # Default uplink speed in Mbps
    downlink_speed = 500     # Default downlink speed in Mbps
    buffer_size = 128        # Default buffer size in KB
    packet_limit = 1000      # Default packet queue limit
    ecn_enabled = False      # ECN enabled by default?
    fq_codel_enabled = True  # FQ-CoDel enabled by default?
    
    # Convert classes to the format needed by the template
    traffic_classes = []
    for cls in config['classes']:
        traffic_classes.append({
            'id': cls['id'],
            'name': cls['name'],
            'priority': cls['priority'],
            'min_bandwidth': cls.get('min_bandwidth', 0),
            'max_bandwidth': cls.get('max_bandwidth', cls['bandwidth']),
            'description': cls.get('description', f"{cls['name']} Traffic Class")
        })
    
    # Convert filters to traffic rules for the template
    traffic_rules = []
    for fltr in config['filters']:
        # Find the class name for this rule
        class_name = "Default"
        for cls in traffic_classes:
            if cls['id'] == fltr.get('class_id'):
                class_name = cls['name']
                break
                
        traffic_rules.append({
            'id': fltr['id'],
            'name': fltr.get('description', f"Rule {fltr['id']}"),
            'class_id': fltr.get('class_id', 1),
            'class_name': class_name,
            'source': fltr.get('src_ip', 'any'),
            'destination': fltr.get('dst_ip', 'any'),
            'protocol': fltr.get('protocol', 'any'),
            'port': fltr.get('dst_port', 'any'),
            'enabled': fltr.get('enabled', True)
        })
    
    # Get the username for the template
    username = session.get('user_id', 'Admin')
    
    return render_template(
        'qos.html',
        config=config,
        page=page,
        total_pages=total_pages,
        qos_enabled=qos_enabled,
        bandwidth_usage=bandwidth_usage,
        active_policies=active_policies,
        prioritized_traffic=prioritized_traffic,
        throttled_traffic=throttled_traffic,
        uplink_speed=uplink_speed,
        downlink_speed=downlink_speed,
        buffer_size=buffer_size,
        packet_limit=packet_limit,
        ecn_enabled=ecn_enabled,
        fq_codel_enabled=fq_codel_enabled,
        traffic_classes=traffic_classes,
        traffic_rules=traffic_rules,
        username=username,
        current_app=current_app,
        session=session
    )

@app.route('/logs')
@login_required
def logs():
    """Logs page."""
    # Get logs with higher limit
    firewall_logs = get_recent_logs(limit=50)
    
    return render_template('logs.html', logs=firewall_logs, current_app=current_app, session=session)

@app.route('/settings')
@login_required
def settings():
    """Settings page."""
    # Get current settings
    settings = {
        'general': {
            'hostname': 'charon-firewall',
            'timezone': 'UTC',
            'auto_update': True
        },
        'network': {
            'interface': 'eth0',
            'ip_address': '192.168.1.1',
            'netmask': '255.255.255.0',
            'gateway': '192.168.1.254',
            'dns': '8.8.8.8, 8.8.4.4'
        },
        'security': {
            'failed_login_attempts': 5,
            'session_timeout': 720,
            'require_strong_passwords': True
        }
    }
    
    if db:
        try:
            # Get settings from database
            for section in settings:
                for key in settings[section]:
                    # Convert value to the appropriate type
                    value = db.get_config(section, key, str(settings[section][key]))
                    
                    # Convert string to appropriate type
                    if isinstance(settings[section][key], bool):
                        settings[section][key] = value.lower() == 'true'
                    elif isinstance(settings[section][key], int):
                        settings[section][key] = int(value) if value.isdigit() else settings[section][key]
                    else:
                        settings[section][key] = value
        except Exception as e:
            logger.error(f"Error getting settings from database: {e}")
    
    return render_template('settings.html', settings=settings, current_app=current_app, session=session)

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

@app.route('/api/logs')
@login_required
def api_logs():
    """Get recent logs for API."""
    logs = get_recent_logs(limit=50)
    return jsonify(logs)

@app.route('/api/rules')
@login_required
def api_rules():
    """Get firewall rules for API."""
    if db:
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
    
    # Return mock data if no database or error
    rules = [
        {
            'id': 1,
            'chain': 'INPUT',
            'action': 'ACCEPT',
            'protocol': 'TCP',
            'src_ip': 'any',
            'dst_ip': 'any',
            'src_port': 'any',
            'dst_port': '22',
            'description': 'Allow SSH',
            'enabled': True
        },
        {
            'id': 2,
            'chain': 'INPUT',
            'action': 'ACCEPT',
            'protocol': 'TCP',
            'src_ip': 'any',
            'dst_ip': 'any',
            'src_port': 'any',
            'dst_port': '80',
            'description': 'Allow HTTP',
            'enabled': True
        },
        {
            'id': 3,
            'chain': 'INPUT',
            'action': 'ACCEPT',
            'protocol': 'TCP',
            'src_ip': 'any',
            'dst_ip': 'any',
            'src_port': 'any',
            'dst_port': '443',
            'description': 'Allow HTTPS',
            'enabled': True
        }
    ]
    return jsonify(rules)

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
            'timestamp': datetime.datetime.now().isoformat(),
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
        response.headers['Content-Disposition'] = f'attachment; filename=charon_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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
        # Reset settings
        default_settings = {
            'general': {
                'hostname': 'charon-firewall',
                'timezone': 'UTC',
                'auto_update': 'true'
            },
            'network': {
                'interface': 'eth0',
                'ip_address': '192.168.1.1',
                'netmask': '255.255.255.0',
                'gateway': '192.168.1.254',
                'dns': '8.8.8.8, 8.8.4.4'
            },
            'security': {
                'failed_login_attempts': '5',
                'session_timeout': '720',
                'require_strong_passwords': 'true'
            }
        }
        
        # Apply default settings
        for section in default_settings:
            for key, value in default_settings[section].items():
                db.set_config(section, key, value)
        
        # Clear and reset firewall rules
        db.clear_rules()
        
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
            db.add_rule(
                chain=rule['chain'],
                action=rule['action'],
                protocol=rule['protocol'],
                src_ip=rule['src_ip'],
                dst_ip=rule['dst_ip'],
                src_port=rule['src_port'],
                dst_port=rule['dst_port'],
                description=rule['description'],
                enabled=rule['enabled']
            )
        
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

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found", current_app=current_app), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Internal server error", current_app=current_app), 500

# Main entry point
if __name__ == '__main__':
    # Enable development mode
    app.debug = True
    # Run the application
    app.run(host='0.0.0.0', port=5000) 