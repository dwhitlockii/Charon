#!/usr/bin/env python3
"""
Hello World Plugin for Charon Firewall

This is a simple example plugin that demonstrates the plugin system.
"""

import logging
from ..plugin_base import PluginBase

logger = logging.getLogger('charon.plugins.hello_world')

class HelloWorldPlugin(PluginBase):
    """A simple example plugin that logs hello world messages."""
    
    def __init__(self):
        """Initialize the Hello World plugin."""
        super().__init__(
            name="Hello World",
            description="A simple example plugin that demonstrates the plugin system",
            enabled=False
        )
    
    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        logger.info("Hello, World! Plugin initialized.")
        
        # Add a simple rule to demonstrate the plugin
        rule_message = "# Hello World Plugin was here"
        try:
            with open("/etc/charon/hello_world.txt", "w") as f:
                f.write(rule_message)
            logger.info("Created hello world marker file")
            return True
        except Exception as e:
            logger.error(f"Failed to create hello world marker file: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up resources when the plugin is disabled.
        
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        logger.info("Goodbye, World! Plugin cleaned up.")
        
        # Remove the rule that was added during initialization
        try:
            import os
            if os.path.exists("/etc/charon/hello_world.txt"):
                os.remove("/etc/charon/hello_world.txt")
            logger.info("Removed hello world marker file")
            return True
        except Exception as e:
            logger.error(f"Failed to remove hello world marker file: {e}")
            return False 