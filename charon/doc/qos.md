# Quality of Service (QoS) Documentation

## Overview

The Quality of Service (QoS) module in Charon allows for traffic shaping and bandwidth management. It provides a way to prioritize certain types of traffic and allocate bandwidth based on traffic classes.

## Key Features

- Traffic classification based on protocol, IP addresses, and ports
- Bandwidth allocation and limits for different traffic types
- Priority queuing for time-sensitive applications
- Predefined QoS profiles for common use cases

## Basic Concepts

### Traffic Classes

Traffic classes are used to organize network traffic and apply specific bandwidth rules. Each class can have:

- A guaranteed bandwidth rate
- A ceiling (maximum) bandwidth rate
- A priority level

### Filters

Filters are used to classify traffic into the appropriate traffic classes. Filters can match on:

- IP protocol (TCP, UDP)
- Source and destination IP addresses
- Source and destination ports

## Usage

### Basic Setup

```python
from charon.src.core.qos import QoS

# Initialize QoS with interface and total bandwidth
qos = QoS(interface="eth0", total_bandwidth=100)  # 100 Mbps

# Set up the basic queueing discipline
qos.setup_tc_qdisc()
```

### Creating Traffic Classes

```python
# Add a high-priority class with 20 Mbps guaranteed bandwidth
# and ability to use up to 50 Mbps when available
qos.add_traffic_class(
    class_id=10,
    rate=20000,     # 20 Mbps in Kbps
    ceiling=50000,  # 50 Mbps in Kbps
    priority=0      # Highest priority
)

# Add a low-priority class with 10 Mbps guaranteed bandwidth
qos.add_traffic_class(
    class_id=20,
    rate=10000,     # 10 Mbps in Kbps
    ceiling=30000,  # 30 Mbps in Kbps
    priority=3      # Lower priority
)
```

### Adding Filters

```python
# Classify SSH traffic (TCP port 22) as high priority
qos.add_filter(
    class_id=10,
    protocol="tcp",
    dst_port=22
)

# Classify video streaming traffic to a specific server as medium priority
qos.add_filter(
    class_id=20,
    protocol="tcp",
    dst_ip="192.168.1.100",
    dst_port=8080
)
```

### Using Predefined Profiles

For quick setup, you can use the default profile:

```python
qos.setup_default_profile()
```

This will create a basic QoS setup with:
- High-priority class (20% of bandwidth) for VoIP and SSH
- Medium-priority class (30% of bandwidth) for web browsing
- Low-priority class (10% of bandwidth) for P2P and downloads
- Default class (40% of bandwidth) for all other traffic

## Customization

You can create your own QoS profiles by combining traffic classes and filters based on your specific requirements.

## Requirements

- Linux system with `tc` (traffic control) utility installed
- Root privileges
- Knowledge of your network's bandwidth and traffic patterns

## Examples

### Setting Up QoS for a Home Network

```python
from charon.src.core.qos import QoS

# Initialize QoS for a 100 Mbps connection
qos = QoS(interface="eth0", total_bandwidth=100)

# Set up basic QoS with predefined profiles
qos.setup_default_profile()

# Add a custom filter for gaming traffic
qos.add_filter(10, protocol="udp", dst_port=3074)  # Xbox Live
```

### Limiting Bandwidth for Specific Hosts

```python
from charon.src.core.qos import QoS

# Initialize QoS
qos = QoS(interface="eth0", total_bandwidth=100)
qos.setup_tc_qdisc()

# Create a limited bandwidth class
qos.add_traffic_class(50, rate=2000, ceiling=2000, priority=5)  # 2 Mbps max

# Apply to a specific host
qos.add_filter(50, src_ip="192.168.1.50")
``` 