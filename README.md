# Live HLS Stream Monitor 📺

A powerful web-based tool for real-time monitoring and analysis of HLS (HTTP Live Streaming) streams. Built with Flask and featuring an advanced dashboard with system metrics integration.

![Live HLS Monitor Dashboard](https://img.shields.io/badge/Status-Live-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### Real-Time HLS Monitoring
- **Live Stream Analysis**: Monitor HLS streams in real-time with automatic updates
- **Master Playlist Support**: Automatically handles variant selection from master playlists
- **Segment Health Monitoring**: Track segment availability and response times
- **Stream Quality Metrics**: Monitor bitrate, resolution, frame rate, and duration

### Advanced Video & Audio Analysis
- **Dual Stream Support**: Separate video and audio stream analysis
- **Codec Detection**: Identify video and audio codecs in use
- **Bitrate Intelligence**: Smart bitrate estimation from master playlists
- **Resolution Tracking**: Monitor stream resolution changes over time

### Professional Dashboard
- **Cockpit.js Integration**: Advanced system metrics with professional gauges
- **Real-Time Charts**: Live updating charts for bitrate, success rate, and performance
- **System Monitoring**: CPU, memory, disk, and network usage tracking
- **Health Indicators**: Stream health status with visual indicators

### Technical Capabilities
- **FFprobe Integration**: Detailed media analysis using FFmpeg tools
- **SSL/HTTPS Support**: Handle secure streaming protocols
- **Error Resilience**: Graceful fallback for missing dependencies
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Privacy-First**: All processing is local, no data transmission to external servers

## 🔒 Privacy & Security

### Data Privacy
- **Local Processing Only**: All stream analysis happens on your machine
- **No Data Collection**: Stream URLs and analysis results are not stored
- **No External Transmission**: Data is never sent to third-party servers
- **Open Source Transparency**: Full source code available for review

### Security Features
- **Local Network Binding**: Runs on localhost by default (127.0.0.1:8181)
- **SSL/HTTPS Support**: Secure handling of HTTPS streaming protocols
- **Input Validation**: URL validation to prevent malicious requests
- **Optional Dependencies**: System metrics and advanced features are opt-in

**📄 Full Privacy Policy**: See [PRIVACY.md](PRIVACY.md) for complete privacy details.

## 🛠 Installation

### Prerequisites
- Python 3.7 or higher
- FFmpeg (for advanced video analysis)

### Quick Start
1. **Clone the repository**:
   ```bash
   git clone https://github.com/msahmarani/live-hls-stream-monitor.git
   cd live-hls-stream-monitor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Install system metrics support**:
   ```bash
   pip install psutil  # For real system metrics
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser**:
   Navigate to [http://localhost:8181](http://localhost:8181)

## 🎯 Usage

### Basic Stream Monitoring
1. Enter your HLS stream URL (`.m3u8` playlist)
2. Click "Start Live Monitor" 
3. View real-time metrics and stream health

### Advanced Features
- **Master Playlists**: Automatically detects and analyzes variant streams
- **Audio Metrics**: View audio codec, sample rate, and channel information  
- **System Metrics**: Monitor server performance alongside stream metrics
- **Health Monitoring**: Track segment success rates and response times

### Supported Stream Types
- Master playlists with multiple variants
- Direct media playlists
- Live streaming URLs
- VOD (Video on Demand) playlists
- Both HTTP and HTTPS streams

## 📊 Dashboard Features

### Stream Metrics Panel
- Real-time bitrate monitoring (video + audio)
- Segment success rate tracking
- Duration and timing analysis
- Resolution and codec information

### System Performance Panel (Cockpit.js)
- CPU usage gauges
- Memory utilization charts  
- Network bandwidth monitoring
- Disk usage indicators

### Visual Analytics
- Live updating charts using Chart.js
- Performance trend analysis
- Health status indicators
- Responsive design for all devices

## 🏗 Technical Architecture

### Core Components
- **Flask Backend**: RESTful API for stream analysis and metrics
- **m3u8 Parser**: HLS playlist parsing and variant detection  
- **FFprobe Integration**: Media analysis and codec detection
- **Chart.js Frontend**: Real-time data visualization
- **Cockpit.js Metrics**: Advanced system monitoring dashboard

### API Endpoints
- `GET /api/live-metrics/<playlist_url>` - Real-time stream metrics
- `GET /api/system-metrics` - System performance data
- `GET /api/health-check` - Application health status
- `GET /api/test-url/<playlist_url>` - URL connectivity testing

### Dependencies
- **Flask 2.3.3**: Web framework
- **m3u8 4.0.0**: HLS playlist parsing
- **requests 2.31.0**: HTTP client library
- **psutil** (optional): System metrics collection
- **FFmpeg/FFprobe**: Media analysis tools

## 🔧 Configuration

### Environment Setup
The application runs on `127.0.0.1:8181` by default. You can modify the host and port in `app.py`:

```python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8181, debug=True)
```

### FFmpeg Installation
For advanced video analysis, install FFmpeg:

**Windows**:
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux**:
```bash
sudo apt update && sudo apt install ffmpeg
```

### System Metrics (Optional)
Install psutil for real system monitoring:
```bash
pip install psutil
```

Without psutil, the application will use simulated metrics data.

## 🚦 Troubleshooting

### Common Issues

**FFprobe not found**:
- Ensure FFmpeg is installed and in your PATH
- The application will work without FFprobe but with limited analysis

**SSL Certificate errors**:
- The application handles SSL verification automatically
- HTTPS streams are supported with certificate validation disabled

**Memory usage**:
- Large playlists may consume more memory
- Consider segment limits for very long streams

**Port conflicts**:
- Change the port in `app.py` if 8181 is in use
- Ensure no firewall blocking on the chosen port

### Security Considerations

**Network Access**:
- Application binds to localhost (127.0.0.1) by default for security
- Only change host binding if you understand the security implications
- Consider using a reverse proxy (nginx) for external access

**Stream URL Validation**:
- Only analyze trusted HLS streams
- Be cautious with streams from unknown sources
- The application validates URLs but cannot guarantee stream content safety

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the application logs for detailed error information

## 🙏 Acknowledgments

- **Flask** - Micro web framework for Python
- **m3u8** - Python library for parsing M3U8 files
- **Chart.js** - Beautiful charts for web applications
- **Cockpit.js** - Advanced metrics and monitoring widgets
- **FFmpeg** - Complete, cross-platform solution for media processing

---

**Made with ❤️ for the streaming community**
- **Resolution Width Chart**: Line graph showing width in pixels across segments
- **Frame Rate Chart**: Line graph showing frame rate (fps) across segments
- Interactive tables with segment details

## Installation Requirements

### FFmpeg/ffprobe
This application requires `ffprobe` (part of FFmpeg) to analyze video segments:

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract and add the `bin` folder to your system PATH
3. Verify installation: `ffprobe -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Python Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

## Development

### Project Structure
```
hls/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── index.html        # Main form
│   ├── variants.html     # Variant selection
│   └── result.html       # Analysis results
└── .github/
    └── copilot-instructions.md
```

### Running in Development Mode
The application runs in debug mode by default when executed directly:
```bash
python app.py
```
Server will start at `http://localhost:8181`

---
See `.github/copilot-instructions.md` for workspace-specific Copilot instructions.
