# Charon Firewall User Guide

## Getting Started

### First Login
1. Open your web browser and navigate to `http://localhost:5000`
2. Use the default credentials:
   - Username: admin
   - Password: admin
3. Change your password immediately after first login

### Dashboard Overview
The dashboard provides a comprehensive view of your firewall's status and activity:
- System status indicators
- Traffic monitoring
- Recent activity log
- Quick action buttons

## Theme Customization

### Switching Themes
1. Click the theme toggle in the top-right corner
2. Choose between Light and Dark mode
3. Your preference will be saved automatically

### Theme Features
- Automatic system preference detection
- Smooth transitions between themes
- Persistent across sessions
- Consistent styling throughout the application

## Dashboard Widgets

### Managing Widgets
1. **Moving Widgets**
   - Click and hold any widget header
   - Drag to desired position
   - Release to place

2. **Resizing Widgets**
   - Hover over widget edges
   - Click and drag to resize
   - Widgets will automatically adjust layout

3. **Customizing Widgets**
   - Click the settings icon (⚙️) in widget header
   - Adjust refresh rate
   - Toggle specific metrics
   - Change display options

### Available Widgets

#### System Status
- Displays CPU, Memory, and Disk usage
- Shows system uptime
- Color-coded indicators for resource levels

#### Traffic Monitor
- Real-time network traffic graphs
- Incoming/outgoing traffic rates
- Active connections count
- Bandwidth usage statistics

#### Firewall Status
- Active rules count
- Blocked connections
- Security status indicators
- Quick enable/disable toggle

#### Recent Activity
- Latest firewall events
- System notifications
- User actions
- Filterable by type and time

## Interactive Features

### Toast Notifications
- Appear in bottom-right corner
- Auto-dismiss after 5 seconds
- Manual dismissal available
- Color-coded by type:
  - Green: Success
  - Yellow: Warning
  - Red: Error

### Sidebar Navigation
- Collapsible for more screen space
- Active section highlighted
- Quick access to all features
- Responsive on mobile devices

## Data Visualization

### Traffic Graphs
- Real-time updates
- Time range selection
- Zoom functionality
- Export options

### Progress Bars
- System resource monitoring
- Color thresholds:
  - Green: < 60%
  - Yellow: 60-80%
  - Red: > 80%
- Animated updates

## Troubleshooting

### Common Issues

#### Theme Not Saving
1. Clear browser cache
2. Check localStorage is enabled
3. Try logging out and back in

#### Widget Layout Issues
1. Refresh the page
2. Check browser console for errors
3. Reset widget positions if needed

#### Performance Problems
1. Reduce widget refresh rates
2. Close unused widgets
3. Check network connection

### Getting Help
- Check the [Technical Documentation](ui_components.md)
- Review [FAQ](faq.md)
- Contact support if issues persist

## Security Best Practices

1. **Regular Password Updates**
   - Change password every 90 days
   - Use strong, unique passwords
   - Enable two-factor authentication if available

2. **Access Control**
   - Create separate user accounts
   - Assign appropriate permissions
   - Monitor user activity

3. **System Monitoring**
   - Regularly check system status
   - Review firewall logs
   - Monitor traffic patterns

## Mobile Access

### Responsive Design
- Optimized for all screen sizes
- Touch-friendly interface
- Collapsible sidebar
- Adaptive widget layouts

### Mobile Features
- Swipe gestures supported
- Touch-optimized controls
- Mobile-specific layouts
- Offline capabilities

## Exporting Data

### Available Exports
1. Traffic logs
2. System metrics
3. Firewall rules
4. User activity

### Export Formats
- CSV
- JSON
- PDF (for reports)
- Custom formats via API 