"""
Plugins package for Charon firewall.

This package provides the plugin system for extending firewall functionality.
"""

from .plugin_base import PluginBase
from .plugin_manager import PluginManager

__all__ = ['PluginBase', 'PluginManager'] 