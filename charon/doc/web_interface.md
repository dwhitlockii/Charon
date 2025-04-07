# Charon Web Interface Documentation

## Overview

The Charon web interface provides a comprehensive management system for the firewall, offering real-time monitoring, configuration management, and security controls through an intuitive web-based dashboard.

## Features

### Dashboard

The dashboard provides a real-time overview of the system's status and performance:

1. **System Health Monitoring**
   - CPU usage with real-time updates
   - Memory utilization tracking
   - Disk space monitoring
   - Visual progress bars for resource usage
   - System uptime display
   - Last backup information

2. **Network Traffic Analysis**
   - Real-time traffic graphs
   - Incoming/outgoing bandwidth monitoring
   - Historical traffic data visualization
   - Traffic pattern analysis
   - Time range selection (1h, 6h, 24h, 7d)
   - Traffic summary statistics

3. **Security Status**
   - Active firewall rules count
   - Blocked connection attempts
   - VPN connection status
   - Security event tracking
   - Threat level indicator
   - Security alerts display

4. **Recent Events**
   - Real-time event logging
   - Event categorization (info, warning, error)
   - Timestamp tracking
   - Event filtering capabilities
   - Pagination support
   - Search functionality

5. **Network Status**
   - Interface status monitoring (WAN, LAN, DMZ)
   - IP address display for each interface
   - DNS server configuration
   - DHCP lease information
   - Network load indicators
   - Interface connection status

6. **VPN Status**
   - Active VPN connection display
   - Connection type information (IPSec, OpenVPN)
   - Connection status indicators
   - IP address and uptime tracking
   - VPN management actions
   - VPN log access

### Quick Actions

The dashboard includes quick access buttons for common tasks:
- Block IP addresses
- Allow specific ports
- Restart services
- Export logs
- Backup configuration
- Scan network for vulnerabilities
- Add VPN connections
- View VPN logs

## Technical Implementation

### Real-time Updates

The dashboard implements real-time updates through the following mechanisms:

1. **System Statistics**
   - Updates every 5 seconds
   - CPU, memory, and disk usage monitoring
   - Resource utilization alerts

2. **Network Statistics**
   - Updates every 10 seconds
   - Interface status monitoring
   - DNS and DHCP information
   - Network load indicators

3. **Security Statistics**
   - Updates every 30 seconds
   - Rule status monitoring
   - Connection tracking
   - Security event logging

4. **Event Updates**
   - Updates every minute
   - Event categorization
   - Priority-based display
   - Historical event access

5. **VPN Status**
   - Updates every 30 seconds
   - Connection status monitoring
   - Uptime tracking
   - Connection management

### API Endpoints

The dashboard utilizes the following API endpoints:

1. `/api/system/stats`
   - Returns system resource utilization
   - CPU, memory, and disk usage
   - System load information
   - Uptime and backup information

2. `/api/network/stats`
   - Network traffic statistics
   - Bandwidth utilization
   - Connection counts
   - Interface status information

3. `/api/network/interfaces`
   - Interface configuration
   - IP address information
   - Connection status
   - DNS and DHCP settings

4. `/api/security/stats`
   - Firewall rule status
   - Security event counts
   - VPN connection status
   - Threat level information

5. `/api/events/recent`
   - Recent system events
   - Security alerts
   - System notifications
   - Filtered event access

6. `/api/vpn/status`
   - VPN connection information
   - Connection type details
   - Status and uptime
   - Management actions

## User Interface Components

### Navigation

The interface includes a responsive sidebar with:
- Dashboard
- Firewall Rules
- Content Filter
- QoS Management
- VPN Configuration
- Logs
- Settings

### Theme Support

- Light/dark mode toggle
- Responsive design
- Mobile-friendly interface
- Persistent theme preference

### Widget Management

- Draggable widget positioning
- Widget minimization
- Widget visibility toggling
- Persistent widget layout
- Customizable dashboard

## Security Considerations

1. **Authentication**
   - Required for all dashboard access
   - Role-based access control
   - Session management
   - Secure login process

2. **Data Protection**
   - Secure API endpoints
   - Encrypted data transmission
   - Access logging
   - CSRF protection

3. **Action Verification**
   - Confirmation dialogs for critical actions
   - Audit logging for all changes
   - Permission-based action availability

## Best Practices

1. **Dashboard Usage**
   - Regular monitoring of system health
   - Review of security events
   - Traffic pattern analysis
   - Resource utilization tracking
   - Network status verification
   - VPN connection monitoring

2. **Performance Optimization**
   - Efficient data polling
   - Cached responses
   - Optimized updates
   - Widget visibility management
   - Browser resource usage

## Future Enhancements

Planned improvements include:
1. Advanced traffic analysis
2. Custom dashboard widgets
3. Enhanced reporting capabilities
4. Additional security monitoring features
5. Extended API functionality
6. Network topology visualization
7. Advanced VPN management
8. Automated backup scheduling
9. System update management
10. Mobile application support

## Troubleshooting

Common issues and solutions:
1. Dashboard not updating
   - Check network connectivity
   - Verify API endpoint accessibility
   - Clear browser cache
   - Check browser console for errors

2. Performance issues
   - Reduce update frequency
   - Clear browser cache
   - Check system resources
   - Minimize unused widgets
   - Use a supported browser

3. Widget display problems
   - Reset widget layout
   - Clear browser cache
   - Check for JavaScript errors
   - Verify widget data sources

## API Documentation

Detailed API documentation is available in the [API Documentation](api.md). 