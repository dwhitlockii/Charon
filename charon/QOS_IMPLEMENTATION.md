# QoS Module Implementation

This document provides technical details about the Quality of Service (QoS) module implementation in the Charon Firewall project, with a focus on cross-platform support.

## Overview

The QoS module enables traffic shaping and prioritization capabilities in Charon, allowing administrators to:

1. Set up traffic classes with guaranteed bandwidth
2. Apply priority levels to different types of traffic
3. Filter network traffic based on protocol, IP, and port
4. Monitor QoS status and performance

## Cross-Platform Architecture

The QoS module is designed to work on both Linux and Windows environments through platform-specific implementations and a consistent API.

### Platform Detection

The module automatically detects the underlying platform using Python's `platform.system()`:

```python
import platform

class QoS:
    def __init__(self, interface: Optional[str] = None, total_bandwidth: int = 1000):
        # ...
        self.platform = platform.system()
        # ...
```

### Platform-Specific Implementations

#### Linux Implementation

On Linux systems, the QoS module uses the Traffic Control (`tc`) subsystem with the Hierarchical Token Bucket (HTB) queuing discipline:

```python
def setup_tc_qdisc(self) -> bool:
    """Set up the traffic control queuing discipline (Linux only)."""
    if self.platform == 'Windows':
        logger.warning("setup_tc_qdisc is not supported on Windows")
        return False
        
    # Linux-specific implementation
    cmd = ["tc", "qdisc", "add", "dev", self.interface, 
           "root", "handle", "1:", "htb", "default", "30"]
    subprocess.run(cmd, check=True, capture_output=True)
    # ...
```

#### Windows Implementation

On Windows systems, the QoS module uses PowerShell commands to manage Network QoS Policies:

```python
def _apply_windows_qos(self) -> bool:
    """Apply QoS settings on Windows using PowerShell."""
    # Create temporary PowerShell script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as script_file:
        script_file.write("""
        # Remove existing Charon QoS policies
        Get-NetQosPolicy | Where-Object { $_.Name -like "Charon*" } | Remove-NetQosPolicy -Confirm:$false
        
        # Create QoS policies for different traffic classes
        New-NetQosPolicy -Name "Charon-High-SSH" -IPProtocol TCP -IPDstPort 22 -DSCPAction 46 -NetworkProfile All
        # ...
        """)
    
    # Execute PowerShell script
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    # ...
```

### Consistent API

Despite the different underlying implementations, the module provides a consistent API for both platforms:

```python
# Common API that works on both platforms
qos = QoS()
qos.apply_qos()       # Automatically selects platform-specific implementation
qos.get_status()      # Works on both platforms
qos.remove_all_policies()  # Works on both platforms
```

## Key Features

### Auto-Detection of Network Interfaces

The module can automatically detect the default network interface on both platforms:

```python
def _detect_default_interface(self) -> str:
    """Detect the default network interface."""
    if self.platform == 'Windows':
        # Windows implementation using PowerShell
        cmd = ["powershell", "-Command", 
               "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 -ExpandProperty Name"]
    else:
        # Linux implementation
        cmd = ["ip", "route", "get", "8.8.8.8"]
    # ...
```

### Permission Checking

The module includes platform-specific permission checks:

```python
def _check_permissions(self) -> None:
    """Check if the current user has permissions to modify QoS settings."""
    try:
        if self.platform == 'Windows':
            # Check if running as Administrator on Windows
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                logger.warning("Not running as Administrator. QoS operations on Windows may fail.")
        else:
            # Check if running as root on Linux/Unix
            if os.geteuid() != 0:
                logger.warning("Not running as root. QoS operations may fail.")
    except Exception as e:
        logger.warning(f"Could not check permissions: {e}")
```

### Traffic Classes and Policies

Both platforms implement the concept of traffic classes, though with different mechanisms:

- **Linux**: Uses HTB classes with guaranteed and ceiling bandwidth rates
- **Windows**: Uses DSCP (Differentiated Services Code Point) markings to prioritize traffic

### Traffic Filtering

Traffic can be filtered and assigned to appropriate classes based on various criteria:

- **Linux**: Uses `tc filter` with match conditions
- **Windows**: Uses IP protocol and port matching in QoS policies

### Status Reporting

The module provides a unified status reporting interface that works on both platforms:

```python
def get_status(self) -> Dict[str, Any]:
    """Get the current status of QoS settings."""
    status = {
        "platform": self.platform,
        "interface": self.interface,
        "total_bandwidth": self.total_bandwidth,
        "enabled": False,
        "policies": [],
        "error": None
    }
    
    if self.platform == 'Windows':
        # Windows-specific status retrieval
        # ...
    else:
        # Linux-specific status retrieval
        # ...
        
    return status
```

## Platform-Specific Limitations

### Linux-Specific Features

The following features are only available on Linux:

- Fine-grained control over bandwidth guarantees and ceilings
- Advanced traffic class hierarchies
- Detailed traffic statistics
- Complex filtering rules with multiple conditions

### Windows-Specific Features

The following features are only available on Windows:

- Network profile selection (All, Public, Private, Domain)
- Integration with Windows Group Policy
- PowerShell-based management

## Graceful Degradation

The module includes checks for platform support and degrades gracefully when methods are called on unsupported platforms:

```python
def add_traffic_class(self, class_id: int, rate: int, ceiling: Optional[int] = None, 
                      parent_id: int = 1, priority: int = 0) -> bool:
    """Add a traffic class for bandwidth allocation (Linux only)."""
    if self.platform == 'Windows':
        logger.warning("add_traffic_class is not supported on Windows")
        return False
        
    # Linux implementation...
```

## Testing Strategy

The testing strategy includes:

1. **Mocking platform detection**: Tests override `platform.system()` to simulate different platforms
2. **Skip conditionals**: Platform-specific tests are skipped on inappropriate platforms
3. **Mock system commands**: `subprocess.run` calls are mocked to prevent actual system changes
4. **Consistent error handling**: Error cases are tested consistently across platforms

Example:

```python
@unittest.skipIf(platform.system() == 'Windows', "Linux-specific test")
def test_linux_specific_feature(self):
    # Test code for Linux-specific feature
```

## Integration with Web Interface

The QoS module integrates with the Charon web interface, providing:

1. Status dashboard showing current QoS configuration
2. Network bandwidth settings
3. Traffic class management
4. Traffic rule management
5. Platform-appropriate controls and feedback

## Future Improvements

Planned improvements include:

1. **Enhanced Windows Support**: More granular control options for Windows
2. **Traffic Monitoring**: Real-time traffic monitoring and graphs
3. **Application Recognition**: Automatic application recognition for traffic classification
4. **Dynamic Rate Adjustment**: Automatic adjustment based on network conditions
5. **More Platform Support**: Extend to additional platforms like macOS

## Conclusion

The QoS module provides a robust, cross-platform approach to traffic shaping and prioritization, using a consistent API while leveraging platform-specific capabilities to provide the best experience on each supported operating system. 