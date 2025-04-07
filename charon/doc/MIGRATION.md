# Migration Guide

## Overview
This guide will help you migrate to the new version of Charon Firewall with the modernized UI and enhanced features.

## Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher (for frontend dependencies)
- Modern web browser (Chrome, Firefox, Safari, or Edge)

## Step 1: Backup Your Data
1. Export your current configuration:
   ```bash
   python -m charon.src.web.server --export-config
   ```
2. Backup your database:
   ```bash
   python -m charon.src.db.database --backup
   ```

## Step 2: Update Dependencies
1. Update Python dependencies:
   ```bash
   pip install -r requirements.txt --upgrade
   ```
2. Install new frontend dependencies (via CDN, no installation needed)

## Step 3: Configuration Updates
1. Update your `.env` file with new settings:
   ```env
   # Theme settings
   DEFAULT_THEME=light
   THEME_PERSISTENCE=true
   
   # Real-time updates
   ENABLE_WEBSOCKET=true
   UPDATE_INTERVAL=5000
   
   # Widget settings
   DEFAULT_WIDGET_LAYOUT=grid
   WIDGET_PERSISTENCE=true
   ```

## Step 4: Database Migration
1. Run database migrations:
   ```bash
   python -m charon.src.db.database --migrate
   ```
2. Verify database integrity:
   ```bash
   python -m charon.src.db.database --verify
   ```

## Step 5: Testing
1. Start the server:
   ```bash
   python -m charon.src.web.server
   ```
2. Verify the following:
   - Theme switching works
   - Widgets are draggable
   - Real-time updates function
   - Notifications appear
   - All existing functionality works

## Known Issues and Workarounds

### Theme Persistence
If themes don't persist:
1. Clear browser cache
2. Check localStorage is enabled
3. Try logging out and back in

### Widget Layout
If widgets don't save position:
1. Refresh the page
2. Check browser console for errors
3. Reset widget positions

### Performance Issues
If experiencing slowdown:
1. Reduce update interval
2. Close unused widgets
3. Clear browser cache

## Rollback Procedure
If you need to rollback:

1. Stop the server
2. Restore your backup:
   ```bash
   python -m charon.src.db.database --restore
   ```
3. Revert to previous version:
   ```bash
   git checkout v0.2.0
   pip install -r requirements.txt
   ```

## Post-Migration Tasks

### User Training
1. Inform users about new features
2. Provide access to updated documentation
3. Schedule training sessions if needed

### Monitoring
1. Monitor system performance
2. Watch for any UI issues
3. Track user feedback

### Documentation
1. Update internal documentation
2. Review and update user guides
3. Document any custom configurations

## Support
If you encounter issues:
1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review the [FAQ](faq.md)
3. Contact support if needed

## Future Updates
- Regular security patches
- Performance optimizations
- New features and improvements
- Enhanced documentation 