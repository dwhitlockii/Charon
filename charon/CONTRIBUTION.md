# Contributing to Charon Firewall

Thank you for your interest in contributing to Charon! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

1. **Clone the repository:**
   ```
   git clone https://github.com/yourusername/charon.git
   cd charon
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install development dependencies
   ```

3. **Create a development database:**
   ```
   python -m charon.scripts.setup_database --skip-mysql
   ```

4. **Run tests to verify your setup:**
   ```
   python -m pytest
   ```

## Development Workflow

1. **Create a new branch for your feature or bugfix:**
   ```
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit them:**
   ```
   git add .
   git commit -m "Description of your changes"
   ```

3. **Run tests to make sure everything works:**
   ```
   python -m pytest
   ```

4. **Push your branch and create a pull request.**

## Testing Guidelines

- All new features should include appropriate tests.
- Ensure that all tests pass before submitting a pull request.
- Use pytest fixtures when appropriate to reduce test code duplication.
- Windows developers: Note that some firewall-specific tests that use Linux-specific calls may be skipped on Windows.

## Code Style Guidelines

Charon follows the following style guidelines:

- **PEP 8** for Python code style.
- **Black** for code formatting.
- **isort** for import sorting.
- **mypy** for type checking.

You can check your code with:

```
black .
isort .
flake8 .
mypy charon/
```

## Documentation

- Update documentation when adding or changing features.
- Document public APIs with docstrings (using Google style).
- Keep the README.md and documentation.md up to date.

## Making a Release

1. **Update version number in pyproject.toml.**
2. **Create a tag for the new version:**
   ```
   git tag -a v0.x.0 -m "Version 0.x.0"
   git push origin v0.x.0
   ```

## Project Structure

```
charon/                # Main package
├── src/               # Source code
│   ├── api/           # API endpoints
│   ├── core/          # Core firewall functionality
│   ├── db/            # Database models and operations
│   ├── plugins/       # Plugin system
│   ├── scheduler/     # Scheduled tasks
│   └── web/           # Web interface
├── scripts/           # Utility scripts
├── tests/             # Test suite
└── data/              # Data files (created at runtime)
```

## Current Development Status

As of April 2024, the Charon firewall is in beta status. The following components are implemented:

- [x] Core database functionality
- [x] Basic web interface
- [x] Firewall rule management
- [x] Logging system
- [x] Configuration system
- [ ] Plugin system (in progress)
- [ ] QoS module (in progress)
- [ ] Content filtering (in progress)
- [ ] API documentation (in progress)

## Getting Help

If you have questions about contributing to Charon, feel free to:

- Open an issue on GitHub
- Contact the development team at info@charonfw.org

Thank you for contributing to Charon! 