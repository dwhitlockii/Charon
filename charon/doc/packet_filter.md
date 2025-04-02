# Packet Filter Module Documentation

## Overview

The Packet Filter module is the core component of Charon's firewall functionality. It provides a Python interface to interact with nftables, which is a powerful packet filtering framework in the Linux kernel.

## Key Features

- Create and manage nftables tables and chains
- Add, delete, and list firewall rules
- Check for appropriate permissions
- Provides logging for all operations

## Usage

### Basic Setup

```python
from charon.src.core.packet_filter import PacketFilter

# Initialize the packet filter
pf = PacketFilter()  # Default table name is "charon"

# Create the base table and chains
if pf.setup_base_table():
    print("Base table and chains created successfully")
else:
    print("Failed to create base table and chains")
```

### Managing Rules

The module provides methods to add, delete, and list rules:

```python
# Add a rule to allow SSH traffic
pf.add_rule("input", "tcp dport 22 accept")

# List all rules
rules_json = pf.list_rules()
if rules_json:
    print(rules_json)

# Delete a rule with handle 4 from the input chain
pf.delete_rule("input", 4)
```

## Requirements

- Linux system with nftables installed
- Root privileges (or sudo) to modify firewall rules

## Implementation Details

The Packet Filter module uses the Python subprocess module to execute nftables commands. It provides methods that wrap these commands in an easy-to-use API.

The nftables commands are executed with the `--json` option when appropriate to provide structured output.

## Error Handling

The module logs all operations and errors using Python's logging module. Each method returns a boolean value indicating success or failure, making it easy to check the result of operations. 