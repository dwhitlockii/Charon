#!/usr/bin/env python3
"""
Plugin Base Module for Charon Firewall

This module defines the base class for all plugins in the Charon firewall system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger('charon.plugins')

class PluginBase(ABC):
    """Abstract base class for all Charon firewall plugins."""
    
    def __init__(self, name: str, description: str = "", enabled: bool = True):
        """Initialize a plugin with basic information.
        
        Args:
            name: The name of the plugin
            description: A brief description of the plugin's functionality
            enabled: Whether the plugin is enabled by default
        """
        self.name = name
        self.description = description
        self.enabled = enabled
        self.config: Dict[str, Any] = {}
        logger.info(f"Initializing plugin: {name}")
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Must be implemented by all plugins.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up resources when the plugin is disabled or removed.
        
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the plugin with the provided settings.
        
        Args:
            config: A dictionary of configuration settings
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        self.config.update(config)
        logger.info(f"Plugin {self.name} configured with: {config}")
        return True 