# Plugin System Documentation

## Overview

The Charon firewall's plugin system allows users to extend the core functionality with custom features. Plugins are modular components that can be enabled, disabled, and configured independently.

## Plugin Architecture

The plugin system consists of the following components:

1. **Plugin Base**: An abstract base class that all plugins must inherit from
2. **Plugin Manager**: A class that handles plugin discovery, loading, and lifecycle management
3. **Available Plugins**: A directory containing all available plugins

## Creating a Plugin

To create a plugin, you need to:

1. Create a new Python file in the `charon/src/plugins/available` directory
2. Define a class that inherits from `PluginBase`
3. Implement the required methods

Here's a simple example plugin:

```python
from ..plugin_base import PluginBase

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__(
            name="My Plugin",
            description="This is my custom plugin",
            enabled=False
        )
    
    def initialize(self) -> bool:
        # Code to initialize the plugin
        return True
    
    def cleanup(self) -> bool:
        # Code to clean up resources
        return True
```

## Plugin Lifecycle

Plugins go through the following lifecycle stages:

1. **Discovery**: The plugin manager finds available plugins in the plugin directory
2. **Loading**: The plugin class is loaded from its module
3. **Instantiation**: An instance of the plugin class is created
4. **Configuration**: The plugin is configured with user-provided settings
5. **Initialization**: The plugin is initialized when enabled
6. **Cleanup**: Resources are released when the plugin is disabled

## Using the Plugin Manager

The `PluginManager` class provides methods to interact with plugins:

```python
from charon.src.plugins import PluginManager

# Create a plugin manager
manager = PluginManager()

# Discover available plugins
plugins = manager.discover_plugins()
print(f"Found plugins: {plugins}")

# Enable a plugin
manager.enable_plugin("hello_world")

# Configure a plugin
manager.instantiate_plugin("hello_world", {"option": "value"})

# Disable a plugin
manager.disable_plugin("hello_world")

# Get information about all plugins
all_plugins = manager.get_all_plugins()
for name, info in all_plugins.items():
    print(f"{name}: {info['description']} (Enabled: {info['enabled']})")
```

## Hello World Example

The Charon firewall comes with a simple "Hello World" plugin that demonstrates the plugin system. This plugin logs messages when enabled and disabled, and creates a marker file to demonstrate its functionality.

To use the Hello World plugin:

```python
from charon.src.plugins import PluginManager

manager = PluginManager()
manager.enable_plugin("hello_world")
# Use the plugin...
manager.disable_plugin("hello_world")
```

## Adding Your Own Plugins

To add your own plugin:

1. Create a new Python file in the `charon/src/plugins/available` directory
2. Define a class that inherits from `PluginBase`
3. Implement the required methods (`initialize`, `cleanup`)
4. Optionally override the `configure` method if your plugin has configuration options

Your plugin will be automatically discovered by the plugin manager and can be enabled through the API or UI. 