"""
Web UI package for Charon firewall.

This package provides a web-based interface for managing the firewall.
"""

from .server import app

try:
    from .firewall_service import FirewallService
    __all__ = ['app', 'FirewallService']
except ImportError:
    __all__ = ['app'] 