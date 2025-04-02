# Security Policy

## Supported Versions

Charon Firewall is currently in development. The following versions are receiving security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. To report a security issue, please follow these steps:

1. **Do NOT disclose the vulnerability publicly** (no GitHub issues, forum posts, social media, etc.)
2. Email our security team at security@charonfw.org with details about the vulnerability
3. Include steps to reproduce, impact, and any potential mitigations you've identified
4. Our team will acknowledge receipt of your report within 48 hours

## Security Process

1. **Receive**: We'll acknowledge your report within 48 hours
2. **Verify**: Our team will work to verify the issue
3. **Prioritize**: We'll assign a severity based on impact and complexity
4. **Fix**: A fix will be developed privately
5. **Communicate**: We'll provide you with updates on the fix process
6. **Release**: After deploying the fix, we'll publish a security advisory
7. **Credit**: With your permission, we'll credit you in our advisory

## Recent Security Updates

- **April 2024**: Updated setuptools to ≥70.0.0 to address CVE-2024-6345 (remote code execution vulnerability)
- **April 2024**: Updated cryptography to 44.0.2 to fix multiple high-severity issues

## Security Measures

Charon Firewall implements the following security measures:

- Regular dependency vulnerability scanning through GitHub Actions
- Manual code reviews focused on security
- Strong input validation and output encoding
- Container sandboxing in Docker environments
- Principle of least privilege in system operations

## Security Design

As a firewall application, security is built into the core of Charon:

- Separation of privileges between components
- Comprehensive logging and audit trails
- Regular security testing
- Containerized execution environments
- Third-party dependency monitoring

## Contact

For security concerns, contact security@charonfw.org 