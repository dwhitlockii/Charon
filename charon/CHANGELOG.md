# Changelog

All notable changes to the Charon Firewall project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern UI overhaul with dark/light theme support
- Customizable dashboard with draggable widgets
- Interactive traffic visualization using Chart.js
- Real-time system monitoring with progress bars
- Toast notifications for system events
- Collapsible sidebar for better space utilization
- Responsive design improvements for all devices
- Theme persistence using localStorage
- Quick action buttons for common tasks
- Enhanced data visualization components
- Cross-platform QoS module with support for both Linux and Windows
- Windows implementation of QoS using PowerShell Network QoS Policies
- Auto-detection of network interfaces on both platforms
- QoS status reporting for monitoring and troubleshooting
- Platform-specific permission checks for QoS operations
- Windows-specific QoS policy management API
- Comprehensive test suite for QoS module with cross-platform tests
- Windows support for content filtering module
- Windows Defender Firewall integration for domain blocking
- Platform-specific default paths for configuration and database files
- Comprehensive platform detection system
- Improved database connection handling for cross-platform support
- Platform-specific permission checks
- Windows-compatible temporary file management
- New CROSS_PLATFORM.md documentation file

### Changed
- Improved dashboard layout and organization
- Enhanced user experience with modern UI elements
- Updated documentation to reflect UI changes
- Improved error handling in QoS module with platform-specific messages
- Enhanced platform detection mechanism
- Updated documentation to include QoS cross-platform support
- Updated documentation with platform-specific details
- Enhanced error handling for cross-platform operation
- Refactored content filter to use platform-specific implementations
- Improved database connection management
- Updated content filter tests to support both platforms
- Adjusted project milestones to reflect cross-platform progress

### Fixed
- UI responsiveness issues on mobile devices
- Theme transition glitches
- Widget layout persistence
- Permission checking now works correctly on both Windows and Linux
- Subprocess calls now properly capture output for better error reporting
- Content filter compatibility issues on Windows
- Database connection handling in cross-platform environments
- Permission detection on non-Unix platforms
- Path handling for different operating systems

### Security
- Updated dependencies to address multiple critical security vulnerabilities:
  - Flask updated to 3.1.0 (from >=2.3.0) to fix information exposure in session cookie handling (CVE-2023-30861)
  - Werkzeug updated to 3.1.3 (from >=2.3.0) to fix Remote Code Execution, Directory Traversal, and Resource Allocation vulnerabilities
  - Cryptography updated to 44.0.2 (from >=41.0.0) to fix multiple high-severity issues including Type Confusion and Improper Certificate Validation
  - All dependencies pinned to specific versions to prevent future unexpected vulnerabilities
- Updated setuptools dependency to version 70.0.0 or higher to address CVE-2024-6345, a remote code execution vulnerability in the package_index module

## [0.2.0] - 2024-04-15

### Added
- Windows support for the content filtering module
- Windows Defender Firewall integration
- Platform-specific paths for configuration files
- Comprehensive platform detection system
- QoS management interface in the web UI
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Modern Python packaging with pyproject.toml
- Environment variable configuration system
- Automatic startup scripts for Linux (SystemD) and Windows (NSSM)

### Changed
- Improved database connection handling
- Enhanced error reporting
- Upgraded dependency management
- More detailed permissions checking

### Fixed
- Content filter permissions verification on Windows
- Database concurrency issues
- File path handling on different platforms
- Inconsistent rule application
- Web interface styling issues on mobile devices

## [0.1.0] - 2024-02-10

### Added
- Core firewall engine implementation
- Basic content filtering with domain blocking
- Web interface with authentication
- Support for SQLite and MySQL databases
- Initial Linux support with nftables integration
- Basic installation documentation
- Configuration file support 