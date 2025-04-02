# Cross-Platform Compatibility in Charon Firewall

This document provides an overview of the cross-platform approach and implementation details for the Charon Firewall project, with a focus on recent improvements to the content filtering module and the Quality of Service (QoS) module.

## Overview

Charon Firewall is designed to work seamlessly across multiple operating systems, with primary support for Linux and Windows. The system detects the underlying platform and adapts its behavior accordingly, using platform-specific implementations for core functionality while maintaining a consistent API.

## Cross-Platform Modules

### Content Filter Cross-Platform Implementation

The content filter module has been implemented with cross-platform compatibility in mind:

- Platform detection using `platform.system()`
- Platform-specific database paths:
  - Linux: `/etc/charon/content_filter.db`
  - Windows: `%LOCALAPPDATA%\Charon\content_filter.db`
- Adaptive permission checking based on the operating system
- Integration with the respective firewall technologies on each platform
- Improved error handling and connection management

### QoS Module Cross-Platform Implementation

The Quality of Service (QoS) module now supports both Linux and Windows platforms:

- Platform-specific implementations for traffic shaping:
  - Linux: Uses the Traffic Control (`tc`) subsystem with Hierarchical Token Bucket (HTB) queuing discipline
  - Windows: Uses PowerShell Network QoS Policies with DSCP traffic marking
- Automatic network interface detection for both platforms
- Windows-specific QoS policy management
- Platform-specific permission checks
- Consistent API across platforms with feature detection
- Status reporting and monitoring on both platforms

## Key Improvements

### Platform Detection

```python
import platform

platform_name = platform.system()  # Returns 'Linux', 'Windows', etc.
```

### Platform-Specific File Paths

```python
if platform.system() == 'Windows':
    db_path = os.path.join(os.environ.get('LOCALAPPDATA'), 'Charon', 'content_filter.db')
else:
    db_path = '/etc/charon/content_filter.db'
```

### Permission Handling

```python
def _check_permissions(self):
    try:
        if platform.system() == 'Windows':
            # Check if running as Administrator on Windows
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                logger.warning("Not running as Administrator. Operations may fail.")
        else:
            # Check if running as root on Linux/Unix
            if os.geteuid() != 0:
                logger.warning("Not running as root. Operations may fail.")
    except Exception as e:
        logger.warning(f"Could not check permissions: {e}")
```

### Firewall Integration

#### Linux Firewall Integration

For Linux, the QoS module integrates with the `tc` command for traffic shaping:

```python
def setup_tc_qdisc(self):
    """Set up the traffic control queuing discipline (Linux only)."""
    if self.platform == 'Windows':
        logger.warning("setup_tc_qdisc is not supported on Windows")
        return False
        
    # Linux-specific implementation using the tc command
    cmd = ["tc", "qdisc", "add", "dev", self.interface, 
           "root", "handle", "1:", "htb", "default", "30"]
    subprocess.run(cmd, check=True, capture_output=True)
    # ...
```

#### Windows Firewall Integration

For Windows, the QoS module uses PowerShell commands to set up Network QoS Policies:

```python
def _apply_windows_qos(self):
    """Apply QoS settings on Windows using PowerShell."""
    # Create a temporary PowerShell script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as script_file:
        script_path = script_file.name
        
        # Write PowerShell script content
        script_file.write("""
        # Remove existing Charon QoS policies
        Get-NetQosPolicy | Where-Object { $_.Name -like "Charon*" } | Remove-NetQosPolicy -Confirm:$false
        
        # Create QoS policies for different traffic classes
        New-NetQosPolicy -Name "Charon-High-SSH" -IPProtocol TCP -IPDstPort 22 -DSCPAction 46 -NetworkProfile All
        # ...
        """)
    
    # Execute the PowerShell script
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
```

## Testing Cross-Platform Functionality

### Platform-Specific Test Cases

The test suite includes platform-specific tests that ensure functionality on each supported platform:

```python
def test_apply_qos_linux(self):
    """Test apply_qos on Linux."""
    self.mock_platform.return_value = 'Linux'
    # ...

def test_apply_qos_windows(self):
    """Test apply_qos on Windows."""
    self.mock_platform.return_value = 'Windows'
    # ...
```

### Mocking for Platform Independence

Using `unittest.mock` to simulate different platforms during testing:

```python
# Mock platform detection
self.platform_patcher = mock.patch('platform.system')
self.mock_platform = self.platform_patcher.start()
self.mock_platform.return_value = 'Windows'  # or 'Linux' for specific tests
```

### Parameterized Tests

Using `pytest.mark.parametrize` for testing across platforms with the same test code:

```python
@pytest.mark.parametrize("platform_name", ["Windows", "Linux"])
def test_get_status(self, platform_name):
    # Test status reporting on different platforms
    # ...
```

### Conditional Test Skipping

Skip tests that don't apply to certain platforms:

```python
@pytest.mark.skipif(platform.system() == 'Windows', reason="Test only applies to Linux")
def test_linux_specific_feature(self):
    # ...
```

## Documentation Updates

The following documentation has been updated to reflect cross-platform capabilities:

1. **Technical Documentation**: Updated with platform support information
2. **Content Filter Documentation**: Details for Windows and Linux implementations
3. **QoS Module Documentation**: Platform-specific implementation details
4. **Project Milestones**: Updated to reflect cross-platform progress
5. **Installation Instructions**: Platform-specific setup steps
6. **Configuration Guides**: Separate sections for Linux and Windows

## Future Cross-Platform Work

The following areas still need cross-platform improvements:

1. **Plugin System**: Ensure plugin compatibility across platforms
2. **Installation Process**: Native installers for Windows (.msi) and Linux (.deb, .rpm)
3. **System Integration**: Boot-time startup and system services
4. **Advanced Packet Filtering**: Unified API for packet handling

## Benefits of Cross-Platform Support

1. **Broader User Base**: Making Charon accessible to users of both Windows and Linux
2. **Testing Environment Flexibility**: Developers can contribute from their preferred OS
3. **Enterprise Adoption**: Organizations with mixed environments can deploy consistently
4. **Educational Value**: Students can learn firewall concepts on their existing systems
5. **Feature Parity**: Users get the same protection regardless of platform

## Implementation Principles

When implementing cross-platform features, we follow these principles:

1. **Single Codebase**: Maintain one codebase with conditional paths rather than separate implementations
2. **Consistent API**: Public interfaces remain the same across platforms
3. **Graceful Degradation**: Features not available on a platform degrade gracefully
4. **Explicit Platform Detection**: Always use explicit platform detection rather than trying to infer from behavior
5. **Comprehensive Testing**: Test all code paths on all supported platforms
6. **Clear Documentation**: Document platform-specific behavior and limitations 