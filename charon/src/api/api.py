#!/usr/bin/env python3
"""
API Module for Charon Firewall

This module provides a RESTful API for external applications to interact with the firewall.
"""

import logging
import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
import jwt
from flask import Flask, request, jsonify, g
from functools import wraps

from ..db.database import Database
from ..core.packet_filter import PacketFilter
from ..core.content_filter import ContentFilter
from ..core.qos import QoS
from ..scheduler.firewall_scheduler import FirewallScheduler
from ..plugins.plugin_manager import PluginManager

logger = logging.getLogger('charon.api')

app = Flask(__name__)

# Set a secret key for JWT
app.config['SECRET_KEY'] = os.environ.get('CHARON_API_SECRET', 'dev_key_change_in_production')

# Store for API keys (in a real application, use a database)
API_KEYS = {}

# Load API keys from configuration if available
def load_api_keys():
    """Load API keys from the configuration file."""
    try:
        api_keys_file = os.environ.get('CHARON_API_KEYS_FILE', '/etc/charon/api_keys.json')
        if os.path.exists(api_keys_file):
            with open(api_keys_file, 'r') as f:
                keys_data = json.load(f)
                for key_id, data in keys_data.items():
                    API_KEYS[key_id] = data
            logger.info(f"Loaded {len(API_KEYS)} API keys from {api_keys_file}")
        else:
            # Create a default API key if no API keys file exists
            default_key = hashlib.sha256(os.urandom(32)).hexdigest()
            API_KEYS['default'] = {
                'key': default_key,
                'role': 'admin',
                'name': 'Default API Key'
            }
            logger.warning(f"No API keys file found, created default API key: {default_key}")
            
            # Save the default key to file
            os.makedirs(os.path.dirname(api_keys_file), exist_ok=True)
            with open(api_keys_file, 'w') as f:
                json.dump(API_KEYS, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to load API keys: {e}")

# Authentication decorator
def require_api_key(f):
    """Decorator to require API key for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
            
        # Check if API key is valid
        for key_id, data in API_KEYS.items():
            if data['key'] == api_key:
                g.api_key_id = key_id
                g.api_key_role = data['role']
                return f(*args, **kwargs)
                
        return jsonify({'error': 'Invalid API key'}), 401
    return decorated_function

# JWT token generation and verification
def generate_token(key_id: str, expires_in: int = 3600) -> str:
    """Generate a JWT token for API access.
    
    Args:
        key_id: API key ID
        expires_in: Expiration time in seconds
        
    Returns:
        JWT token string
    """
    payload = {
        'sub': key_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + expires_in
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        API key ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.PyJWTError:
        return None

# Token-based authentication decorator
def require_auth_token(f):
    """Decorator to require JWT token for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication token required'}), 401
            
        token = auth_header.split(' ')[1]
        key_id = verify_token(token)
        
        if not key_id or key_id not in API_KEYS:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        g.api_key_id = key_id
        g.api_key_role = API_KEYS[key_id]['role']
        return f(*args, **kwargs)
    return decorated_function

# Admin role decorator
def require_admin(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'api_key_role') or g.api_key_role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Initialize firewall components
def init_firewall():
    """Initialize firewall components for API use."""
    if not hasattr(g, 'firewall_components'):
        # Initialize database
        db = Database()
        db.connect()
        
        # Initialize packet filter
        packet_filter = PacketFilter()
        
        # Initialize content filter
        content_filter = ContentFilter()
        
        # Initialize QoS
        qos = QoS()
        
        # Initialize scheduler
        scheduler = FirewallScheduler(db=db)
        
        # Initialize plugin manager
        plugin_manager = PluginManager()
        
        g.firewall_components = {
            'db': db,
            'packet_filter': packet_filter,
            'content_filter': content_filter,
            'qos': qos,
            'scheduler': scheduler,
            'plugin_manager': plugin_manager
        }
        
    return g.firewall_components

# API routes
@app.route('/api/v1/auth/token', methods=['POST'])
@require_api_key
def get_token():
    """Get a JWT token for API access."""
    expires_in = request.json.get('expires_in', 3600)  # Default to 1 hour
    token = generate_token(g.api_key_id, expires_in)
    
    return jsonify({
        'token': token,
        'expires_in': expires_in,
        'token_type': 'Bearer'
    })

@app.route('/api/v1/status', methods=['GET'])
@require_auth_token
def get_status():
    """Get the current firewall status."""
    try:
        # Initialize firewall components
        components = init_firewall()
        packet_filter = components['packet_filter']
        
        # Get status from packet filter
        status = packet_filter.get_status()
        
        return jsonify({
            'status': 'active' if status else 'inactive',
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error getting firewall status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules', methods=['GET'])
@require_auth_token
def get_rules():
    """Get the list of firewall rules."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        
        # Get rules from database
        filter_criteria = {}
        if request.args.get('chain'):
            filter_criteria['chain'] = request.args.get('chain')
        if request.args.get('action'):
            filter_criteria['action'] = request.args.get('action')
        if request.args.get('enabled') in ['true', 'false']:
            filter_criteria['enabled'] = request.args.get('enabled') == 'true'
            
        rules = db.get_rules(filter_criteria)
        
        return jsonify({'rules': rules})
    except Exception as e:
        logger.error(f"Error getting firewall rules: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules', methods=['POST'])
@require_auth_token
def add_rule():
    """Add a new firewall rule."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        packet_filter = components['packet_filter']
        
        # Get rule data from request
        rule_data = request.json
        
        # Validate rule data
        required_fields = ['chain', 'action']
        for field in required_fields:
            if field not in rule_data:
                return jsonify({'error': f"Missing required field: {field}"}), 400
                
        # Add rule to database
        rule_id = db.add_rule(rule_data)
        
        if not rule_id:
            return jsonify({'error': "Failed to add rule to database"}), 500
            
        # Apply rule to firewall
        chain = rule_data.get('chain')
        action = rule_data.get('action')
        protocol = rule_data.get('protocol')
        src_ip = rule_data.get('src_ip')
        dst_ip = rule_data.get('dst_ip')
        src_port = rule_data.get('src_port')
        dst_port = rule_data.get('dst_port')
        
        packet_filter.add_rule(
            chain=chain,
            action=action,
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port
        )
        
        return jsonify({'success': True, 'id': rule_id})
    except Exception as e:
        logger.error(f"Error adding firewall rule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<int:rule_id>', methods=['GET'])
@require_auth_token
def get_rule(rule_id):
    """Get a specific firewall rule."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        
        # Get rule from database
        rules = db.get_rules({'id': rule_id})
        
        if not rules:
            return jsonify({'error': f"Rule not found: {rule_id}"}), 404
            
        return jsonify({'rule': rules[0]})
    except Exception as e:
        logger.error(f"Error getting firewall rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<int:rule_id>', methods=['PUT'])
@require_auth_token
def update_rule(rule_id):
    """Update a firewall rule."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        packet_filter = components['packet_filter']
        
        # Get rule data from request
        rule_data = request.json
        
        # Update rule in database
        success = db.update_rule(rule_id, rule_data)
        
        if not success:
            return jsonify({'error': f"Rule not found: {rule_id}"}), 404
            
        # In a real application, you would update the rule in the firewall
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating firewall rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rules/<int:rule_id>', methods=['DELETE'])
@require_auth_token
def delete_rule(rule_id):
    """Delete a firewall rule."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        packet_filter = components['packet_filter']
        
        # Get the rule before deleting it
        rules = db.get_rules({'id': rule_id})
        
        if not rules:
            return jsonify({'error': f"Rule not found: {rule_id}"}), 404
            
        # Delete rule from database
        success = db.delete_rule(rule_id)
        
        if not success:
            return jsonify({'error': f"Failed to delete rule: {rule_id}"}), 500
            
        # In a real application, you would delete the rule from the firewall
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting firewall rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/logs', methods=['GET'])
@require_auth_token
def get_logs():
    """Get firewall logs."""
    try:
        # Initialize firewall components
        components = init_firewall()
        db = components['db']
        
        # Get logs from database
        limit = int(request.args.get('limit', 100))
        
        filter_criteria = {}
        if request.args.get('action'):
            filter_criteria['action'] = request.args.get('action')
        if request.args.get('src_ip'):
            filter_criteria['src_ip'] = request.args.get('src_ip')
        if request.args.get('dst_ip'):
            filter_criteria['dst_ip'] = request.args.get('dst_ip')
            
        logs = db.get_logs(limit, filter_criteria)
        
        return jsonify({'logs': logs})
    except Exception as e:
        logger.error(f"Error getting firewall logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/content-filter/categories', methods=['GET'])
@require_auth_token
def get_categories():
    """Get content filter categories."""
    try:
        # Initialize firewall components
        components = init_firewall()
        content_filter = components['content_filter']
        
        # Get categories from content filter
        categories = content_filter.get_categories()
        
        return jsonify({'categories': categories})
    except Exception as e:
        logger.error(f"Error getting content filter categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/content-filter/domains', methods=['GET'])
@require_auth_token
def get_domains():
    """Get domains in a content filter category."""
    try:
        # Initialize firewall components
        components = init_firewall()
        content_filter = components['content_filter']
        
        # Get category from query parameters
        category = request.args.get('category')
        
        if not category:
            return jsonify({'error': "Missing required parameter: category"}), 400
            
        # Get domains from content filter
        domains = content_filter.get_domains_by_category(category)
        
        return jsonify({'domains': domains})
    except Exception as e:
        logger.error(f"Error getting domains for category {category}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/content-filter/domains', methods=['POST'])
@require_auth_token
def add_domain():
    """Add a domain to the content filter."""
    try:
        # Initialize firewall components
        components = init_firewall()
        content_filter = components['content_filter']
        
        # Get domain data from request
        data = request.json
        
        if 'domain' not in data:
            return jsonify({'error': "Missing required field: domain"}), 400
            
        domain = data['domain']
        category = data.get('category', 'uncategorized')
        
        # Add domain to content filter
        success = content_filter.add_domain(domain, category)
        
        if not success:
            return jsonify({'error': f"Failed to add domain: {domain}"}), 500
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error adding domain: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/content-filter/apply', methods=['POST'])
@require_auth_token
@require_admin
def apply_content_filter():
    """Apply the content filter to the firewall."""
    try:
        # Initialize firewall components
        components = init_firewall()
        content_filter = components['content_filter']
        
        # Apply content filter to firewall
        success = content_filter.apply_to_firewall()
        
        if not success:
            return jsonify({'error': "Failed to apply content filter to firewall"}), 500
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error applying content filter: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/qos/profiles', methods=['GET'])
@require_auth_token
def get_qos_profiles():
    """Get available QoS profiles."""
    # This is a placeholder - in a real application, you would retrieve QoS profiles
    return jsonify({
        'profiles': [
            {'id': 'default', 'name': 'Default Profile'},
            {'id': 'gaming', 'name': 'Gaming Profile'},
            {'id': 'streaming', 'name': 'Streaming Profile'}
        ]
    })

@app.route('/api/v1/qos/setup', methods=['POST'])
@require_auth_token
@require_admin
def setup_qos():
    """Set up QoS on the firewall."""
    try:
        # Initialize firewall components
        components = init_firewall()
        qos = components['qos']
        
        # Get profile from request
        data = request.json
        profile = data.get('profile', 'default')
        
        # Apply QoS profile
        if profile == 'default':
            success = qos.setup_default_profile()
        else:
            # In a real application, you would implement other profiles
            return jsonify({'error': f"Unknown profile: {profile}"}), 400
        
        if not success:
            return jsonify({'error': f"Failed to apply QoS profile: {profile}"}), 500
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting up QoS: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/plugins', methods=['GET'])
@require_auth_token
def get_plugins():
    """Get available plugins."""
    try:
        # Initialize firewall components
        components = init_firewall()
        plugin_manager = components['plugin_manager']
        
        # Get plugins from plugin manager
        plugins = plugin_manager.get_all_plugins()
        
        return jsonify({'plugins': plugins})
    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/plugins/<string:plugin_name>/enable', methods=['POST'])
@require_auth_token
@require_admin
def enable_plugin(plugin_name):
    """Enable a plugin."""
    try:
        # Initialize firewall components
        components = init_firewall()
        plugin_manager = components['plugin_manager']
        
        # Enable the plugin
        success = plugin_manager.enable_plugin(plugin_name)
        
        if not success:
            return jsonify({'error': f"Failed to enable plugin: {plugin_name}"}), 500
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error enabling plugin {plugin_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/plugins/<string:plugin_name>/disable', methods=['POST'])
@require_auth_token
@require_admin
def disable_plugin(plugin_name):
    """Disable a plugin."""
    try:
        # Initialize firewall components
        components = init_firewall()
        plugin_manager = components['plugin_manager']
        
        # Disable the plugin
        success = plugin_manager.disable_plugin(plugin_name)
        
        if not success:
            return jsonify({'error': f"Failed to disable plugin: {plugin_name}"}), 500
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error disabling plugin {plugin_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/scheduler/tasks', methods=['GET'])
@require_auth_token
def get_scheduled_tasks():
    """Get scheduled tasks."""
    try:
        # Initialize firewall components
        components = init_firewall()
        scheduler = components['scheduler']
        
        # Get scheduled tasks
        tasks = scheduler.list_scheduled_rules()
        
        return jsonify({'tasks': tasks})
    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        return jsonify({'error': str(e)}), 500

def run_api(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the API server.
    
    Args:
        host: Hostname to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    load_api_keys()
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the API server
    run_api(debug=True) 