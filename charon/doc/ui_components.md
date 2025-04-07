# UI Components Technical Documentation

## Theme System

### Overview
The theme system provides a consistent look and feel across the application with support for light and dark modes.

### Implementation
- Uses CSS variables for theme colors and properties
- Theme state is persisted in localStorage
- Smooth transitions between themes
- Responsive design considerations

### CSS Variables
```css
:root {
    --primary-color: #4a6ee0;
    --secondary-color: #f5f5f5;
    --text-color: #333;
    --light-text: #666;
    --border-color: #ddd;
    --success-color: #2ecc71;
    --warning-color: #f1c40f;
    --danger-color: #e74c3c;
}
```

### Theme Toggle
- Implemented as a switch component
- Updates localStorage on change
- Triggers CSS variable updates
- Handles system preference detection

## Dashboard Widgets

### Architecture
- Grid-based layout system
- Draggable components using SortableJS
- Widget state persistence
- Real-time data updates

### Widget Types
1. **System Status**
   - CPU usage
   - Memory usage
   - Disk usage
   - Uptime

2. **Traffic Monitor**
   - Real-time traffic graphs
   - Connection statistics
   - Bandwidth usage

3. **Firewall Status**
   - Active rules count
   - Blocked connections
   - Security status

4. **Recent Activity**
   - Latest firewall events
   - System notifications
   - User actions

### Widget Configuration
- Position persistence
- Size customization
- Data refresh intervals
- Visibility toggles

## Data Visualization

### Chart.js Integration
- Real-time traffic monitoring
- Historical data analysis
- Custom chart configurations
- Responsive design

### Progress Bars
- System resource monitoring
- Custom styling
- Animated updates
- Threshold indicators

## Interactive Elements

### Toast Notifications
- System event alerts
- Success/warning/error states
- Auto-dismissal
- Manual dismissal option

### Sidebar
- Collapsible design
- Active state indicators
- Responsive behavior
- Navigation structure

## API Integration

### Real-time Updates
- WebSocket connections
- Polling fallback
- Data refresh mechanisms
- Error handling

### Endpoints
```javascript
// Theme management
GET /api/theme
POST /api/theme

// Widget configuration
GET /api/widgets
POST /api/widgets
PUT /api/widgets/{id}
DELETE /api/widgets/{id}

// System monitoring
GET /api/system/status
GET /api/system/resources
GET /api/system/traffic
```

## Performance Considerations

### Optimization
- Lazy loading of components
- Debounced updates
- Cached data
- Efficient DOM updates

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile device compatibility
- Progressive enhancement
- Fallback mechanisms

## Security

### Best Practices
- Input sanitization
- XSS prevention
- CSRF protection
- Secure data transmission

### Authentication
- Session management
- Role-based access
- Secure storage
- Token validation

## Testing

### Unit Tests
- Component testing
- Theme switching
- Widget functionality
- Data visualization

### Integration Tests
- API endpoints
- Real-time updates
- User interactions
- Cross-browser compatibility

## Troubleshooting

### Common Issues
1. Theme persistence problems
   - Check localStorage availability
   - Verify CSS variable updates
   - Clear browser cache

2. Widget layout issues
   - Verify SortableJS initialization
   - Check grid system configuration
   - Validate widget state

3. Performance problems
   - Monitor WebSocket connections
   - Check data update frequency
   - Verify caching mechanisms

### Debug Tools
- Browser developer tools
- Network monitoring
- Performance profiling
- Error logging 