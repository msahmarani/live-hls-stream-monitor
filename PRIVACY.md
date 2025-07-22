# Privacy Policy

**Last Updated: July 22, 2025**

## Overview

Live HLS Stream Monitor ("the Application") is designed to analyze and monitor HLS (HTTP Live Streaming) streams in real-time. This privacy policy explains how the application handles data when you use it.

## Data Collection and Usage

### What Data We Process

**Stream URLs and Metadata:**
- HLS playlist URLs you provide for analysis
- Stream metadata (codec information, resolution, bitrate, etc.)
- Segment availability and response times
- Audio and video stream characteristics

**System Performance Data:**
- CPU usage, memory usage, disk space (when psutil is installed)
- Network bandwidth metrics
- Application performance metrics

**Technical Data:**
- HTTP request/response data for stream analysis
- Temporary analysis results
- Application logs and error messages

### How We Use This Data

**Local Processing Only:**
- All analysis is performed locally on your machine
- No data is transmitted to external servers (except for the HLS streams you choose to analyze)
- Stream URLs and analysis results are not stored persistently
- System metrics are only displayed in real-time and not saved

**Network Requests:**
- The application makes HTTP requests only to the HLS stream URLs you provide
- These requests are necessary to download and analyze playlist and segment files
- SSL certificate verification is disabled for HTTPS streams to handle self-signed certificates

## Data Storage and Retention

**No Persistent Storage:**
- Stream URLs are not saved between sessions
- Analysis results are temporary and cleared when you close the application
- No user data is written to files or databases

**In-Memory Processing:**
- All data processing occurs in application memory
- Data is automatically cleared when the application is closed
- No caching of sensitive stream information

## Data Sharing

**No Third-Party Sharing:**
- Your stream URLs and analysis data are never shared with third parties
- No analytics or tracking services are integrated
- No data is transmitted to external servers for processing

**Local Network Only:**
- The application runs on localhost (127.0.0.1:8181) by default
- Access is limited to your local machine unless you explicitly configure otherwise

## Security Measures

**Network Security:**
- HTTPS streams are supported with appropriate SSL handling
- Network requests include timeouts to prevent hanging connections
- Input validation on stream URLs to prevent malicious requests

**Application Security:**
- No user authentication or session management (runs locally)
- CORS is enabled only for local development
- Debug mode should be disabled in production deployments

## Your Rights and Choices

**Control Over Data:**
- You choose which stream URLs to analyze
- You can stop monitoring at any time
- No data persists after closing the application

**Optional Features:**
- System metrics collection (psutil) is optional
- FFmpeg integration is optional for advanced analysis
- All features can be disabled by not installing optional dependencies

## Open Source Transparency

**Code Transparency:**
- Full source code is available on GitHub
- You can review exactly how data is processed
- No hidden data collection or transmission

**Self-Hosted:**
- You run the application on your own infrastructure
- You have complete control over the deployment environment
- No dependency on external services

## Contact Information

This is an open-source project hosted on GitHub. For privacy-related questions or concerns:

- **GitHub Issues**: https://github.com/msahmarani/live-hls-stream-monitor/issues
- **Repository**: https://github.com/msahmarani/live-hls-stream-monitor

## Changes to This Policy

This privacy policy may be updated to reflect changes in the application or legal requirements. Updates will be published in the GitHub repository with appropriate version tracking.

## Compliance Notes

**GDPR Compliance:**
- No personal data is collected or processed
- Stream URLs are considered technical data, not personal data
- Processing is based on legitimate interest (technical analysis)

**Data Minimization:**
- Only necessary data for stream analysis is processed
- No excessive or unnecessary data collection
- Temporary processing with no persistent storage

---

**Note**: This privacy policy applies to the open-source Live HLS Stream Monitor application. If you deploy this application in a commercial or organizational environment, you may need to create additional privacy documentation based on your specific use case and local regulations.
