# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Considerations

### Application Security
- **Local Deployment**: The application is designed to run locally for security
- **No Authentication**: No user accounts or session management (local access only)
- **Network Binding**: Binds to localhost (127.0.0.1) by default
- **External Requests**: Only makes HTTP requests to user-provided HLS stream URLs

### Data Privacy
- **No Persistent Storage**: Stream URLs and analysis data are not saved
- **Local Processing**: All analysis happens on the user's machine
- **No Telemetry**: No data is transmitted to external servers
- **Open Source**: Full transparency through public source code

### Dependencies
- **FFmpeg**: Optional external dependency for video analysis
- **psutil**: Optional dependency for system metrics
- **Python Libraries**: Standard libraries with known security profiles

## Reporting a Vulnerability

If you discover a security vulnerability in Live HLS Stream Monitor:

### Where to Report
- **GitHub Security**: Use GitHub's private vulnerability reporting
- **Public Issues**: For non-sensitive security improvements
- **Email**: Contact the maintainer directly for sensitive issues

### What to Include
1. **Description**: Clear description of the vulnerability
2. **Steps to Reproduce**: How to reproduce the issue
3. **Impact Assessment**: Potential security impact
4. **Suggested Fix**: If you have a proposed solution
5. **Environment**: OS, Python version, and dependencies

### Response Timeline
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Development**: Based on severity (1-4 weeks)
- **Public Disclosure**: After fix is available

### Security Best Practices

**For Users:**
- Run on localhost only unless necessary
- Use trusted HLS stream sources
- Keep dependencies updated
- Review source code before deployment

**For Contributors:**
- Follow secure coding practices
- Validate all inputs
- Avoid storing sensitive data
- Test security implications of changes

**For Deployment:**
- Use HTTPS for external access
- Implement proper network security
- Monitor system resources
- Regular security updates

## Responsible Disclosure

We appreciate responsible disclosure of security vulnerabilities. We commit to:

- Working with security researchers to address issues
- Providing credit for responsible disclosure
- Timely fixes for confirmed vulnerabilities
- Transparent communication about security updates

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 1.0.1)
- Documented in CHANGELOG.md
- Announced in GitHub releases
- Tagged with security labels

---

**Note**: This is an open-source project. Users deploying in production environments should conduct their own security assessments and implement additional security measures as needed.
