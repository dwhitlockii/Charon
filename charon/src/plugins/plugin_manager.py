#!/usr/bin/env python3
"""
Plugin Manager for Charon Firewall

This module provides functionality to discover, load, and manage plugins.
"""

import os
import importlib
import inspect
import logging
import sys
from typing import Dict, List, Type, Any, Optional

from .plugin_base import PluginBase

logger = logging.getLogger('charon.plugins.manager')

class PluginManager:
    """Manager for handling plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugin_dirs: List[str] = None):
        """Initialize the plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        if plugin_dirs is None:
            # Default to the plugins directory
            self.plugin_dirs = [os.path.join(os.path.dirname(__file__), 'available')]
        else:
            self.plugin_dirs = plugin_dirs
            
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}
    
    def discover_plugins(self) -> List[str]:
        """Search plugin directories and discover available plugins.
        
        Returns:
            List of plugin module names found
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
                
            # Find all Python files in the plugin directory
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and not filename.startswith('_'):
                    plugin_name = filename[:-3]  # Remove .py extension
                    discovered_plugins.append(plugin_name)
                    logger.info(f"Discovered plugin: {plugin_name}")
        
        return discovered_plugins
    
    def load_plugin_class(self, plugin_name: str) -> Optional[Type[PluginBase]]:
        """Load a plugin class from its module name.
        
        Args:
            plugin_name: Name of the plugin module to load
            
        Returns:
            The plugin class or None if loading failed
        """
        try:
            # Construct the module path
            for plugin_dir in self.plugin_dirs:
                module_path = os.path.join(plugin_dir, f"{plugin_name}.py")
                if os.path.exists(module_path):
                    # Add the plugin directory to the path if needed
                    if plugin_dir not in sys.path:
                        sys.path.append(plugin_dir)
                    
                    # Import the module
                    module = importlib.import_module(f"available.{plugin_name}")
                    
                    # Find the plugin class in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, PluginBase) and 
                            obj != PluginBase):
                            self.plugin_classes[plugin_name] = obj
                            logger.info(f"Loaded plugin class: {obj.__name__}")
                            return obj
            
            logger.error(f"No plugin class found in module: {plugin_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return None
            
    def instantiate_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> Optional[PluginBase]:
        """Instantiate a plugin and configure it.
        
        Args:
            plugin_name: Name of the plugin to instantiate
            config: Configuration for the plugin
            
        Returns:
            Plugin instance or None if instantiation failed
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} is already instantiated")
            return self.plugins[plugin_name]
            
        # Load the plugin class if not already loaded
        if plugin_name not in self.plugin_classes:
            plugin_class = self.load_plugin_class(plugin_name)
            if plugin_class is None:
                return None
        else:
            plugin_class = self.plugin_classes[plugin_name]
            
        try:
            # Instantiate the plugin
            plugin = plugin_class()
            
            # Configure the plugin if configuration is provided
            if config:
                plugin.configure(config)
                
            # Store the plugin instance
            self.plugins[plugin_name] = plugin
            
            logger.info(f"Instantiated plugin: {plugin_name}")
            return plugin
        except Exception as e:
            logger.error(f"Failed to instantiate plugin {plugin_name}: {e}")
            return None
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin by initializing it.
        
        Args:
            plugin_name: Name of the plugin to enable
            
        Returns:
            True if the plugin was successfully enabled, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} is not instantiated, attempting to instantiate")
            plugin = self.instantiate_plugin(plugin_name)
            if plugin is None:
                return False
        else:
            plugin = self.plugins[plugin_name]
        
        if plugin.enabled:
            logger.info(f"Plugin {plugin_name} is already enabled")
            return True
            
        if plugin.initialize():
            plugin.enabled = True
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        else:
            logger.error(f"Failed to initialize plugin: {plugin_name}")
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin by cleaning it up.
        
        Args:
            plugin_name: Name of the plugin to disable
            
        Returns:
            True if the plugin was successfully disabled, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} is not instantiated")
            return False
            
        plugin = self.plugins[plugin_name]
        
        if not plugin.enabled:
            logger.info(f"Plugin {plugin_name} is already disabled")
            return True
            
        if plugin.cleanup():
            plugin.enabled = False
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        else:
            logger.error(f"Failed to clean up plugin: {plugin_name}")
            return False
    
    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all discovered plugins.
        
        Returns:
            Dictionary mapping plugin names to their information
        """
        # First discover all available plugins
        discovered = self.discover_plugins()
        
        # Build information about each plugin
        result = {}
        for plugin_name in discovered:
            if plugin_name in self.plugins:
                # Plugin is already instantiated
                plugin = self.plugins[plugin_name]
                result[plugin_name] = {
                    "name": plugin.name,
                    "description": plugin.description,
                    "enabled": plugin.enabled,
                    "loaded": True
                }
            else:
                # Plugin is available but not loaded
                result[plugin_name] = {
                    "name": plugin_name,
                    "description": "",
                    "enabled": False,
                    "loaded": False
                }
                
        return result 